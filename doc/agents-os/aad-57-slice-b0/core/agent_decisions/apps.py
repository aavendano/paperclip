from django.apps import AppConfig


class AgentDecisionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core.agent_decisions'
    label = 'agent_decisions'
    verbose_name = 'Agent execution decisions'
