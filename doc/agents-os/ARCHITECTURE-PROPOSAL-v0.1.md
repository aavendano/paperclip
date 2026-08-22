# Architecture Proposal v0.3 — Paperclip × Agents-OS Core × Hermes

**Status:** **NOT APPROVED.** Revised after Cursor adversarial review (AAD-52) and Codex second-pass critique (AAD-55). Architecture approval is withheld pending Slice B falsification evidence. **ADR-0060 remains controlling** until Direction or a formal ADR supersedes it.

**Experiment order:** Run **Slice B before Slice A.** Slice A remains documented but is deferred until Slice B produces pass/fail evidence for H1, H2, and ADR-0060 compatibility.

---

## Document classification

This proposal separates normative claims from hypotheses and open implementation facts.

### SUPPORTED requirements

| Requirement | Notes |
|---|---|
| Paperclip frontend as organization/operator UX | Presentation for hierarchy, work state, approvals, activity. May project Core/QMS state. |
| Core as canonical governance/runtime boundary | Identity, capability/authority evaluation, policy, Human Gates, evidence requirements, governed execution authorization. Versioned interfaces; not source-editable by operational agents. |
| One semantic authorization decision | Core/QMS Human Gate is authoritative. Paperclip may project/submit; separate Paperclip approval records must be non-authoritative, reconstructible, or absent in target runtime. |
| Hermes as replaceable cognitive/runtime provider | Experimental provider only; not canonical principal or memory authority. |
| Linear as engineering SSoT for missing-capability work | Tracks implementation status; not user-memory or business-domain SSoT. |
| Paperclip backend as lab comparator | Adapters, heartbeat code, approval models, MCP gateway, Hermes integration are implementation evidence for isolated falsification tests only. |
| Fail-closed authorization on Core outage | If Core cannot decide synchronously within bounds, material execution must not proceed. |
| Correlated escalation minimum fields | principal/actor id, conversation id, originating work/request id, capability key, evidence/reference ids, Linear issue id, escalation status, implementation/project reference if approved. |
| Slice B negative controls | Denied action, alternate adapter/direct-tool bypass, Core timeout, replay/changed arguments, duplicate heartbeat/retry, stale/revoked gate, unmanaged MCP (if applicable), one lifecycle owner per transition. |

### Hypotheses (not approved)

| ID | Hypothesis | Falsification trigger |
|---|---|---|
| **H1** | Canonical governance path is `Paperclip/OpenWebUI presentation → Core application/operational boundary → governed work/execution → provider adapter (Hermes or other) → tool`. Paperclip backend is not canonical while ADR-0060 stands. | Pre-execution Core authorization can be bypassed, duplicated, or lifecycle authority splits across Paperclip and Core. |
| **H2** | Core runs as versioned service/sidecar with thin adapter/shim at execution entry points. Shim transports identity, requested capability, work context, evidence requirements; does not implement policy independently. | Safe synchronous authorization cannot be inserted without duplicating lifecycle/locks or unacceptable coupling. |
| **H3** | One principal/CEO identity independent of Hermes, Paperclip, OpenWebUI. Memory classes: (1) governed durable facts/decisions, (2) conversation history/bindings, (3) task/run context, (4) provider-local transient state. Only governed scopes provide cross-channel continuity by default. | Deterministic capability detection, correlation, or round-trip status fails in Slice A. |
| **H4** | Missing capability escalates via correlated path: `user_need → capability evaluation → CAPABILITY_UNAVAILABLE/ESCALATION_REQUIRED → EscalationRecord → Linear issue → engineering decision/status → user-visible status update`. | Correlation or round-trip status fails in Slice A. |

### UNKNOWN implementation facts

| Topic | Open question |
|---|---|
| Canonical CEO identity model | Cursor recommends QMS `AgentProfile`; `agents-os-core` identity model requires direct verification. |
| Durable memory storage contract | Governed documents/conversation bindings are stronger than Hermes-local state; concrete storage location undecided. |
| Hermes adapter governance completeness | This fork contains `packages/adapters/hermes` and `packages/adapters/hermes-gateway` plus join/smoke/E2E scripts. Open question is whether they satisfy the governed principal-agent contract, not whether integration exists. |
| Core service deployment shape | Sidecar vs remote service vs embedded boundary for lab experiment. |
| Paperclip approval projection semantics | How non-authoritative projection is enforced in target runtime vs lab comparator. |
| Unmanaged MCP exposure surface | Whether unmanaged MCP endpoints exist in lab setup and how they are enumerated for Slice B. |
| Lifecycle owner assignment | See authority/lifecycle matrix — most transitions remain **OPEN** pending Slice B evidence. |

