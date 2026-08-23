"""Persisted agent execution decisions and nonce consumption."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class AgentExecutionDecision(models.Model):
    """Short-lived, argument-bound allow/deny decision for one material action."""

    OUTCOME_ALLOW = 'ALLOW'
    OUTCOME_DENY = 'DENY'
    OUTCOME_FAIL_CLOSED = 'FAIL_CLOSED'

    decision_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    request_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    decision_nonce = models.CharField(max_length=128, unique=True, db_index=True)

    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='execution_decisions',
        limit_choices_to={'kind': 'agent'},
    )
    principal_id = models.PositiveBigIntegerField()
    adapter_type = models.CharField(max_length=64, db_index=True)
    capability_key = models.CharField(max_length=128, db_index=True)
    material_action = models.CharField(max_length=256)
    argument_binding = models.CharField(max_length=128)
    work_context = models.JSONField(default=dict)
    arguments = models.JSONField(default=dict)

    outcome = models.CharField(max_length=32, db_index=True)
    reason_code = models.CharField(max_length=64, db_index=True)
    contract_version = models.CharField(max_length=64)
    qms_version = models.CharField(max_length=64)
    policy_version = models.CharField(max_length=64)

    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(db_index=True)
    consumed_at = models.DateTimeField(null=True, blank=True, db_index=True)

    auth_token = models.ForeignKey(
        'users.AuthToken',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='execution_decisions',
    )

    class Meta:
        ordering = ('-issued_at',)
        indexes = [
            models.Index(fields=['agent', 'adapter_type', 'outcome']),
        ]

    @property
    def is_allow(self) -> bool:
        return self.outcome == self.OUTCOME_ALLOW

    @property
    def is_consumed(self) -> bool:
        return self.consumed_at is not None
