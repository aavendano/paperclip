# Add to INSTALLED_APPS in config/settings.py (or local overlay):
#   'core.agent_decisions',

# Add to core/agents/api_router.py (after existing imports):
#
#   from core.agent_decisions.api import router as agent_decisions_router
#   router.add_router('/v1/', agent_decisions_router)
#
# Resulting endpoint:
#   POST /api/agent/v1/decisions/authorize
#
# Distinct from Operational API:
#   /api/operational/v1/*  (human operator + Core-MS service token)

# Optional settings defaults:
#   AGENT_DECISION_TTL_SECONDS = 60
#   AGENT_DECISION_POLICY_VERSION = 'agent-decision-policy/0.1'
#   QMS_VERSION = 'agents-os/dev'
#   AGENT_DECISION_FORCE_OUTAGE = False  # tests only
