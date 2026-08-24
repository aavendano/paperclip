"""Tests for MCP dispatch authority consumption (AAD-57 rework).

Copy to integrations/mcp/tests/test_dispatch_authorization.py in agents-os.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from django.test import TestCase

from core.agent_decisions.exceptions import AgentActionAuthzError
from core.agent_decisions.services import (
    normalize_material_action,
    request_agent_action_authorization,
)
from integrations.models import AgentMaterialAuthorityGrant, AgentToolGrant
from integrations.mcp.dispatch import execute_mcp_tool_authorized


class McpDispatchAuthorizationTests(TestCase):
    databases = '__all__'

    def setUp(self):
        from core.agent_decisions.tests.helpers import make_agent_with_profile, make_work_order_run

        self.agent, self.profile, _ = make_agent_with_profile()
        self.work_order, self.run = make_work_order_run(agent_profile=self.profile)
        self.tool_name = 'filesystem.read'
        self.action = normalize_material_action(f'mcp.{self.tool_name}')
        self.arguments = {'path': '/tmp/test.txt'}

    def _mint_allow(self):
        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name=self.action,
            granted_by_id=self.agent.pk,
        )
        AgentMaterialAuthorityGrant.objects.create(
            agent=self.agent,
            normalized_action=self.action,
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
            action=self.action,
            arguments=self.arguments,
            nonce=uuid.uuid4().hex,
        )

    def test_mcp_blocked_without_decision(self):
        invoked = MagicMock()
        with self.assertRaises(AgentActionAuthzError):
            execute_mcp_tool_authorized(
                agent=self.agent,
                tool_name=self.tool_name,
                arguments=self.arguments,
                work_order=self.work_order,
                run=self.run,
                inputs={},
                agent_profile_id=self.profile.pk,
                invoke=invoked,
            )
        invoked.assert_not_called()

    def test_mcp_allowed_with_credential(self):
        minted = self._mint_allow()
        invoked = MagicMock(return_value={'ok': True})
        result = execute_mcp_tool_authorized(
            agent=self.agent,
            tool_name=self.tool_name,
            arguments=self.arguments,
            work_order=self.work_order,
            run=self.run,
            inputs={
                '__agent_action_credentials': {
                    self.action: {
                        'decision_id': minted.decision_id,
                        'nonce': minted.nonce,
                    },
                },
            },
            agent_profile_id=self.profile.pk,
            invoke=invoked,
        )
        self.assertEqual(result, {'ok': True})
        invoked.assert_called_once()

    def test_mcp_capability_alone_insufficient(self):
        """Capability grant without authority ticket must fail at mint — never reach execute."""
        AgentToolGrant.objects.create(
            agent=self.agent,
            tool_name=self.action,
            granted_by_id=self.agent.pk,
        )
        from core.agent_decisions.constants import REASON_DENY_AUTHORITY_MISSING

        result = request_agent_action_authorization(
            agent=self.agent,
            request_id=str(uuid.uuid4()),
            scope={
                'work_order_id': self.work_order.pk,
                'run_id': self.run.pk,
                'process_id': self.work_order.process_id,
                'agent_profile_id': self.profile.pk,
            },
            action=self.action,
            arguments=self.arguments,
            nonce=uuid.uuid4().hex,
        )
        self.assertNotEqual(result.decision, 'ALLOW')
        self.assertEqual(result.reason_code, REASON_DENY_AUTHORITY_MISSING)
