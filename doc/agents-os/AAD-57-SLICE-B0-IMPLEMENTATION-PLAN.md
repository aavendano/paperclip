# AAD-57 — Slice B-0 implementation plan

**Status:** Patch bundle prepared in Paperclip PR; **not yet applied** in `aavendano/agents-os` from this Cloud Agent context.

**Architecture remains NOT APPROVED.** ADR-0060 remains controlling. Paperclip backend remains lab comparator.

## Blocker encountered in Cloud Agent

The Cloud Agent token can create GitHub issues on `aavendano/agents-os` but **cannot clone, read contents, create branches, or open PRs** (403 on git/refs and contents APIs). Implementation is therefore delivered as an **exact patch bundle** in this repository:

```text
doc/agents-os/aad-57-slice-b0/
```

Tracking issue opened in QMS repo: **https://github.com/aavendano/agents-os/issues/257**

## Objective (Linear AAD-57)

Implement minimum callable, **agent-authenticated** QMS per-action authorization decision endpoint and wire **one** material execution path (`process`) through it.

Satisfies Slice B-0 gates **B-0.1**, **B-0.2** (argument binding), **B-0.3** (first of ≥3 adapters), **B-0.4** (short-lived nonce/TTL).

## What the patch implements

| Component | Path in agents-os | Purpose |
|---|---|---|
| Agent decision auth | `core/agent_decisions/auth.py` | Agent bearer only; rejects Operational API pattern |
| Decision persistence | `core/agent_decisions/models.py` | Auditable allow/deny + nonce + binding + TTL |
| Binding + reason codes | `binding.py`, `reason_codes.py` | Argument hash; stable machine reasons |
| Authorization service | `services.py` | Deny-by-default; Capability (`AgentToolGrant`) ≠ Authority (bound decision) |
| HTTP endpoint | `api.py` | `POST /api/agent/v1/decisions/authorize` |
| Process choke point | `processes/material_execution.py` | Subprocess only after `verify_and_consume_decision` |
| Tests | `core/agent_decisions/tests.py` | allow, deny, replay, expiry, binding mismatch, outage, process path |

### Endpoint contract

- **URL:** `POST /api/agent/v1/decisions/authorize`
- **Auth:** `Authorization: Bearer <QMS AuthToken for agent>`
- **Not:** `/api/operational/v1/*` (operator + Core-MS service token)
- **Contract:** `qms-agent-decision/0.1`

### Capability vs Authority

- **Capability probe:** existing `AgentToolGrant` on normalized key `{capability_key}:{material_action}` (tool-name layer retained, not sufficient alone).
- **Authority decision:** persisted `AgentExecutionDecision` with `argument_binding`, `decision_nonce`, short TTL, auditable `decision_id`.
- **Material execution:** requires consumed ALLOW decision; 48h spawn/JWT credentials do **not** authorize material actions.

### Process material path

`processes/material_execution.execute_process_material_action(...)` verifies decision then runs `subprocess.run(...)`. This is the first B-0.3 adapter surface; Hermes/Paperclip adapters remain future work in QMS/Paperclip lab harness.

## Apply instructions (human or agents-os Cloud Agent)

```bash
# In agents-os repo root on branch cursor/aad-57-slice-b0-c417 from master
bash /path/to/paperclip/doc/agents-os/aad-57-slice-b0/apply-to-agents-os.sh

# Wire router + INSTALLED_APPS per PATCHES.md

.venv/bin/python manage.py makemigrations agent_decisions
.venv/bin/python manage.py migrate

# Targeted tests
.venv/bin/python manage.py test core.agent_decisions.tests --verbosity=2

# Repository standard CI
make ci
```

## Expected test coverage (acceptance criteria mapping)

| AC | Test |
|---|---|
| Callable endpoint with allow/deny + audit | `AgentDecisionApiTests`, `AgentDecisionServiceTests.test_allow_*`, `test_deny_*` |
| Process path blocked without ALLOW | `ProcessMaterialExecutionTests.test_process_path_denied_without_decision` |
| QMS outage/timeout fail-closed | `test_qms_unavailable_fail_closed`, `test_process_path_fail_closed_on_qms_outage` |
| Argument mismatch | `test_reject_argument_mismatch_at_consume` |
| Expiry + replay | `test_reject_expired_decision`, `test_reject_replayed_nonce` |
| No Authority | `test_deny_without_authority` |

## CI commands (agents-os standard)

From merged PR #256 verification pattern:

```bash
.venv/bin/python manage.py test core.agent_decisions.tests --verbosity=2
make ci
# migrate-check, django-check, ruff, mypy, full test suite, test-scripts
```

**Not run from Paperclip Cloud Agent** — no agents-os checkout access.

## Paperclip PR scope (this repo)

- Patch bundle + plan only
- Architecture proposal experiment evidence link
- **No Paperclip backend canonicalization**
- **Do not merge** architecture PR

## Next after merge in agents-os

1. Record agents-os PR URL in Paperclip architecture doc (B-0.1 evidence).
2. Re-evaluate H1 from UNKNOWN → testable if endpoint + process choke point green.
3. Proceed toward B-0.3 adapters 2–3 before Slice B-1.

## Open gaps (unchanged)

- Unmanaged MCP/host execution remains out-of-scope.
- Lifecycle duplication Paperclip vs QMS not resolved by this slice.
- Hermes session-key identity risk (H3 WEAKENED) unchanged.
