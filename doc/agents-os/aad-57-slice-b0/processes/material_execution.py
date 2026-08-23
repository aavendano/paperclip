"""Material execution choke point for adapter_type=process (Slice B-0)."""

from __future__ import annotations

import subprocess
import uuid
from dataclasses import dataclass
from typing import Sequence

from django.core.exceptions import ValidationError

from core.agent_decisions.services import (
    AuthorizationServiceUnavailable,
    verify_and_consume_decision,
)
from users.models import User


@dataclass(frozen=True)
class ProcessExecutionResult:
    returncode: int
    stdout: str
    stderr: str


class ProcessExecutionDenied(Exception):
    """Material execution blocked by authorization boundary."""


def execute_process_material_action(
    *,
    agent: User,
    decision_id: uuid.UUID,
    decision_nonce: str,
    argument_binding: str,
    command: Sequence[str],
    timeout_seconds: int = 30,
) -> ProcessExecutionResult:
    """Run one subprocess only after QMS decision verification."""
    if not command:
        raise ValidationError('command is required.')

    try:
        verify_and_consume_decision(
            agent=agent,
            decision_id=decision_id,
            decision_nonce=decision_nonce,
            argument_binding=argument_binding,
        )
    except AuthorizationServiceUnavailable as exc:
        raise ProcessExecutionDenied('QMS unavailable.') from exc
    except ValidationError as exc:
        raise ProcessExecutionDenied(str(exc)) from exc

    completed = subprocess.run(
        list(command),
        capture_output=True,
        text=True,
        timeout=max(1, timeout_seconds),
        check=False,
    )
    return ProcessExecutionResult(
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
