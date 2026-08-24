# AAD-57 — Slice B-1 harness and test plan

**Status:** Required Slice B-0 deliverable (test plan only). **Architecture NOT APPROVED.**

**Prerequisite:** All Slice B-0 gates (B-0.1–B-0.4) must **PASS** before B-1 cases are interpretable as architecture evidence.

**Strict thresholds:** Devin PASS/FAIL thresholds from Architecture Proposal v0.4 (AAD-56). Any FAIL keeps architecture NOT APPROVED.

---

## Harness topology

```
┌─────────────────┐     mint ALLOW/DENY      ┌──────────────────────┐
│  Lab agent      │ ───────────────────────► │ QMS                  │
│  (AuthToken)    │ POST /api/agent/         │ action-decisions     │
└────────┬────────┘     action-decisions/   └──────────┬───────────┘
         │                                               │
         │  __agent_action_credentials                   │ consume + audit
         ▼                                               ▼
┌─────────────────┐   transport (demoted)    ┌──────────────────────┐
│ Paperclip lab   │ ◄─────────────────────── │ Material choke points│
│ heartbeat/run   │   run_id, task_id refs   │ (≥3 adapters)        │
└─────────────────┘                          └──────────────────────┘
         Adapters under test:
         • python provider (workflows/providers/dispatch.py)
         • service/BPMN (workflows/bpmn/executor.py)
         • process spawn (work_orders/services.py) — after rework
         • MCP managed tools (integrations/mcp/dispatch.py) — after rework
         • Hermes (Paperclip lab adapter) — optional 5th for cross-system
```

**Harness repo locations:**

| Component | Repository | Notes |
|---|---|---|
| QMS decision endpoint + enforcement | `aavendano/agents-os` | PR #263 + rework |
| Paperclip heartbeat/transport | `aavendano/paperclip` | Lab comparator only |
| Hermes provider | `aavendano/hermes-agent` | Replaceable adapter |
| Test orchestration | `agents-os` test suite + optional Paperclip e2e script | See commands below |

---

## B-0 gate verification (blocking)

| Gate | Harness check | Pass command | Pass criterion |
|---|---|---|---|
| B-0.1 | Agent-authenticated endpoint callable | `manage.py test core.agent_decisions.tests.test_api` | 200 ALLOW/DENY with audit |
| B-0.2 | Argument binding | `test_services` binding mismatch cases | DENY on hash mismatch |
| B-0.3 | ≥3 adapters incl. `process` | `test_enforcement` + spawn + MCP tests | Zero execution without credential on all wired adapters |
| B-0.4 | Short TTL + nonce replay | expiry + replay tests | Second consume fails; spawn JWT alone fails |

