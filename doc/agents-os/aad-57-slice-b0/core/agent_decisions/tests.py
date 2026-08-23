"""Tests for agent-authenticated execution decisions (Slice B-0 / AAD-57)."""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import patch

from django.test import Client, TestCase, override_settings
from django.utils import timezone

from core.agent_decisions.binding import compute_argument_binding
from core.agent_decisions.models import AgentExecutionDecision
from core.agent_decisions.reason_codes import ReasonCode
from core.agent_decisions.services import (
    AuthorizationServiceUnavailable,
    DecisionRequest,
    authorize_execution,
    verify_and_consume_decision,
)
from integrations.models import AgentToolGrant
from processes.material_execution import ProcessExecutionDenied, execute_process_material_action
from users.models import AgentUser, HumanUser
from users.tokens import AuthToken


class AgentDecisionServiceTests(TestCase):
    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        cls.human = HumanUser.objects.create_user(
            username='aad57-human',
            password='pass',
        )
        cls.agent = AgentUser.objects.create_user(
            username='aad57-agent',
            email='aad57-agent@example.com',
        )
        cls.auth_token, cls.raw_token = AuthToken.create_for(cls.agent, label='aad57')

    def _request(self, **overrides) -> DecisionRequest:
        data = {
            'request_id': uuid.uuid4(),
            'decision_nonce': uuid.uuid4().hex,
            'adapter_type': 'process',
            'capability_key': 'process',
            'material_action': 'echo',
            'arguments': {'argv': ['echo', 'ok']},
            'work_context': {'run_id': 'run-1'},
        }
        data.update(overrides)
        return DecisionRequest(**data)

    def test_allow_when_grant_and_binding_present(self):
        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name='process:echo',
            granted_by=self.human,
        )
        response = authorize_execution(
            agent=self.agent,
            request=self._request(),
            auth_token=self.auth_token,
        )
        self.assertEqual(response.outcome, AgentExecutionDecision.OUTCOME_ALLOW)
        self.assertEqual(response.reason_code, str(ReasonCode.ALLOW))
        self.assertTrue(
            AgentExecutionDecision.objects.filter(decision_id=response.decision_id).exists()
        )

    def test_deny_without_authority(self):
        response = authorize_execution(agent=self.agent, request=self._request())
        self.assertEqual(response.outcome, AgentExecutionDecision.OUTCOME_DENY)
        self.assertEqual(response.reason_code, str(ReasonCode.NO_AUTHORITY))

    def test_reject_replayed_nonce(self):
        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name='process:echo',
            granted_by=self.human,
        )
        req = self._request(decision_nonce='fixed-nonce')
        authorize_execution(agent=self.agent, request=req)
        replay = authorize_execution(agent=self.agent, request=req)
        self.assertEqual(replay.reason_code, str(ReasonCode.REPLAY_DETECTED))

    def test_reject_argument_mismatch_at_consume(self):
        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name='process:echo',
            granted_by=self.human,
        )
        req = self._request()
        allowed = authorize_execution(agent=self.agent, request=req)
        with self.assertRaises(Exception):
            verify_and_consume_decision(
                agent=self.agent,
                decision_id=allowed.decision_id,
                decision_nonce=allowed.decision_nonce,
                argument_binding='sha256:deadbeef',
            )

    def test_reject_expired_decision(self):
        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name='process:echo',
            granted_by=self.human,
        )
        req = self._request()
        allowed = authorize_execution(agent=self.agent, request=req)
        decision = AgentExecutionDecision.objects.get(decision_id=allowed.decision_id)
        decision.expires_at = timezone.now() - timedelta(seconds=1)
        decision.save(update_fields=['expires_at'])
        with self.assertRaises(Exception):
            verify_and_consume_decision(
                agent=self.agent,
                decision_id=allowed.decision_id,
                decision_nonce=allowed.decision_nonce,
                argument_binding=allowed.argument_binding,
            )

    @override_settings(AGENT_DECISION_FORCE_OUTAGE=True)
    def test_qms_unavailable_fail_closed(self):
        with self.assertRaises(AuthorizationServiceUnavailable):
            authorize_execution(agent=self.agent, request=self._request())


