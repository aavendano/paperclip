"""HTTP adapter for agent-authenticated execution decisions."""

from __future__ import annotations

import uuid

from django.core.exceptions import ValidationError
from ninja import Router, Schema
from ninja.errors import HttpError

from core.agent_decisions.auth import AgentDecisionAuth
from core.agent_decisions.reason_codes import CONTRACT_VERSION, ReasonCode
from core.agent_decisions.services import (
    AuthorizationServiceUnavailable,
    DecisionRequest,
    authorize_execution,
)

router = Router(auth=AgentDecisionAuth(), tags=['agent-decisions-v1'])


class AuthorizeExecutionIn(Schema):
    contract_version: str = CONTRACT_VERSION
    request_id: uuid.UUID
    decision_nonce: str
    adapter_type: str
    capability_key: str
    material_action: str
    arguments: dict = {}
    work_context: dict = {}
    principal_id: int | None = None


class AuthorizeExecutionOut(Schema):
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


@router.post('/decisions/authorize', response=AuthorizeExecutionOut)
def authorize_execution_endpoint(request, payload: AuthorizeExecutionIn):
    if payload.contract_version != CONTRACT_VERSION:
        raise HttpError(400, 'Unsupported contract_version.')

    try:
        response = authorize_execution(
            agent=request.auth,
            auth_token=getattr(request, 'agent_auth_token', None),
            request=DecisionRequest(
                request_id=payload.request_id,
                decision_nonce=payload.decision_nonce,
                adapter_type=payload.adapter_type,
                capability_key=payload.capability_key,
                material_action=payload.material_action,
                arguments=payload.arguments,
                work_context=payload.work_context,
                principal_id=payload.principal_id,
            ),
        )
    except AuthorizationServiceUnavailable as exc:
        raise HttpError(503, str(ReasonCode.QMS_UNAVAILABLE)) from exc
    except ValidationError as exc:
        raise HttpError(400, str(exc)) from exc

    return AuthorizeExecutionOut(
        contract_version=response.contract_version,
        decision_id=response.decision_id,
        request_id=response.request_id,
        decision_nonce=response.decision_nonce,
        outcome=response.outcome,
        reason_code=response.reason_code,
        argument_binding=response.argument_binding,
        expires_at=response.expires_at,
        qms_version=response.qms_version,
        policy_version=response.policy_version,
    )