**Current status (PR #263 head `93caa0c`):** B-0.1, B-0.2, B-0.4 **PASS**; B-0.3 **FAIL** (process spawn + MCP open).

---

## B-1 test matrix (B0–B10)

Execute only after B-0 PASS. Each case records: `decision_id`, `request_id`, `nonce`, `argument_hash`, `adapter_type`, `qms_version`, `policy_version`, `reason_code`, `run_id` (transport), `agent_profile_id`.

| Case | Setup | Action | Expected | Thresholds |
|---|---|---|---|---|
| **B0** Positive | Grants + authority; fresh nonce | Mint ALLOW → execute via each wired adapter | One authorized execution; full QMS correlation | #1, #10 |
| **B1** Denied | Policy/capability/authority deny | Mint or auto-DENY → attempt execution | Zero material effects; deny-before-tool | #1, #2 |
| **B2** Alternate adapter bypass | B1 denial on adapter A | Same args via B, C, D (≥3 incl. process) | Zero unauthorized across all | #1 |
| **B3** Managed MCP bypass | B1 denial | Invoke MCP tool without fresh ALLOW | No material effect | #1, #2 |
| **B4** QMS timeout/outage | `AGENT_DECISION_FORCE_OUTAGE=True` or network block | Execute after mint | Fail-closed; no execution | #7 |
| **B4b** Outage + stale credential | Prior unconsumed ALLOW; QMS down | New material attempt | No execution despite prior row | #7 |
| **B5** Replay | ALLOW consumed once | Reuse same nonce | Replay rejection | #4 |
| **B6** Argument mutation | ALLOW for args P | Execute with P′ | Binding rejection | #3 |
| **B7** TTL expiry | ALLOW near expiry | Execute after `expires_at` | Deny | #5 |
| **B8** Stale gate | Gate revoked after ALLOW (when implemented) | Execute with stale ref | Deny | #6 |
| **B9** Duplicate heartbeat | First dispatch in flight or complete | Second heartbeat same work unit | ≤1 material execution | #8 |
| **B10** Lifecycle audit | Any B0–B9 | Trace all transitions | One owner per transition; QMS reconstructible | #9, #10 |

---

## Devin PASS/FAIL thresholds (strict)

Slice B **PASSES** only if **all** rows PASS on in-scope paths.

| # | Threshold | PASS | FAIL |
|---|---|---|---|
| 1 | Unauthorized material actions across **≥3 adapters including `process`** | **Zero** | ≥1 unauthorized action |
| 2 | Deny-before-tool | No material effect before/on DENY | Effect despite DENY |
| 3 | Argument mutation rejection | P′ blocked after ALLOW(P) | Execution with P′ |
| 4 | Replay rejection | Reused nonce blocked | Second execution |
| 5 | TTL expiry | Post-expiry blocked | Execution after TTL |
| 6 | Stale/revoked gate | Revoked gate blocks | Execution despite revocation |
| 7 | QMS outage fail-closed | No new material actions during outage | Material action during outage |
| 8 | Duplicate heartbeat exactly-once | ≤1 material execution per logical unit | Duplicate effects |
| 9 | One owner per lifecycle transition | Single authoritative owner in audit | Conflicting writers |
| 10 | QMS-only reconstructible correlation | Full chain from QMS `decision_id` | Requires Paperclip-only ids or session keys |

**Automatic FAIL triggers:**

- Any in-scope adapter executes without consumed ALLOW
- `work_orders/services.py` spawn without gate (pre-rework)
- MCP tool executes with capability grant only (pre-rework)
- Unmanaged path inventory gaps (G-1..G-5) not documented in lab report

---

## Test commands (agents-os)

```bash
# Targeted B-0 / enforcement suite (PR #263 baseline)
.venv/bin/python manage.py test core.agent_decisions.tests --verbosity=2

# Workflow runtime (dispatch + verifier + BPMN)
.venv/bin/python manage.py test workflows.tests.test_runtime --verbosity=1

# After rework — add:
.venv/bin/python manage.py test work_orders.tests.test_spawn_authorization --verbosity=2
.venv/bin/python manage.py test integrations.mcp.tests.test_dispatch_authorization --verbosity=2

# Full CI (required before B-1 evidence claim)
make ci
```

---

## End-to-end correlation script (B0 smoke)

Pseudocode for lab operator or CI job:

```python
# 1. Mint
resp = agent_client.post('/api/agent/action-decisions/', json={
    'request_id': str(uuid4()),
    'scope': {'work_order_id': wo.id, 'run_id': run.id, 'process_id': wo.process_id,
              'agent_profile_id': profile.id},
    'action': 'process.agent',
    'arguments': {'command': ['echo', 'b1-smoke'], 'cwd': '/tmp'},
    'nonce': secrets.token_hex(16),
})
assert resp['decision'] == 'ALLOW'
decision_id = resp['decision_id']

# 2. Execute with credential map
spawn_payload = {
    '__agent_action_credentials': {
        'process.agent': {'decision_id': decision_id, 'nonce': resp['nonce']},
    },
    'command': ['echo', 'b1-smoke'],
}
result = spawn_agent_subprocess(work_order=wo, run=run, payload=spawn_payload)
assert result.returncode == 0

# 3. Verify audit + consumption
row = AgentActionDecision.objects.get(decision_id=decision_id)
assert row.consumed_at is not None
assert audit_contains('agent_action_decision.consume', decision_id=decision_id)

# 4. Replay must fail (B5)
with pytest.raises(AgentActionAuthzError):
    spawn_agent_subprocess(..., same credential ...)
```

---

## Evidence artifacts (required for Direction review)

| Artifact | Location |
|---|---|
| Unmanaged path inventory | `doc/agents-os/AAD-57-UNMANAGED-PATH-INVENTORY.md` |
| Demotion matrix | `doc/agents-os/AAD-57-LIFECYCLE-DEMOTION-MATRIX.md` |
| This harness plan | `doc/agents-os/AAD-57-SLICE-B1-HARNESS-PLAN.md` |
| CI logs | agents-os `make ci` run URL |
| Test count evidence | 44+ core tests + runtime + rework tests |
| Lab report | Linear AAD-57 comment or linked doc with per-case PASS/FAIL |

---

## Falsification mapping (post B-0)

| Hypothesis | Falsified when |
|---|---|
| H1 (revised) | Thresholds 1–10 fail |
| H2′ (future single QMS authority) | Threshold 9 or 10 fail |
| ADR-0060 | Paperclip backend required beyond lab transport |
| H3 | Session-key used as correlation proof |

**Architecture approval remains NOT APPROVED** until B-0 pass + B-1 all thresholds PASS + unmanaged gaps documented with Direction risk acceptance.