class AgentDecisionApiTests(TestCase):
    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        cls.human = HumanUser.objects.create_user(
            username='aad57-api-human',
            password='pass',
        )
        cls.agent = AgentUser.objects.create_user(
            username='aad57-api-agent',
            email='aad57-api-agent@example.com',
        )
        cls.auth_token, cls.raw_token = AuthToken.create_for(cls.agent, label='aad57-api')

    def test_endpoint_allow_and_deny(self):
        client = Client()
        base = {
            'contract_version': 'qms-agent-decision/0.1',
            'request_id': str(uuid.uuid4()),
            'decision_nonce': uuid.uuid4().hex,
            'adapter_type': 'process',
            'capability_key': 'process',
            'material_action': 'echo',
            'arguments': {'argv': ['echo', 'hi']},
            'work_context': {'run_id': 'run-2'},
        }
        deny = client.post(
            '/api/agent/v1/decisions/authorize',
            data=base,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.raw_token}',
        )
        self.assertEqual(deny.status_code, 200)
        self.assertEqual(deny.json()['outcome'], 'DENY')

        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name='process:echo',
            granted_by=self.human,
        )
        base['request_id'] = str(uuid.uuid4())
        base['decision_nonce'] = uuid.uuid4().hex
        allow = client.post(
            '/api/agent/v1/decisions/authorize',
            data=base,
            content_type='application/json',
            HTTP_AUTHORIZATION=f'Bearer {self.raw_token}',
        )
        self.assertEqual(allow.status_code, 200)
        self.assertEqual(allow.json()['outcome'], 'ALLOW')


class ProcessMaterialExecutionTests(TestCase):
    databases = '__all__'

    @classmethod
    def setUpTestData(cls):
        cls.human = HumanUser.objects.create_user(
            username='aad57-process-human',
            password='pass',
        )
        cls.agent = AgentUser.objects.create_user(
            username='aad57-process-agent',
            email='aad57-process-agent@example.com',
        )

    def _allow_decision(self):
        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name='process:echo',
            granted_by=self.human,
        )
        req = DecisionRequest(
            request_id=uuid.uuid4(),
            decision_nonce=uuid.uuid4().hex,
            adapter_type='process',
            capability_key='process',
            material_action='echo',
            arguments={'argv': ['echo', 'slice-b0']},
            work_context={'run_id': 'run-process-1'},
        )
        return authorize_execution(agent=self.agent, request=req)

    def test_process_path_requires_valid_decision(self):
        allowed = self._allow_decision()
        result = execute_process_material_action(
            agent=self.agent,
            decision_id=allowed.decision_id,
            decision_nonce=allowed.decision_nonce,
            argument_binding=allowed.argument_binding,
            command=['echo', 'slice-b0'],
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('slice-b0', result.stdout)

    def test_process_path_denied_without_decision(self):
        with self.assertRaises(ProcessExecutionDenied):
            execute_process_material_action(
                agent=self.agent,
                decision_id=uuid.uuid4(),
                decision_nonce='missing',
                argument_binding='sha256:missing',
                command=['echo', 'nope'],
            )

    @override_settings(AGENT_DECISION_FORCE_OUTAGE=True)
    def test_process_path_fail_closed_on_qms_outage(self):
        allowed = DecisionRequest(
            request_id=uuid.uuid4(),
            decision_nonce=uuid.uuid4().hex,
            adapter_type='process',
            capability_key='process',
            material_action='echo',
            arguments={'argv': ['echo', 'x']},
            work_context={},
        )
        with patch(
            'processes.material_execution.verify_and_consume_decision',
            side_effect=AuthorizationServiceUnavailable('down'),
        ):
            with self.assertRaises(ProcessExecutionDenied):
                execute_process_material_action(
                    agent=self.agent,
                    decision_id=uuid.uuid4(),
                    decision_nonce=allowed.decision_nonce,
                    argument_binding='sha256:x',
                    command=['echo', 'x'],
                )
