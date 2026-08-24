# Architecture Proposal v0.4 — Paperclip × Agents-OS Core × Hermes

**Status:** **NOT APPROVED.** Revised after Cursor adversarial review (AAD-52), Codex second-pass critique (AAD-55), and independent Devin falsification review (AAD-56). Architecture approval is withheld pending Slice B-0 prerequisites and Slice B falsification evidence. **ADR-0060 remains controlling** until Direction or a formal ADR supersedes it.

**Experiment order:** **Slice B-0 → Slice B → Slice A.** Slice B cases B1–B10 are not interpretable as evidence for H1/H2 until Slice B-0 prerequisites pass. Slice A remains deferred.

---

## Terminology: do not conflate Core library with QMS authority

| Term | Meaning in this document |
|---|---|
| **`agents-os-core`** | Library/spec boundary. Per AAD-56, it has **no executable authorization endpoint** today. Referencing it as runtime authority is incorrect without new implementation. |
| **`agents-os` (QMS)** | Implemented governance authority in the QMS codebase. Current grants (`AgentToolGrant`) are **tool-name-only** without argument binding. |
| **Paperclip backend** | Lab comparator. Already implements **argument-bound signed decisions** and owns heartbeat/task/run lifecycle in practice. |
| **Core (target)** | Normative governance boundary this experiment aims toward. Not synonymous with `agents-os-core` as deployed today, nor with Paperclip backend lifecycle. |

This proposal does **not** silently rename QMS implementation as Core or treat `agents-os-core` as if it were already executable authority.

---

## Document classification

### SUPPORTED requirements

| Requirement | Notes |
|---|---|
| Paperclip frontend as organization/operator UX | Presentation for hierarchy, work state, approvals, activity. May project QMS state. |
| One semantic authorization decision (target) | QMS Human Gate is the intended authoritative semantic decision. Paperclip may project/submit; separate Paperclip approval records must be non-authoritative, reconstructible, or absent in target runtime. **Conflict:** Paperclip backend already issues argument-bound signed decisions — see H2 and explicit disagreements. |
| Hermes as replaceable cognitive/runtime provider | Experimental provider only; not canonical principal or memory authority. |
| Linear as engineering SSoT for missing-capability work | Tracks implementation status; not user-memory or business-domain SSoT. |
| Paperclip backend as lab comparator only | Adapters, heartbeat, approvals, MCP gateway, Hermes integration are falsification harness material under ADR-0060. Not canonical authority. |
| Fail-closed authorization on QMS outage | If QMS cannot decide synchronously within bounds, material execution must not proceed. Already-issued credentials must not authorize new material actions during outage. |
| ADR-0060 controlling | Paperclip presentation permitted; Paperclip backend not canonical runtime authority. |

### Hypothesis reclassification (AAD-56 evidence)

| ID | v0.3 status | **v0.4 status** | Confidence / evidence |
|---|---|---|---|
| **H1** | Hypothesis (testable via Slice B) | **UNKNOWN / untestable as written** | **Evidence (AAD-56):** `agents-os-core` has no executable authorization endpoint. Implemented authority currently lives in QMS (`agents-os`). Slice B v0.3 assumed a callable Core endpoint that does not exist. H1 cannot be tested until a **new agent-authenticated QMS decision endpoint** exists and is wired to a material-execution choke point. |
| **H2** | Hypothesis (Core service + thin shim) | **REJECTED as stated** | **Evidence (AAD-56):** Paperclip already has argument-bound signed decisions; QMS `AgentToolGrant` is tool-name-only. Lifecycle authority is **structurally duplicated** between Paperclip backend (heartbeat, checkout, run state) and proposed QMS/Core boundary. Thin shim cannot be assumed without resolving duplicate ownership. A revised H2′ (single QMS decision endpoint + Paperclip demoted to projection/transport) remains a future hypothesis, not approved. |
| **H3** | Hypothesis (one principal identity) | **WEAKENED** | **Evidence (AAD-56):** Hermes/Paperclip session-key behavior can become **implicit provider-memory identity** and must not be treated as canonical identity. Cross-channel continuity via session resume is an identity leak risk until governed principal binding is proven. |
| **H4** | Hypothesis (correlated escalation) | **UNKNOWN** | **Evidence (AAD-56):** Capability registry, stable reason-code catalog, `EscalationRecord`, and durable generic wakeup are **missing**. Slice A path is not falsifiable until these artifacts exist or are stubbed with explicit lab-only scope. |

