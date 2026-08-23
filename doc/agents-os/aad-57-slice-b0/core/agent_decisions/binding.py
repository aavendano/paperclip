"""Canonical argument binding for per-action authorization."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str)


def compute_argument_binding(
    *,
    agent_id: int,
    principal_id: int,
    adapter_type: str,
    capability_key: str,
    material_action: str,
    arguments: dict[str, Any],
    work_context: dict[str, Any],
    policy_version: str,
    decision_nonce: str,
    expires_at: str,
) -> str:
    payload = {
        'agent_id': agent_id,
        'principal_id': principal_id,
        'adapter_type': adapter_type,
        'capability_key': capability_key,
        'material_action': material_action,
        'arguments': arguments,
        'work_context': work_context,
        'policy_version': policy_version,
        'decision_nonce': decision_nonce,
        'expires_at': expires_at,
    }
    digest = hashlib.sha256(canonical_json(payload).encode('utf-8')).hexdigest()
    return f'sha256:{digest}'
