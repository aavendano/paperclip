# AAD-57 — Lifecycle authority demotion matrix

**Status:** Required Slice B-0 deliverable. **Architecture NOT APPROVED.** ADR-0060 remains controlling.

**Purpose:** For every lifecycle transition under test, identify which Paperclip authority is **disabled/demoted**, which QMS/Core owner becomes **canonical**, and what evidence proves the demotion during Slice B-1 falsification.

**Baseline conflict (AAD-56):** Paperclip backend currently owns heartbeat/task/run lifecycle and issues argument-bound signed decisions. QMS owns Human Gates and tool-name grants. This is structural double governance — not resolved by documentation alone.

---

## Legend

| Symbol | Meaning |
|---|---|
| **CANONICAL** | Sole authoritative writer for this transition in target runtime |
| **DEMOTED** | Retained for lab/transport only; writes must not affect governed state |
| **DISABLED** | Must not execute this transition during B-1 test runs |
| **CONFLICT** | Both systems write today — demotion required before architecture approval |
| **OPEN** | Owner unassigned; blocks threshold #9 |

---

## Transition matrix

| Transition | Current owner(s) | Paperclip under test | QMS under test | Target canonical | Demotion action for B-1 |
|---|---|---|---|---|---|
| **T1** Agent/task scheduling wakeup | Paperclip heartbeat scheduler | **DEMOTED** — trigger only via lab harness script | **CANONICAL** — `WorkOrder` enqueue | QMS | Disable Paperclip auto-heartbeat; QMS owns enqueue |
| **T2** Work/run creation | Paperclip (`issues`, `heartbeat_runs`) | **DEMOTED** — create lab run as transport record only | **CANONICAL** — `Run` + scope in decision | QMS | Paperclip run id stored as `work_context.run_id` reference, not authority |
| **T3** Pre-execution capability check | QMS `AgentToolGrant` + Paperclip grants | **DISABLED** for capability-only path | **CANONICAL** — capability probe at mint | QMS | Remove Paperclip grant checks from test path |
| **T4** Pre-execution authority decision | **CONFLICT** Paperclip signed decisions + QMS (new endpoint) | **DISABLED** — no Paperclip `authorization.ts` ALLOW for material | **CANONICAL** — `POST /api/agent/action-decisions/` | QMS | Paperclip approval routes return 403 or are bypassed in harness |
| **T5** Material execution (process spawn) | **OPEN** — `work_orders/services.py` unwired | N/A | **CANONICAL** after rework — consume before Popen | QMS | Wire spawn gate; block direct Popen |
| **T6** Material execution (workflow provider) | QMS `dispatch.py` (PR #263) | N/A | **CANONICAL** | QMS | Already wired; verify per-action credentials |
| **T7** Material execution (MCP tool) | **CONFLICT** — capability only | Paperclip MCP gateway (lab) | **CANONICAL** after rework | QMS | Demote Paperclip MCP gateway to read-only proxy or disable |
| **T8** Material execution (Hermes remote) | Hermes + Paperclip adapter | **DEMOTED** — transport/session only | **CANONICAL** decision mint in QMS before Hermes invoke | QMS | Hermes session key ≠ authorization |
| **T9** Execution lock / single-flight | Paperclip checkout/lock | **DISABLED** | **CANONICAL** — QMS run state + decision nonce | QMS | Disable Paperclip atomic checkout in harness |
| **T10** Retry / duplicate heartbeat | Paperclip + Hermes session resume | **DISABLED** duplicate material path | **CANONICAL** — nonce exactly-once | QMS | Second heartbeat must not re-consume or bypass |
| **T11** Cancellation | Paperclip + Hermes | **DEMOTED** — signal only | **CANONICAL** — QMS run terminal + revoke unconsumed decisions | QMS | Cancel does not authorize new material actions |
| **T12** Completion / terminal state | Paperclip run status | **DEMOTED** — mirror QMS state | **CANONICAL** | QMS | Paperclip status is projection |
| **T13** Human Gate / acceptance | QMS Human Gate | Projection only | **CANONICAL** | QMS | Paperclip approval UI may display; no separate approval record |
| **T14** Escalation record | **OPEN** (missing `EscalationRecord`) | N/A | **CANONICAL** (when H4 infra exists) | QMS → Linear | Stub or defer in B-1; document UNKNOWN |
| **T15** Durable identity | QMS `AgentProfile` vs session keys | **DISABLED** session-key identity | **CANONICAL** — `AgentProfile.identity` | QMS | Reject correlation proofs using Hermes/Paperclip session keys |
| **T16** Correlation ID issuance | **CONFLICT** Paperclip run ids vs QMS `decision_id` | **DEMOTED** — transport ids only | **CANONICAL** — `decision_id` reconstructible | QMS | Threshold #10: full chain from QMS `decision_id` |

---

## Per-transition demotion checklist (B-1 harness configuration)

Before each B-1 case executes, the harness must verify:

| Check | Pass criterion |
|---|---|
| D-1 | Paperclip backend material authorization endpoints are not called (or return DENY) |
| D-2 | QMS decision endpoint is the only ALLOW source for in-scope adapters |
| D-3 | Paperclip heartbeat cannot spawn subprocess without QMS credential in payload |
| D-4 | MCP tools reject execution without consumed QMS decision (post rework) |
| D-5 | Hermes invoke requires QMS mint immediately before remote call |
| D-6 | Lifecycle state writes to Paperclip tables are read-only mirrors in test env |
| D-7 | Audit log contains QMS `decision_id` for every material effect |

---

## Revocation and outage semantics (T4, T10, T11)

Already-running local or remote providers may hold previously issued credentials. Required behavior:

| Scenario | Paperclip spawn JWT / session | QMS per-action decision | Required behavior |
|---|---|---|---|
| QMS outage mid-run | May still be valid for **identity** | Unconsumable | **Fail-closed** — no new material actions |
| Agent profile paused after mint | Unaffected | ALLOW row exists | **Deny at consume** — `REASON_CONSUME_PROFILE_INACTIVE` |
| User deactivated after mint | Token may work for API | ALLOW row exists | **Deny at consume** — `REASON_CONSUME_AGENT_INACTIVE` |
| Decision TTL expired | N/A | Expired row | **Deny at consume** — `REASON_CONSUME_EXPIRED` |
| Nonce replay | N/A | Already consumed | **Deny** — `REASON_CONSUME_REPLAY` |
| Gate revoked (future) | N/A | Stale `gateRef` | **Deny** — B-8 case |

**Spawn JWT (48h) must never authorize material execution alone** (B-0.4 rejected alternative).

---

## Mapping to Architecture Proposal v0.4 authority matrix

This matrix operationalizes the CONFLICT/OPEN rows in `ARCHITECTURE-PROPOSAL-v0.1.md` § Authority and lifecycle matrix. Slice B-1 case **B10 — Lifecycle owner audit** validates every row marked CONFLICT → CANONICAL/DEMOTED.

---

## References

- AAD-56 independent falsification (structural duplication finding)
- agents-os PR #263 enforcement module
- Unmanaged path inventory: `doc/agents-os/AAD-57-UNMANAGED-PATH-INVENTORY.md`
- B-1 harness: `doc/agents-os/AAD-57-SLICE-B1-HARNESS-PLAN.md`