### UNKNOWN implementation facts

| Topic | Open question |
|---|---|
| Executable QMS decision endpoint | Must be **new**, agent-authenticated, distinct from operator Operational API. Does not exist; required for Slice B-0. |
| Argument binding parity | Paperclip signed decisions bind arguments; QMS `AgentToolGrant` does not. Parity mechanism undecided. |
| Material-execution choke point | Must cover **≥3 adapters including `process`**. Location and enforcement mechanism not implemented. |
| Decision credential TTL | Must be **short-lived per-call decision/nonce**, not 48h spawn credential. Current spawn credential model insufficient per AAD-56. |
| Canonical CEO identity model | QMS `AgentProfile` vs session-key-derived identity unresolved. |
| Durable memory storage contract | Governed documents/conversation bindings vs Hermes-local/session-key state. |
| Capability registry & reason codes | Required for H4; missing. |
| EscalationRecord & durable generic wakeup | Required for H4; missing. |
| Lifecycle owner assignment | Structurally duplicated today; see authority/lifecycle matrix. |
| Unmanaged direct MCP/host execution | **Out-of-scope gap** for current experiment — not a passing control (see Slice B scope). |

### REJECTED alternatives

| Alternative | Reason |
|---|---|
| Paperclip backend as co-equal authority with QMS/Core (target) | **REJECT** under ADR-0060. |
| Treating `agents-os-core` library as executable runtime authority | **REJECT** per AAD-56 — no authorization endpoint exists. |
| H2 as stated (Core sidecar + thin shim without resolving duplication) | **REJECT** per AAD-56 — structural lifecycle duplication and grant/binding mismatch. |
| Hermes/session-key as canonical identity or memory authority | **REJECT / WEAKENED** — implicit provider-memory identity risk. |
| 48h spawn credential as per-call authorization | **REJECT** per AAD-56 — decisions must be short-lived with nonce replay protection. |
| Slice B1–B10 as H1/H2 evidence before Slice B-0 | **REJECT** per AAD-56 — prerequisites block interpretation. |
| Unmanaged MCP/host bypass as in-scope passing control | **REJECT as in-scope** — documented **out-of-scope gap**; cannot pass Slice B by marking N/A. |
| Silent supersession of ADR-0060 | **REJECT.** Normative conflict remains explicit. |
| Architecture approval before falsification evidence | **REJECT.** Status remains NOT APPROVED. |

---

## What changed after Devin (AAD-56)

Independent falsification review of v0.3 against repository and QMS implementation evidence:

1. **H1 downgraded to UNKNOWN/untestable.** v0.3 assumed `POST /v1/authorize/execution` on Core; no such executable endpoint exists in `agents-os-core`. Authority is in QMS (`agents-os`).
2. **H2 rejected as stated.** Paperclip already enforces argument-bound signed decisions; QMS grants are tool-name-only. Lifecycle ownership is duplicated — not a thin-shim insert problem alone.
3. **H3 weakened.** Session-key resume across Hermes/Paperclip heartbeats risks implicit provider-memory identity.
4. **H4 downgraded to UNKNOWN.** Missing capability registry, reason-code catalog, EscalationRecord, durable generic wakeup.
5. **Slice B insufficient without B-0.** Four blocking preconditions must pass first (see below).
6. **Unmanaged MCP/host execution is an out-of-scope gap**, not a negative control that can pass by enumeration/N/A.

Prior review conclusions retained:

- **AAD-52:** ADR-0060 conflict; double-governance warning.
- **AAD-55:** Withhold approval; Slice B before Slice A; negative controls; proposed contract shape.

---

## Revised responsibility split

### Paperclip frontend

Presentation/operator surface. May project QMS state. Must not independently own lifecycle, gates, cost, locks, or durable wakeups while ADR-0060 remains accepted.

### Paperclip backend (lab comparator)

Experimental/reference implementation. **Already exercises argument-bound signed decisions and owns heartbeat/task/run lifecycle in the lab.** Used for falsification harness and comparator evidence only — not canonical authority under ADR-0060. **Conflict:** existing Paperclip authority vs proposed single-authority QMS governance is unresolved.

### `agents-os-core` (library)

Specification/library boundary. **Not** executable authorization authority today. Do not cite as runtime endpoint owner without new implementation.

### `agents-os` (QMS — implemented authority)

Current implemented governance: identity profiles, Human Gates, `AgentToolGrant` (tool-name-only). Target location for **new agent-authenticated decision endpoint** (proposed below). Distinct from operator Operational API.

### Hermes

Replaceable cognitive/runtime provider. Session-key/resume behavior is **provider-local state** — must not be treated as canonical identity (H3 weakened).

### OpenWebUI

Conversational channel. Must bind to governed principal identity, not session-key-derived continuity alone.

### Linear

Operational SSoT for engineering escalations when H4 infrastructure exists.

### Tools / MCP

Material execution surface. Managed paths must pass QMS decision choke point. **Unmanaged direct MCP/host execution is an out-of-scope gap** for this experiment.

---

## Authority and lifecycle matrix

Legend: **QMS** = implemented `agents-os` authority; **Paperclip** = Paperclip backend (lab); **Hermes** = provider adapter; **OPEN** = unassigned or structurally duplicated; **CONFLICT** = competing owners per AAD-56.

| Lifecycle concern | QMS (`agents-os`) | Paperclip frontend | Paperclip backend (lab) | Hermes | OpenWebUI | Linear | Tools/MCP |
|---|---|---|---|---|---|---|---|
| Scheduling / wakeup trigger | OPEN | N/A | **Paperclip** | N/A | N/A | N/A | N/A |
| Work/run creation | OPEN | N/A | **Paperclip** | N/A | N/A | N/A | N/A |
| Pre-execution authorization | **CONFLICT** (grants tool-name-only) | N/A | **Paperclip** (signed arg-bound decisions) | N/A | N/A | N/A | N/A |
| Material execution choke point | OPEN (needs B-0.3) | N/A | Partial (lab) | Adapter entry | N/A | N/A | Managed only |
| Execution lock / single-flight | OPEN | N/A | **Paperclip** | N/A | N/A | N/A | N/A |
| Retry / duplicate heartbeat | OPEN | N/A | **Paperclip** | **Hermes** (session resume) | N/A | N/A | N/A |
| Cancellation | OPEN | N/A | **Paperclip** | **Hermes** | N/A | N/A | N/A |
| Completion / terminal state | OPEN | N/A | **Paperclip** | **Hermes** | N/A | N/A | N/A |
| Human Gate / acceptance | **QMS** | Projection | Non-authoritative projection | N/A | N/A | N/A | N/A |
| Escalation record | OPEN (missing EscalationRecord) | N/A | OPEN | N/A | N/A | **Linear** | N/A |
| Durable identity | **QMS** (target) | N/A | **CONFLICT** (session keys) | **CONFLICT** (session resume) | Binding only | N/A | N/A |
| Correlation ID issuance | **QMS** (target: reconstructible) | N/A | **Paperclip** (run/task ids) | N/A | OPEN | **Linear** | N/A |

**AAD-56 finding:** lifecycle authority is structurally duplicated today. Slice B-0 and Devin PASS/FAIL thresholds require convergence to **one owner per transition** with **QMS-only reconstructible correlation**.

---

## Proposed QMS agent authorization contract (not implemented)