### REJECTED alternatives

| Alternative | Reason |
|---|---|
| Paperclip backend as co-equal authority with Core | **REJECT** under current ADR-0060. |
| Hermes as canonical CEO identity/memory authority | **REJECT.** Provider-local state cannot define durable identity, authority, or canonical memory. |
| Dual semantic authorization (Paperclip approval + Core gate both authoritative) | **REJECT** under current baseline. Creates double-governance risk across approvals, task/run lifecycle, wakeups, and gates. |
| Proceeding to Slice A or target-runtime promotion before Slice B evidence | **REJECT** per AAD-55. Architecture approval withheld until Slice B completes. |
| Silent supersession of ADR-0060 by this proposal | **REJECT.** Normative conflict with project intent (Paperclip as organizational base) remains explicit and unresolved. |

---

## What changed after Codex (AAD-55)

Codex reviewed v0.2 plus Cursor AAD-52 findings and repository evidence. Material conclusions:

1. **Withhold architecture approval.** This document is a falsification plan, not an approved target architecture.
2. **Keep ADR-0060 controlling.** Paperclip backend remains lab comparator; promotion requires explicit superseding decision.
3. **Run Slice B before Slice A.** Governance insertion and bypass resistance must be proven on the existing Hermes/Hermes Gateway adapter path before broader capability-escalation experiments.
4. **Require negative controls.** Positive-path-only tests are insufficient; Slice B must include denied action, bypass attempts, timeout/outage, replay/tamper, duplicate retry, stale gate, unmanaged MCP, and single lifecycle owner per transition.
5. **Define minimum Core authorization contract.** Experiment needs versioned request/response with input binding, expiry/replay protection, fail-closed outage semantics, policy/Core version, and decision ID.
6. **Assign or mark lifecycle ownership open.** Double-governance risk across scheduling, wakeups, locks, retries, cancellation, completion, and acceptance must be explicit.

Cursor AAD-52 findings retained:

- Material conflict with ADR-0060 when v0.1 treated Paperclip backend as active organizational control plane.
- High double-governance risk across Paperclip approvals, task/run lifecycle, wakeups, and Core/QMS Gates.
- One Cursor claim disputed: Hermes integration exists in this fork; governance completeness remains open.

---

## Revised responsibility split

### Paperclip frontend

Presentation/operator surface. May project Core/QMS state. Must not independently own lifecycle, gates, cost, locks, or durable wakeups while ADR-0060 remains accepted.

### Paperclip backend

Experimental/reference implementation and **lab comparator only.** Its adapters, heartbeat orchestration, approval models, MCP gateway, and Hermes integration may be exercised in isolated falsification tests. Not canonical authority.

### Agents-OS Core

Canonical governance/runtime boundary for identity, capability/authority evaluation, policy, Human Gates, evidence requirements, and governed execution authorization. Exposes versioned interfaces. Not source-editable by operational agents.

### Hermes

Replaceable cognitive/runtime provider for the principal-agent experiment. Hermes-local state cannot define durable identity, authority, or canonical memory.

### OpenWebUI

Conversational channel bound to the same canonical principal identity and governed durable memory namespace.

### Linear

Operational SSoT for engineering escalations and implementation status generated by missing capabilities.

### Tools / MCP

Execution surface reached only after Core authorization. Unmanaged or out-of-band tool paths are in scope for Slice B bypass tests.

---

## Authority and lifecycle matrix

Legend: **Core** = assigned to Agents-OS Core/QMS; **Paperclip** = Paperclip backend (lab comparator); **Hermes** = provider adapter/runtime; **OPEN** = owner not yet assigned or proven; **N/A** = not applicable in current experiment scope.

