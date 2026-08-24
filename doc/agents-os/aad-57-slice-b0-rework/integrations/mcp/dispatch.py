"""Managed MCP tool dispatch with per-action authority consumption (AAD-57 rework).

Create as integrations/mcp/dispatch.py in agents-os.
Route ALL managed MCP tool invocations through execute_mcp_tool_authorized().
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from core.agent_decisions.constants import (
    REASON_CONSUME_MISSING,
    REASON_CONSUME_NONCE_MISSING,
    REASON_CONSUME_PROFILE_INACTIVE,
    REASON_CONSUME_UNAVAILABLE,
    enforcement_enabled,
)
from core.agent_decisions.credentials import extract_action_credentials, strip_auth_material
from core.agent_decisions.enforcement import (
    _build_scope,
    _consume_or_raise,
    _enforce_identity_active,
    _executing_profile_id,
    _profile_paused,
    _resolve_executing_agent,
)
from core.agent_decisions.exceptions import AgentActionAuthzError
from core.agent_decisions.services import normalize_material_action, record_consume_deny
from users.models import User

logger = logging.getLogger(__name__)

__all__ = ['execute_mcp_tool_authorized', 'material_action_for_mcp_tool']


def material_action_for_mcp_tool(tool_name: str) -> str:
    normalized = (tool_name or '').strip().lower()
    return normalize_material_action(f'mcp.{normalized}')


def assert_mcp_tool_authorized(
    *,
    agent: User,
    tool_name: str,
    arguments: dict[str, Any],
    work_order,
    run,
    inputs: dict[str, Any] | None = None,
    agent_profile_id: int | None = None,
) -> None:
    """Fail-closed gate before MCP tool material effects."""
    if not enforcement_enabled():
        return

    action = material_action_for_mcp_tool(tool_name)
    merged_inputs = dict(inputs or {})
    merged_inputs.update(arguments or {})
    decision_id, nonce = extract_action_credentials(
        inputs=merged_inputs,
        work_order=work_order,
        normalized_action=action,
    )
    scope = _build_scope(
        context=None,
        work_order=work_order,
        run_id=getattr(run, 'pk', None),
        agent_profile_id=agent_profile_id,
    )

    if not decision_id:
        raise AgentActionAuthzError(
            reason_code=REASON_CONSUME_MISSING,
            message=f'MCP tool {tool_name!r} requires a consumed ALLOW decision.',
        )

    exec_profile_id = _executing_profile_id(
        agent_profile_id=agent_profile_id,
        work_order=work_order,
    )
    if exec_profile_id and _profile_paused(exec_profile_id):
        record_consume_deny(
            agent=agent,
            reason_code=REASON_CONSUME_PROFILE_INACTIVE,
            decision_id=decision_id,
            scope=scope,
        )
        raise AgentActionAuthzError(
            reason_code=REASON_CONSUME_PROFILE_INACTIVE,
            message=f'MCP tool {tool_name!r} denied: agent profile is paused.',
        )

    if agent is None:
        raise AgentActionAuthzError(
            reason_code=REASON_CONSUME_UNAVAILABLE,
            message='Unable to resolve MCP tool agent principal.',
        )

    _enforce_identity_active(agent=agent, decision_id=decision_id, scope=scope)

    if not nonce:
        record_consume_deny(
            agent=agent,
            reason_code=REASON_CONSUME_NONCE_MISSING,
            decision_id=decision_id,
            scope=scope,
        )
        raise AgentActionAuthzError(
            reason_code=REASON_CONSUME_NONCE_MISSING,
            message=f'MCP tool {tool_name!r} requires the decision nonce.',
        )

    _consume_or_raise(
        agent=agent,
        decision_id=decision_id,
        nonce=nonce,
        scope=scope,
        action=action,
        exec_arguments=strip_auth_material(merged_inputs),
        error_prefix=f'MCP tool {tool_name!r}',
    )


def execute_mcp_tool_authorized(
    *,
    agent: User,
    tool_name: str,
    arguments: dict[str, Any],
    work_order,
    run,
    inputs: dict[str, Any] | None = None,
    agent_profile_id: int | None = None,
    invoke: Callable[[], Any],
) -> Any:
    """Invoke one MCP tool after authority consumption."""
    assert_mcp_tool_authorized(
        agent=agent,
        tool_name=tool_name,
        arguments=arguments,
        work_order=work_order,
        run=run,
        inputs=inputs,
        agent_profile_id=agent_profile_id,
    )
    return invoke()