**Status:** **PROPOSED ONLY.** This is not a claim that any endpoint exists. v0.3 incorrectly read as fictional implementation of `POST /v1/authorize/execution` on Core.

### Concrete candidate endpoint (NEW — does not exist today)

| Property | Value |
|---|---|
| **Owner** | QMS (`agents-os`) — implemented governance codebase |
| **Authentication** | **Agent-authenticated** (agent API key / agent identity) |
| **Distinct from** | Operator **Operational API** (human/board operator context) |
| **Purpose** | Per-call material execution authorization with argument binding and nonce |
| **Working name** | `POST /api/agent/v1/decisions/authorize` (proposed; path TBD in QMS repo) |
| **Not** | `agents-os-core` library internal call without HTTP/RPC surface; not Paperclip backend approval routes |

### Proposed request fields (`qms-agent-decision/0.1`)

| Field | Required | Purpose |
|---|---|---|
| `contractVersion` | yes | e.g. `"qms-agent-decision/0.1"`. |
| `requestId` | yes | Unique authorization attempt id (UUID). |
| `decisionNonce` | yes | Single-use nonce for exactly-once material execution. |
| `issuedAt` / `expiresAt` | yes | **Short TTL** (seconds/minutes per call — **not** 48h spawn credential). |
| `qmsVersion` / `policyVersion` | yes | Running QMS and policy bundle versions. |
| `agentId` / `principalId` | yes | Canonical agent identity (QMS `AgentProfile` target). |
| `capabilityKey` | yes | Stable capability key from registry (registry itself missing — H4 UNKNOWN). |
| `adapterType` | yes | e.g. `hermes`, `hermes_gateway`, `process`. |
| `workContext` | yes | `companyId`, `taskId`, `runId`, material action descriptor. |
| `argumentBinding` | yes | Cryptographic/canonical hash over exact tool parameters and context. |
| `evidenceRefs` | no | If policy requires. |

### Proposed response fields

| Field | Required | Purpose |
|---|---|---|
| `decisionId` | yes | Immutable decision id; **QMS-only reconstructible** correlation anchor. |
| `requestId` / `decisionNonce` | yes | Echo for verification. |
| `outcome` | yes | `ALLOW`, `DENY`, `ESCALATION_REQUIRED`, `FAIL_CLOSED`. |
| `reasonCode` | yes | From stable catalog (catalog missing — H4 UNKNOWN). |
| `argumentBinding` | yes | Echo; choke point verifies unchanged arguments. |
| `expiresAt` | yes | Decision TTL. |
| `gateRef` | no | When escalation/gate pending. |

### Fail-closed semantics (proposed)

| Condition | Required behavior |
|---|---|
| QMS unreachable | No material execution; `FAIL_CLOSED`. |
| QMS outage with already-issued credential | **No new material actions** even if prior spawn credential valid. |
| Expired decision | Deny; no execution. |
| Reused `decisionNonce` | Replay rejection; at most one material execution. |
| `argumentBinding` mismatch | Deny; no execution. |
| Stale/revoked gate | Deny; no execution. |

---

## Slice B-0 — Prerequisites (blocking)

**Slice B cases B1–B10 cannot be interpreted as evidence for H1 or H2 until all B-0 gates pass.** Documentation/test-plan only; implementation is a follow-on lab task in QMS + Paperclip lab harness.

| Gate | Prerequisite | Pass evidence | Fail implication |
|---|---|---|---|
| **B-0.1** | **Agent-authenticated QMS decision endpoint** exists and is callable by lab agent identity | Successful authenticated request/response against QMS (not Operational API, not `agents-os-core` fiction) | H1 remains UNKNOWN; Slice B blocked |
| **B-0.2** | **Argument binding** on decisions matches or exceeds Paperclip signed-decision binding; QMS grant/tool-name-only path demoted or wrapped | Deny/allow reflects bound arguments, not tool name alone | H2 remains rejected; Slice B blocked |
| **B-0.3** | **Material-execution choke point** enforced across **≥3 adapters including `process`** | All adapters refuse material action without valid QMS `decisionId` + `argumentBinding` + fresh nonce | Bypass resistance untestable |
| **B-0.4** | **Short-lived per-call decision/nonce** replaces 48h spawn credential for material authorization | TTL measured in call scope; replay of nonce fails; spawn credential cannot authorize material action alone | Replay/TTL tests invalid |

