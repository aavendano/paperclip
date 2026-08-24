"""Tests for process spawn authorization gate (AAD-57 rework).

Copy to work_orders/tests/test_spawn_authorization.py in agents-os.
Adjust imports/helpers to match local test fixtures.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from django.test import TestCase

from core.agent_decisions.exceptions import AgentActionAuthzError
from core.agent_decisions.services import (
    normalize_material_action,
    request_agent_action_authorization,
)
from integrations.models import AgentMaterialAuthorityGrant, AgentToolGrant


class ProcessSpawnAuthorizationTests(TestCase):
    databases = '__all__'

    def setUp(self):
        # Replace with agents-os fixture helpers (see core.agent_decisions.tests.helpers)
        from core.agent_decisions.tests.helpers import make_agent_with_profile, make_work_order_run

        self.agent, self.profile, self.raw_token = make_agent_with_profile()
        self.work_order, self.run = make_work_order_run(agent_profile=self.profile)
        self.command = ['echo', 'spawn-test']

    def _mint_allow(self, *, nonce: str | None = None):
        nonce = nonce or uuid.uuid4().hex
        action = normalize_material_action('process.agent')
        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name=action,
            granted_by_id=self.agent.pk,
        )
        AgentMaterialAuthorityGrant.objects.create(
            agent=self.agent,
            normalized_action=action,
            granted_by_id=self.agent.pk,
        )
        return request_agent_action_authorization(
            agent=self.agent,
            request_id=str(uuid.uuid4()),
            scope={
                'work_order_id': self.work_order.pk,
                'run_id': self.run.pk,
                'process_id': self.work_order.process_id,
                'agent_profile_id': self.profile.pk,
            },
            action=action,
            arguments={'command': self.command, 'cwd': '/tmp'},
            nonce=nonce,
        )

    @patch('work_orders.services.subprocess.Popen')
    def test_spawn_blocked_without_decision(self, mock_popen):
        from core.agent_decisions.enforcement import assert_process_spawn_authorized

        with self.assertRaises(AgentActionAuthzError):
            assert_process_spawn_authorized(
                work_order=self.work_order,
                run=self.run,
                command=self.command,
                spawn_context={},
                agent_profile_id=self.profile.pk,
            )
        mock_popen.assert_not_called()

    @patch('work_orders.services.subprocess.Popen')
    def test_spawn_allowed_with_valid_credential(self, mock_popen):
        from core.agent_decisions.enforcement import assert_process_spawn_authorized

        minted = self._mint_allow()
        mock_popen.return_value = MagicMock(returncode=0)

        assert_process_spawn_authorized(
            work_order=self.work_order,
            run=self.run,
            command=self.command,
            spawn_context={
                '__agent_action_credentials': {
                    'process.agent': {
                        'decision_id': minted.decision_id,
                        'nonce': minted.nonce,
                    },
                },
                'command': self.command,
                'cwd': '/tmp',
            },
            agent_profile_id=self.profile.pk,
        )
        # Popen wiring verified in integration test once services.py is patched

    def test_spawn_replay_denied(self):
        from core.agent_decisions.enforcement import assert_process_spawn_authorized

        minted = self._mint_allow()
        creds = {
            '__agent_action_credentials': {
                'process.agent': {
                    'decision_id': minted.decision_id,
                    'nonce': minted.nonce,
                },
            },
            'command': self.command,
            'cwd': '/tmp',
        }
        assert_process_spawn_authorized(
            work_order=self.work_order,
            run=self.run,
            command=self.command,
            spawn_context=creds,
            agent_profile_id=self.profile.pk,
        )
        with self.assertRaises(AgentActionAuthzError):
            assert_process_spawn_authorized(
                work_order=self.work_order,
                run=self.run,
                command=self.command,
                spawn_context=creds,
                agent_profile_id=self.profile.pk,
            )
