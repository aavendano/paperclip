"""Authorization decision services for Slice B-0."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from core.agent_decisions.binding import compute_argument_binding
from core.agent_decisions.models import AgentExecutionDecision
from core.agent_decisions.reason_codes import CONTRACT_VERSION, ReasonCode
from core.audit import record_event
from integrations.models import AgentToolGrant
from users.models import User
from users.tokens import AuthToken

DEFAULT_TTL_SECONDS = 60


class AuthorizationServiceUnavailable(Exception):
    """Raised when decision persistence/evaluation cannot proceed safely."""


@dataclass(frozen=True)
class DecisionRequest:
    request_id: uuid.UUID
    decision_nonce: str
    adapter_type: str
    capability_key: str
    material_action: str
    arguments: dict[str, Any]
    work_context: dict[str, Any]
    principal_id: int | None = None


@dataclass(frozen=True)
class DecisionResponse:
    contract_version: str
    decision_id: uuid.UUID
    request_id: uuid.UUID
    decision_nonce: str
    outcome: str
    reason_code: str
    argument_binding: str
    expires_at: str
    qms_version: str
    policy_version: str


def _ttl_seconds() -> int:
    return int(getattr(settings, 'AGENT_DECISION_TTL_SECONDS', DEFAULT_TTL_SECONDS))


def _qms_version() -> str:
    return str(getattr(settings, 'QMS_VERSION', 'agents-os/dev'))


def _policy_version() -> str:
    return str(getattr(settings, 'AGENT_DECISION_POLICY_VERSION', 'agent-decision-policy/0.1'))


def _simulate_outage() -> bool:
    return bool(getattr(settings, 'AGENT_DECISION_FORCE_OUTAGE', False))


def _normalized_tool_name(capability_key: str, material_action: str) -> str:
    return f'{capability_key}:{material_action}'


def _has_capability(agent: User, capability_key: str, material_action: str) -> bool:
    tool_name = _normalized_tool_name(capability_key, material_action)
    return AgentToolGrant.objects.filter(agent_id=agent.pk, tool_name=tool_name).exists()


def authorize_execution(
    *,
    agent: User,
    request: DecisionRequest,
    auth_token: AuthToken | None = None,
) -> DecisionResponse:
    """Evaluate one per-call authorization request. Deny-by-default."""
    if _simulate_outage():
        raise AuthorizationServiceUnavailable('QMS authorization unavailable.')

    if not getattr(agent, 'is_agent', False):
        raise ValidationError('Agent principal required.')

    expires_at = timezone.now() + timedelta(seconds=_ttl_seconds())
    expires_at_iso = expires_at.isoformat()
    principal_id = int(request.principal_id or agent.pk)
    argument_binding = compute_argument_binding(
        agent_id=agent.pk,
        principal_id=principal_id,
        adapter_type=request.adapter_type,
        capability_key=request.capability_key,
        material_action=request.material_action,
        arguments=request.arguments,
        work_context=request.work_context,
        policy_version=_policy_version(),
        decision_nonce=request.decision_nonce,
        expires_at=expires_at_iso,
    )

    if AgentExecutionDecision.objects.filter(decision_nonce=request.decision_nonce).exists():
        outcome = AgentExecutionDecision.OUTCOME_DENY
        reason = ReasonCode.REPLAY_DETECTED
    elif not _has_capability(agent, request.capability_key, request.material_action):
        outcome = AgentExecutionDecision.OUTCOME_DENY
        reason = ReasonCode.NO_AUTHORITY
    else:
        outcome = AgentExecutionDecision.OUTCOME_ALLOW
        reason = ReasonCode.ALLOW

    try:
        with transaction.atomic():
            decision = AgentExecutionDecision.objects.create(
                request_id=request.request_id,
                decision_nonce=request.decision_nonce,
                agent=agent,
                principal_id=principal_id,
                adapter_type=request.adapter_type,
                capability_key=request.capability_key,
                material_action=request.material_action,
                argument_binding=argument_binding,
                work_context=request.work_context,
                arguments=request.arguments,
                outcome=outcome,
                reason_code=str(reason),
                contract_version=CONTRACT_VERSION,
                qms_version=_qms_version(),
                policy_version=_policy_version(),
                expires_at=expires_at,
                auth_token=auth_token,
            )
            record_event(
                action='agent_decision.authorized',
                actor=agent,
                entity_type='AgentExecutionDecision',
                entity_id=str(decision.decision_id),
                details={
                    'request_id': str(decision.request_id),
                    'decision_nonce': decision.decision_nonce,
                    'outcome': decision.outcome,
                    'reason_code': decision.reason_code,
                    'adapter_type': decision.adapter_type,
                    'argument_binding': decision.argument_binding,
                },
            )
    except Exception as exc:
        raise AuthorizationServiceUnavailable(str(exc)) from exc

    return DecisionResponse(
        contract_version=CONTRACT_VERSION,
        decision_id=decision.decision_id,
        request_id=decision.request_id,
        decision_nonce=decision.decision_nonce,
        outcome=decision.outcome,
        reason_code=decision.reason_code,
        argument_binding=decision.argument_binding,
        expires_at=expires_at_iso,
        qms_version=decision.qms_version,
        policy_version=decision.policy_version,
    )


@dataclass(frozen=True)
class VerifiedDecision:
    decision: AgentExecutionDecision


def verify_and_consume_decision(
    *,
    agent: User,
    decision_id: uuid.UUID,
    decision_nonce: str,
    argument_binding: str,
) -> VerifiedDecision:
    """Fail-closed verification immediately before material execution."""
    if _simulate_outage():
        raise AuthorizationServiceUnavailable('QMS authorization unavailable.')

    try:
        with transaction.atomic():
            decision = (
                AgentExecutionDecision.objects.select_for_update()
                .select_related('agent')
                .get(decision_id=decision_id)
            )
    except AgentExecutionDecision.DoesNotExist as exc:
        raise ValidationError('Unknown decision.') from exc

    if decision.agent_id != agent.pk:
        raise ValidationError('Decision agent mismatch.')
    if decision.decision_nonce != decision_nonce:
        raise ValidationError('Decision nonce mismatch.')
    if decision.argument_binding != argument_binding:
        raise ValidationError(str(ReasonCode.BINDING_MISMATCH))
    if timezone.now() >= decision.expires_at:
        raise ValidationError(str(ReasonCode.DECISION_EXPIRED))
    if not decision.is_allow:
        raise ValidationError(decision.reason_code or str(ReasonCode.POLICY_DENY))
    if decision.is_consumed:
        raise ValidationError(str(ReasonCode.REPLAY_DETECTED))

    decision.consumed_at = timezone.now()
    decision.save(update_fields=['consumed_at'])
    record_event(
        action='agent_decision.consumed',
        actor=agent,
        entity_type='AgentExecutionDecision',
        entity_id=str(decision.decision_id),
        details={'decision_nonce': decision.decision_nonce},
    )
    return VerifiedDecision(decision=decision)