---

## Slice B — Executable falsification plan (after B-0)

**Objective:** After B-0, prove QMS-governed material execution cannot be bypassed and lifecycle ownership converges toward single-authority semantics.

**Scope:** Documentation/test-plan only. Lab harness implementation is out of scope for this PR.

### Out-of-scope gap (not a passing control)

**Unmanaged direct MCP/host execution** — direct tool invocation on host or via unmanaged MCP servers outside the governed choke point — is an **out-of-scope gap**. It cannot be marked N/A to pass Slice B. The lab report must document the gap, affected surface, and risk acceptance by Direction. **B9 from v0.3 is removed as an in-scope negative control.**

In-scope managed paths: adapters in the B-0.3 set (including `process`) and MCP/tools reached only through governed adapter choke points.

### Required correlation IDs and evidence

| ID | Source | Required |
|---|---|---|
| `decisionId` | QMS decision response | yes — **QMS-only reconstructible** |
| `requestId` / `decisionNonce` | QMS decision request | yes |
| `runId` / `taskId` | Paperclip lab (transport only) | yes |
| `agentId` / `principalId` | QMS | yes |
| `argumentBinding` | QMS + choke point verification | yes |
| `adapterType` | Adapter under test | yes |
| `qmsVersion` / `policyVersion` | QMS | yes |
| `reasonCode` | QMS stable catalog (when exists) | yes |

Paperclip-issued ids alone are insufficient for correlation proof; QMS must be able to reconstruct the authorization chain from `decisionId`.

### Test matrix (B0–B10, in-scope paths only)

| Case | Setup | Action | Expected outcome |
|---|---|---|---|
| **B0 — Positive path** | B-0 passed; capability allowed | Heartbeat → QMS ALLOW → single material execution via adapter | One authorized execution; full QMS correlation |
| **B1 — Denied action** | Policy denies capability | Same as B0 | QMS `DENY`; **deny-before-tool**; zero material effects |
| **B2 — Alternate adapter bypass** | B1 denial on adapter A | Same action via adapters B, C (≥3 including `process`) | Zero unauthorized material actions across all adapters |
| **B3 — Managed tool/MCP bypass** | B1 denial | Invoke managed tool path without fresh ALLOW | No material effect without valid decision |
| **B4 — QMS timeout / outage** | QMS unreachable | Heartbeat + execution attempt | Fail-closed; no material execution |
| **B4b — Outage with stale credential** | Valid prior spawn/decision credential | QMS outage during new material attempt | **No material action** despite prior credential |
| **B5 — Replay** | Prior ALLOW consumed | Reuse `decisionNonce` | Replay rejection; ≤1 execution |
| **B6 — Argument mutation** | ALLOW for args P | Execute with P′ | Binding rejection; no execution |
| **B7 — TTL expiry** | ALLOW near expiry | Execute after `expiresAt` | Deny; no execution |
| **B8 — Stale/revoked gate** | Gate revoked after ALLOW | Execute citing stale `gateRef` | Deny; no execution |
| **B9 — Duplicate heartbeat** | First heartbeat completes or in flight | Second heartbeat same task/run | **Exactly-once** material execution by `decisionNonce`; one lifecycle owner |
| **B10 — Lifecycle owner audit** | Any B0–B9 | Trace all transitions | **One owner per transition**; QMS reconstructible correlation |

---

## Devin PASS/FAIL thresholds (AAD-56)

Slice B **PASSES** only if all thresholds below are met on in-scope paths after B-0 passes. Any failure keeps architecture **NOT APPROVED**.

