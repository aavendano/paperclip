"""Process-spawn authorization gate for work_orders/services.py (AAD-57 rework).

Apply to agents-os on branch cursor/aad-57-slice-b0-c417 AFTER merging PR #263 head.

Integration: import and call assert_process_spawn_authorized() immediately BEFORE
subprocess.Popen in work_orders/services.py (approx lines 478-486 per review).
"""

from __future__ import annotations

import logging
from typing import Any, Sequence

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
from core.agent_decisions.services import (
    normalize_material_action,
    record_consume_deny,
)

logger = logging.getLogger(__name__)

PROCESS_SPAWN_ACTION = 'process.agent'


def material_action_for_process_spawn(*, spawn_kind: str = 'agent') -> str:
    return normalize_material_action(f'process.{(spawn_kind or "agent").strip().lower()}')


def _spawn_exec_arguments(
    *,
    command: Sequence[str],
    spawn_context: dict[str, Any] | None,
) -> dict[str, Any]:
    args: dict[str, Any] = {'command': list(command)}
    ctx = spawn_context or {}
    for key in ('cwd', 'env', 'timeout_seconds'):
        if key in ctx:
            args[key] = ctx[key]
    return args


def assert_process_spawn_authorized(
    *,
    work_order,
    run,
    command: Sequence[str],
    spawn_context: dict[str, Any] | None = None,
    agent_profile_id: int | None = None,
    spawn_kind: str = 'agent',
) -> None:
    """Fail-closed gate before subprocess.Popen in work_orders/services.py."""
    if not enforcement_enabled():
        return

    action = material_action_for_process_spawn(spawn_kind=spawn_kind)
    inputs = spawn_context or {}
    decision_id, nonce = extract_action_credentials(
        inputs=inputs,
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
            message='Process spawn requires a consumed ALLOW decision.',
        )

    exec_profile_id = _executing_profile_id(
        agent_profile_id=agent_profile_id,
        work_order=work_order,
    )
    if exec_profile_id and _profile_paused(exec_profile_id):
        agent_for_audit = _resolve_executing_agent(
            agent_profile_id=agent_profile_id,
            work_order=work_order,
        )
        record_consume_deny(
            agent=agent_for_audit,
            reason_code=REASON_CONSUME_PROFILE_INACTIVE,
            decision_id=decision_id,
            scope=scope,
        )
        raise AgentActionAuthzError(
            reason_code=REASON_CONSUME_PROFILE_INACTIVE,
            message='Process spawn denied: agent profile is paused.',
        )

    agent = _resolve_executing_agent(
        agent_profile_id=agent_profile_id,
        work_order=work_order,
    )
    if agent is None:
        raise AgentActionAuthzError(
            reason_code=REASON_CONSUME_UNAVAILABLE,
            message='Unable to resolve agent principal for process spawn.',
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
            message='Process spawn requires the decision nonce.',
        )

    exec_arguments = _spawn_exec_arguments(command=command, spawn_context=inputs)
    _consume_or_raise(
        agent=agent,
        decision_id=decision_id,
        nonce=nonce,
        scope=scope,
        action=action,
        exec_arguments=strip_auth_material(exec_arguments),
        error_prefix='Process spawn',
    )