| Lifecycle concern | Core | Paperclip frontend | Paperclip backend (lab) | Hermes | OpenWebUI | Linear | Tools/MCP |
|---|---|---|---|---|---|---|---|
| Scheduling / wakeup trigger | OPEN | N/A | **Paperclip** (heartbeat scheduler in lab) | N/A | N/A | N/A | N/A |
| Work/run creation | OPEN | N/A | **Paperclip** (task/run records in lab) | N/A | N/A | N/A | N/A |
| Pre-execution authorization | **Core** | N/A | Shim insertion point (lab) | N/A | N/A | N/A | N/A |
| Execution lock / single-flight | OPEN | N/A | **Paperclip** (checkout semantics in lab) | N/A | N/A | N/A | N/A |
| Retry / duplicate heartbeat | OPEN | N/A | **Paperclip** (lab behavior under test) | **Hermes** (session resume) | N/A | N/A | N/A |
| Cancellation | OPEN | N/A | **Paperclip** (lab) | **Hermes** (process kill) | N/A | N/A | N/A |
| Completion / run terminal state | OPEN | N/A | **Paperclip** (lab) | **Hermes** (adapter exit) | N/A | N/A | N/A |
| Acceptance / Human Gate decision | **Core** | Projection only | Non-authoritative projection (lab) | N/A | N/A | N/A | N/A |
| Escalation record creation | **Core** (eval) | N/A | OPEN (lab may mirror) | N/A | N/A | **Linear** (issue state) | N/A |
| Cost / budget enforcement | OPEN | N/A | **Paperclip** (lab) | N/A | N/A | N/A | N/A |
| Durable identity | **Core** | N/A | OPEN | REJECT as authority | Binding only | N/A | N/A |
| Canonical memory write | **Core** / governed store | N/A | OPEN | REJECT as authority | OPEN | N/A | N/A |
| Correlation ID issuance | **Core** (auth decision) | N/A | **Paperclip** (run/task ids in lab) | N/A | OPEN | **Linear** (issue id) | N/A |

**Slice B must prove or falsify:** for each material transition (wakeup → auth request → auth decision → execution → completion), exactly one lifecycle owner is authoritative and no alternate path can mutate state without Core authorization.

---

## Minimum Core authorization contract (experiment v0.1)

This is the minimum versioned contract required for Slice B. It is an experiment contract, not a production API commitment.

### Request — `POST /v1/authorize/execution`

| Field | Required | Purpose |
|---|---|---|
| `contractVersion` | yes | Contract version, e.g. `"core-authz/0.1"`. |
| `requestId` | yes | Unique id for this authorization attempt (UUID). |
| `issuedAt` | yes | ISO-8601 timestamp. |
| `expiresAt` | yes | Short TTL; stale requests must fail closed. |
| `coreVersion` | yes | Running Core/QMS version string. |
| `policyVersion` | yes | Policy bundle version used for evaluation. |
| `principalId` | yes | Canonical actor/principal id. |
| `capabilityKey` | yes | Requested capability/action key. |
| `workContext` | yes | Bound execution context (see below). |
| `evidenceRefs` | no | Required evidence artifact ids, if policy demands. |
| `channel` | yes | Origin channel: `paperclip`, `openwebui`, `adapter`, etc. |
| `nonce` | yes | Replay protection nonce; Core must reject reuse within TTL window. |
| `inputBinding` | yes | Cryptographic or canonical hash binding request to exact inputs (see below). |

**`workContext` minimum fields:**

- `companyId`
- `taskId` or `workItemId`
- `runId` (heartbeat run id)
- `adapterType` (e.g. `hermes`, `hermes_gateway`)
- `requestedTool` or `materialAction` descriptor (stable key + parameter schema hash)

**`inputBinding`:** hash over canonical JSON of `{ principalId, capabilityKey, workContext, requestedToolParams, policyVersion, expiresAt, nonce }`. Execution shim must recompute and compare before invoking material action. Changed arguments after authorization must fail closed.

### Response

| Field | Required | Purpose |
|---|---|---|
| `contractVersion` | yes | Echo or response contract version. |
| `decisionId` | yes | Immutable id for this authorization decision; cite in all downstream logs. |
| `requestId` | yes | Echo request id. |
| `outcome` | yes | `ALLOW`, `DENY`, `ESCALATION_REQUIRED`, or `FAIL_CLOSED`. |
| `reasonCode` | yes | Stable machine reason, e.g. `CAPABILITY_UNAVAILABLE`, `POLICY_DENY`, `GATE_PENDING`, `CORE_TIMEOUT`, `REPLAY_DETECTED`, `BINDING_MISMATCH`. |
| `coreVersion` | yes | Core version that issued decision. |
| `policyVersion` | yes | Policy version evaluated. |
| `expiresAt` | yes | Decision expiry; re-authorization required after. |
| `inputBinding` | yes | Echo binding; shim verifies unchanged inputs. |
| `gateRef` | no | Human Gate reference when `ESCALATION_REQUIRED` or pending gate. |
| `obligations` | no | Post-conditions, logging, evidence upload requirements. |