| # | Threshold | PASS | FAIL |
|---|---|---|---|
| 1 | Unauthorized material actions across **≥3 adapters including `process`** | **Zero** unauthorized material actions | ≥1 unauthorized material action on any in-scope adapter |
| 2 | Deny-before-tool | Tool/MCP/process invocation never precedes QMS ALLOW on denied capability | Material effect before or despite DENY |
| 3 | Argument mutation rejection | P′ after ALLOW(P) blocked | Execution with mutated arguments |
| 4 | Replay rejection | Reused `decisionNonce` blocked | Second material execution from same nonce |
| 5 | TTL expiry | Post-expiry execution blocked | Material action after decision TTL |
| 6 | Stale/revoked gate | Revoked/expired gate blocks execution | Execution despite stale/revoked gate |
| 7 | QMS outage fail-closed | No new material actions during outage, including with already-issued credentials | Material action during outage or via stale credential |
| 8 | Duplicate heartbeat exactly-once | At most one material execution per logical work unit via nonce | Duplicate material effects from retry/duplicate heartbeat |
| 9 | One owner per lifecycle transition | Single authoritative owner per transition in audit | Conflicting writers on same transition |
| 10 | QMS-only reconstructible correlation | Full chain reconstructible from QMS `decisionId` | Correlation requires Paperclip-only ids or session keys |

### Falsification mapping (post B-0)

| Target | Falsified / weakened when |
|---|---|
| **H1** (revised, if B-0 enables test) | Thresholds 1–10 fail, or bypass on in-scope adapters |
| **H2′** (hypothetical future) | Threshold 9 or 10 fail — duplication persists |
| **ADR-0060** | Paperclip backend required for correct authorization beyond lab transport |
| **H3** | Session-key/resume used as correlation or identity proof (threshold 10) |
| **H4** | Not testable in Slice B; remains UNKNOWN until registry/EscalationRecord exist |

**Architecture approval remains NOT APPROVED if:** B-0 not passed, any Devin threshold FAIL, or unmanaged MCP/host gap not documented with explicit risk acceptance.

### Pass criteria to proceed toward Slice A

1. All B-0 gates pass with written evidence.
2. All Devin PASS thresholds met on in-scope paths.
3. Unmanaged MCP/host gap documented (not treated as pass).
4. Lifecycle matrix **CONFLICT** rows resolved or explicitly risk-accepted by Direction.
5. Written lab report: QMS-reconstructible correlation from `decisionId` for every case.

---

## Slice A — Deferred (H4 UNKNOWN)

**Status:** Deferred until Slice B pass criteria met **and** H4 prerequisites exist (capability registry, reason-code catalog, EscalationRecord, durable generic wakeup).

Shopify operator escalation scenario from v0.3 remains documented but is **not falsifiable** today.

---

## Approval invariant (target vs current conflict)

**Target:** one semantic authorization decision; QMS Human Gate authoritative; Paperclip projects only.

**Current conflict (AAD-56, preserved):** Paperclip backend already issues argument-bound signed decisions and owns lifecycle transitions. QMS `AgentToolGrant` is tool-name-only. This is structural double governance — not resolved by documentation alone.

---

## Explicit disagreements retained

1. **ADR-0060 vs project intent:** Paperclip as organizational base vs backend excluded from target runtime.
2. **Paperclip authority vs single-authority target:** Existing Paperclip signed decisions vs proposed QMS-only semantic authority.
3. **`agents-os-core` vs QMS:** Library is not executable authority; do not conflate names.
4. **H2 rejected as stated:** Thin Core shim insufficient given duplication and binding mismatch.
5. **H3 weakened:** Session-key/resume is implicit identity risk, not canonical principal.
6. **H4 UNKNOWN:** Missing escalation infrastructure.
7. **Unmanaged MCP/host gap:** Out of scope — experiment does not prove host-level containment.
8. **Hermes adapter existence vs governance:** Adapters exist in fork; governance completeness open.

---

## AAD-57 — Slice B-0 engineering (rework in progress)

**Status:** agents-os PR #263 mint/consume **verified**; spawn/MCP gaps + docs **addressed in Paperclip rework bundle.** Architecture remains **NOT APPROVED.**

