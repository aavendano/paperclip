"""Stable machine reason codes for agent execution decisions."""

from __future__ import annotations

from enum import StrEnum


class ReasonCode(StrEnum):
    ALLOW = 'ALLOW'
    POLICY_DENY = 'POLICY_DENY'
    NO_AUTHORITY = 'NO_AUTHORITY'
    CAPABILITY_UNAVAILABLE = 'CAPABILITY_UNAVAILABLE'
    REPLAY_DETECTED = 'REPLAY_DETECTED'
    BINDING_MISMATCH = 'BINDING_MISMATCH'
    DECISION_EXPIRED = 'DECISION_EXPIRED'
    FAIL_CLOSED = 'FAIL_CLOSED'
    QMS_UNAVAILABLE = 'QMS_UNAVAILABLE'


CONTRACT_VERSION = 'qms-agent-decision/0.1'