### Fail-closed outage semantics

| Condition | Required behavior |
|---|---|
| Core unreachable | No material execution. Outcome logged as `FAIL_CLOSED` / `CORE_TIMEOUT`. |
| Response after `expiresAt` | Treat as denial; no execution. |
| Reused `nonce` or `requestId` within TTL | `REPLAY_DETECTED`; no execution. |
| `inputBinding` mismatch at shim | `BINDING_MISMATCH`; no execution. |
| `DENY` or `ESCALATION_REQUIRED` without approved gate | No material execution. |
| Stale or revoked gate used | `GATE_REVOKED` or `GATE_STALE`; no execution. |

---

## Slice B — Executable falsification plan (Paperclip/Hermes governance comparator)

**Objective:** Insert Core pre-execution authorization before material execution on the existing Hermes / Hermes Gateway adapter path with one heartbeat-triggered task. Prove that denied capability cannot bypass through another adapter, direct tool, or unmanaged MCP path.

**Scope:** Documentation and test-plan only in this PR. Implementation of shim and harness is a follow-on lab task.

**Prerequisites:**

- Lab Paperclip instance with Hermes or Hermes Gateway adapter configured (`packages/adapters/hermes`, `packages/adapters/hermes-gateway`).
- Core authorization endpoint implementing contract `core-authz/0.1` (may be stubbed for negative controls).
- Observable logging for all paths: heartbeat scheduler, adapter spawn, Core authz call, tool/MCP invocation.
- Correlation ID propagation enforced across components.

### Required correlation IDs and evidence

Every test case must capture:

| ID | Source | Required in evidence |
|---|---|---|
| `requestId` | Core authz request | yes |
| `decisionId` | Core authz response | yes |
| `runId` | Paperclip heartbeat run | yes |
| `taskId` / `workItemId` | Paperclip task | yes |
| `principalId` | Core / agent identity | yes |
| `capabilityKey` | Core evaluation | yes |
| `adapterType` | Adapter under test | yes |
| `policyVersion` / `coreVersion` | Core | yes |
| `gateRef` | When applicable | if escalated |
| `linearIssueId` | When escalated to Linear | if applicable |

Evidence artifacts per case: timestamped log bundle, authz request/response payload, adapter stdout/stderr summary, tool/MCP call trace (or proof of absence), final run/task terminal state.

### Test matrix

| Case | Setup | Action | Expected outcome | Falsifies |
|---|---|---|---|---|
| **B0 — Positive path** | Capability allowed; Core healthy; gate clear if required | Heartbeat triggers task → shim calls Core → ALLOW → adapter executes material action once | Exactly one authorized execution; single lifecycle owner per transition; correlated IDs present end-to-end | N/A (baseline) |
| **B1 — Denied action** | Policy denies `capabilityKey` | Same as B0 | Core returns `DENY`; no material execution; run/task terminal state reflects denial without side effects | H1, H2, ADR-0060 if execution proceeds |
| **B2 — Alternate adapter bypass** | B1 denial on Hermes path | Attempt same material action via different adapter type or direct adapter entry | All paths require Core ALLOW; no orphan execution | H1, H2 |
| **B3 — Direct-tool / MCP bypass** | B1 denial | Invoke tool or MCP directly (managed and unmanaged if present) without fresh ALLOW | No material effect without valid `decisionId` and binding | H1, H2 |
| **B4 — Core timeout / outage** | Core unreachable or exceeds sync bound | Heartbeat triggers task | `FAIL_CLOSED`; no material execution; no partial side effects | H2, fail-closed requirement |
| **B5 — Replay** | Valid ALLOW for case A | Re-submit same `requestId`/`nonce`/binding for second execution | Second attempt `REPLAY_DETECTED`; at most one execution | H1, H2 |
| **B6 — Changed arguments** | Valid ALLOW for params P | Execute with params P' before expiry | Shim rejects `BINDING_MISMATCH`; no execution with P' | H1, H2 |
| **B7 — Duplicate heartbeat / retry** | First heartbeat in flight or completed | Second heartbeat for same task/run without idempotent contract | At most one material execution; no duplicate lifecycle transition owners | H1, H2, lifecycle matrix |
| **B8 — Stale / revoked gate** | Gate was approved then revoked or expired | Attempt execution citing old `gateRef` or expired `decisionId` | `GATE_STALE` / `GATE_REVOKED`; no execution | H1, approval invariant |
| **B9 — Unmanaged MCP (if applicable)** | Enumerate unmanaged MCP endpoints in lab | Attempt material action through unmanaged MCP after denial | No bypass; document surface or confirm N/A | H1 |
| **B10 — Lifecycle owner audit** | Any case B0–B9 | Trace wakeup → auth → execute → complete | Each transition has exactly one authoritative owner; no conflicting state writers | H1, H2, ADR-0060 |