| Artifact | Location |
|---|---|
| Implementation plan | `doc/agents-os/AAD-57-SLICE-B0-IMPLEMENTATION-PLAN.md` |
| Original patch bundle (superseded) | `doc/agents-os/aad-57-slice-b0/` |
| **Rework patch bundle** | `doc/agents-os/aad-57-slice-b0-rework/` |
| Unmanaged path inventory | `doc/agents-os/AAD-57-UNMANAGED-PATH-INVENTORY.md` |
| Lifecycle demotion matrix | `doc/agents-os/AAD-57-LIFECYCLE-DEMOTION-MATRIX.md` |
| Slice B-1 harness plan | `doc/agents-os/AAD-57-SLICE-B1-HARNESS-PLAN.md` |
| QMS implementation PR | https://github.com/aavendano/agents-os/pull/263 |
| QMS tracking issue | https://github.com/aavendano/agents-os/issues/257 |

**Verified in agents-os PR #263 (head `93caa0c`):**

1. `POST /api/agent/action-decisions/` — agent-authenticated, distinct from `/api/operational/v1/*`
2. Argument-bound short-TTL decisions with `decision_id`, nonce, replay/TTL enforcement (44+ tests)
3. Workflow provider choke points (`dispatch.py`, verifier, BPMN executor)
4. Capability ≠ Authority (`AgentToolGrant` + `AgentMaterialAuthorityGrant`)

**Open rework (review REWORK_REQUIRED, 2026-08-24):**

1. `work_orders/services.py` — `subprocess.Popen` bypasses decision consume
2. MCP tool execution — capability-only; needs `integrations/mcp/dispatch.py`
3. Docs delivered in Paperclip: unmanaged inventory, demotion matrix, B-1 harness

**B-0 gate status:**

| Gate | Status |
|---|---|
| B-0.1 Agent-authenticated endpoint | **PASS** (PR #263) |
| B-0.2 Argument binding | **PASS** (PR #263) |
| B-0.3 ≥3 adapters incl. `process` | **REWORK** — apply `aad-57-slice-b0-rework/` |
| B-0.4 Short-lived nonce/TTL | **PASS** (PR #263) |

---

## Architecture decision status

| Decision | Status |
|---|---|
| Target architecture (H1–H4 as operational baseline) | **NOT APPROVED** |
| ADR-0060 | **CONTROLLING** |
| H1 as written | **UNKNOWN / untestable** (until B-0 CI evidence) |
| H2 as written | **REJECTED** |
| H3 | **WEAKENED** |
| H4 | **UNKNOWN** |
| Slice B-0 prerequisites | **REWORK** (PR #263 + spawn/MCP patches) |
| Slice B (B0–B10) | **BLOCKED** until B-0 passes |
| Slice A | **DEFERRED** |
| Proposed agent decision contract | **IMPLEMENTED** (PR #263; pending B-0.3 rework) |
| Proposed QMS agent decision endpoint | **IMPLEMENTED** (PR #263) |
| Unmanaged path inventory | **DOCUMENTED** (`AAD-57-UNMANAGED-PATH-INVENTORY.md`) |
| Lifecycle demotion matrix | **DOCUMENTED** (`AAD-57-LIFECYCLE-DEMOTION-MATRIX.md`) |
| Slice B-1 harness plan | **DOCUMENTED** (`AAD-57-SLICE-B1-HARNESS-PLAN.md`) |

---

## Operational references

- Linear project: `Paperclip × Agents-OS Core × Hermes Experiment`
- Research cycle: **AAD-51**
- Cursor adversarial review: **AAD-52** (completed)
- Codex second-pass review: **AAD-53**
- Codex critique with falsification requirements: **AAD-55** (completed; drives v0.3)
- Independent Devin falsification review: **AAD-56** (completed; drives v0.4)
- Slice B-0 engineering task: **AAD-57** (in progress — patch bundle in Paperclip PR)
