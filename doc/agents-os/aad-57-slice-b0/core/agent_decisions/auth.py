"""Authentication for agent decision endpoints (distinct from Operational API)."""

from __future__ import annotations

from ninja.security import HttpBearer

from integrations.oauth.bearer import resolve_request_principal


class AgentDecisionAuth(HttpBearer):
    """Require a native QMS agent bearer token.

    Unlike ``CoreMsOperationalAuth``, this surface is agent-authenticated only.
    Human operator tokens and Core-MS service tokens are rejected.
    """

    def authenticate(self, request, token: str):
        principal = resolve_request_principal(token, require_human=False)
        if principal is None:
            return None
        user = principal.user
        if not getattr(user, 'is_agent', False):
            return None
        if not getattr(user, 'is_active', False):
            return None
        request.agent_auth_token = principal.auth_token
        return user