### Explicit falsification conditions

**H1 falsified if:** any case B1–B10 shows material execution or lifecycle mutation without a current Core `ALLOW` and matching `inputBinding`, or Paperclip backend and Core both claim authority over the same transition.

**H2 falsified if:** B4 shows unsafe proceed-on-timeout, or inserting the shim duplicates locks/lifecycle in a way that prevents correct single-flight semantics, or coupling requires policy logic in the shim beyond transport and binding verification.

**ADR-0060 compatibility falsified if:** Paperclip backend behavior is required for correct authorization (not merely used as lab transport), or promotion of Paperclip backend lifecycle/approval semantics into canonical path is implied by test outcomes.

**Architecture approval remains NOT APPROVED if:** any of B1–B10 fails, or B0 cannot demonstrate end-to-end correlation with single lifecycle owner per transition.

### Pass criteria to proceed to Slice A

1. B0 passes with full correlation evidence.
2. B1–B10 pass (or B9 marked N/A with documented enumeration).
3. No unresolved **OPEN** lifecycle owners for transitions on the tested path, or OPEN items documented with explicit risk acceptance by Direction.
4. Written lab report links evidence artifacts to `decisionId` and run/task ids.

---

## Slice A — Deferred capability escalation (after Slice B)

**Status:** Deferred until Slice B pass criteria met.

A non-technical Shopify operator asks in OpenWebUI to change a controlled content item. Core evaluates capability. If write capability is unavailable, the system creates a correlated Linear escalation and returns a user-visible tracking reference. After engineering status changes, the principal can report the current state.

Falsifies H3/H4 if deterministic capability detection, correlation, or round-trip status fails.

Do not start Slice A implementation or treat it as approved while architecture status is NOT APPROVED.

---

## Approval invariant

There must be one semantic authorization decision. Under the current baseline, Core/QMS Human Gate is authoritative. Paperclip may project and submit that decision, but a separate Paperclip approval record must be non-authoritative/reconstructible or absent from the target runtime.

---

## Explicit disagreements retained

1. **ADR-0060 vs project intent:** Current project intent wants Paperclip as the organizational base; ADR-0060 excludes its backend from the target runtime. Normative conflict; not resolved by this revision.
2. **Canonical CEO identity:** Cursor recommends QMS `AgentProfile`; `agents-os-core` identity model still requires verification.
3. **Hermes role:** This project treats Hermes as experimental replaceable runtime, never authority; whether that is an acceptable exception remains open.
4. **Durable memory location:** Governed documents/conversation bindings preferred over Hermes-local state; concrete storage contract unknown.
5. **Hermes adapter existence vs governance:** Cursor claimed no native adapter; this fork contains `hermes` and `hermes-gateway` packages and smoke/E2E tooling. Governance completeness remains the open question.

---

## Architecture decision status

| Decision | Status |
|---|---|
| Target architecture (H1–H4 as operational baseline) | **NOT APPROVED** |
| ADR-0060 (Paperclip presentation yes; backend not canonical authority) | **CONTROLLING** |
| Slice B falsification plan | **APPROVED FOR EXECUTION** (test plan only) |
| Slice A | **DEFERRED** |
| Core authorization contract `core-authz/0.1` | **PROPOSED** for experiment |

---

## Operational references

- Linear project: `Paperclip × Agents-OS Core × Hermes Experiment`
- Research cycle: **AAD-51**
- Cursor adversarial review: **AAD-52** (completed)
- Codex second-pass review: **AAD-53** (review task)
- Codex critique with falsification requirements: **AAD-55** (completed; drives v0.3)
