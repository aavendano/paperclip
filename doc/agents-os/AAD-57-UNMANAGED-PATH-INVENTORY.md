# AAD-57 — Unmanaged execution path inventory (trust boundary)

**Status:** Required Slice B-0 deliverable. **Architecture NOT APPROVED.** ADR-0060 remains controlling.

**Purpose:** Document every material-execution surface, whether it is governed by QMS per-action authorization (Capability + Authority + consumed ALLOW decision), and explicit gaps that cannot pass Slice B by marking N/A.

**Evidence baseline:** agents-os PR #263 (`cursor/aad-57-slice-b0-c417`, head `93caa0c`) + independent review verdict **REWORK_REQUIRED** (2026-08-24).

---

## Trust boundary definition

**In-scope (managed):** Any path that can cause material effects — subprocess spawn, shell invocation, filesystem mutation, outbound network, MCP/tool dispatch — and is reachable through QMS workflow orchestration or QMS-owned spawn/MCP entry points.

**Governed choke-point contract (B-0 target):**

1. Agent mints ALLOW via `POST /api/agent/action-decisions/` with bound `scope`, `action`, `arguments`, `nonce`.
2. Execution caller supplies per-dispatch credential (`__agent_action_credentials[normalized_action]` or scalar fallback).
3. Choke point calls `consume_agent_action_decision` under row lock **before** material effect.
4. Failure modes are fail-closed with auditable `consume_deny` (no nonce in metadata).

**Out-of-scope (unmanaged):** Paths that bypass QMS choke points entirely. These are documented gaps requiring Direction risk acceptance; they do **not** satisfy Slice B PASS thresholds.

---

## Material execution surfaces

| # | Surface | Adapter / owner | PR #263 status | Authority at execution | Unmanaged risk |
|---|---|---|---|---|---|
| 1 | Workflow primary provider (`SequentialRunner`) | `workflows/runner.py` → `workflows/providers/dispatch.py` | **WIRED** | Consumed ALLOW + nonce + scope + arguments hash | Low (when credentials supplied) |
| 2 | Workflow verifier re-invocation | `workflows/verifier.py` → `dispatch.py` | **WIRED** | Same as #1; requires separate per-action credential | Medium (dual-dispatch credential map) |
| 3 | BPMN service-task handler | `workflows/bpmn/executor.py` → `assert_bpmn_service_task_authorized` | **WIRED** | Same; multi-node cycles need per-dispatch credentials | Medium |
| 4 | **Work-order agent subprocess spawn** | `work_orders/services.py` (~478–486 `subprocess.Popen`) | **NOT WIRED** | None — direct Popen | **CRITICAL OPEN** |
| 5 | MCP tool invocation (managed server) | `integrations/mcp/*` handlers | **CAPABILITY ONLY** (`has_agent_tool_grant` at mint; `assert_agent_tool_grant` at some paths) | No consumed ALLOW at tool execution | **HIGH OPEN** |
| 6 | Hermes remote provider session | Hermes Gateway / Hermes adapter (Paperclip lab) | Not in PR #263 | Paperclip signed decisions (lab comparator) | Documented lab path; not QMS canonical |
| 7 | Paperclip `process` adapter (lab) | Paperclip backend adapters | Lab comparator | Paperclip argument-hash approvals | Lab only under ADR-0060 |
| 8 | Operator Operational API mutations | `/api/operational/v1/*` | N/A (human operator) | Operator auth, not agent per-action | Out of agent B-0 scope |
| 9 | Direct host shell / SSH | Host OS, developer workstation | Unmanaged | None | **OUT-OF-SCOPE GAP** |
| 10 | Unmanaged MCP servers (external) | Third-party MCP outside QMS registry | Unmanaged | None | **OUT-OF-SCOPE GAP** |
| 11 | Provider-local Hermes session resume | Hermes session keys | Unmanaged identity scope | Provider memory, not QMS principal | **H3 WEAKENED gap** |

---

## PR #263 wired paths (detail)

### Workflow material dispatch

```
workflows/runner.py
  └─ workflows/providers/dispatch.py::execute_material_provider
       └─ core/agent_decisions/enforcement.py::assert_material_execution_authorized
            └─ consume_agent_action_decision (single-use, nonce required)
```

**Provider types gated:** `python`, `service`, `agent` (see `MATERIAL_PROVIDER_TYPES`).

**Credential transport:** `__agent_action_credentials` map keyed by normalized action (e.g. `python.text.word_stats.python`).

### BPMN service tasks

```
workflows/bpmn/executor.py
  └─ assert_bpmn_service_task_authorized
       └─ consume_agent_action_decision
```

---

## Open rework paths (blocking B-0.3)

### R-1: `work_orders/services.py` subprocess spawn

**Finding:** Independent review confirmed `subprocess.Popen` is reachable without `consume_agent_action_decision`.

**Required fix:** Insert `assert_process_spawn_authorized()` immediately before `subprocess.Popen`. Patch bundle: `doc/agents-os/aad-57-slice-b0-rework/work_orders_spawn_gate.py`.

**Normalized action:** `process.agent` (or domain-specific key aligned with `AgentMaterialAuthorityGrant`).

**Mint-time arguments must bind:** `command` (argv list), `cwd`, `env` subset, `work_order_id`, `run_id`.

### R-2: MCP tool execution

**Finding:** PR #263 refactored `integrations/mcp/authz.py` to expose `has_agent_tool_grant` for **mint-time capability** checks only. Tool dispatch still lacks Authority consumption.

**Required fix:** Route all managed MCP tool calls through `integrations/mcp/dispatch.py::execute_mcp_tool_authorized`. Patch bundle: `doc/agents-os/aad-57-slice-b0-rework/integrations/mcp/dispatch.py`.

**Normalized action:** `mcp.{tool_name}` (must match grant + authority rows).

---

## Explicitly unmanaged paths (documented gaps)

These paths **cannot** be marked N/A to pass Slice B. The lab report must document them and obtain Direction risk acceptance.

| Gap ID | Description | Affected hypothesis | Mitigation (future) |
|---|---|---|---|
| G-1 | Direct host shell outside QMS | H1, threshold #1 | OS-level sandbox / separate experiment |
| G-2 | Unregistered external MCP servers | H1, threshold #1 | MCP registry + gateway-only routing |
| G-3 | Hermes session-key identity continuity | H3, threshold #10 | Governed principal binding; no session-key correlation |
| G-4 | Paperclip backend lifecycle during outage | H2, threshold #9 | Lifecycle demotion matrix + single owner |
| G-5 | 48h spawn JWT used as material credential | B-0.4 | Already rejected; spawn JWT ≠ per-action decision |

---

## B-0.3 adapter coverage tracker

Slice B-0 requires **≥3 adapters including `process`** with end-to-end decision correlation.

| Adapter | Normalized action prefix | Choke point | B-0.3 status |
|---|---|---|---|
| `python` provider | `python.{key}` | `dispatch.py` | **PASS** (PR #263) |
| `service` provider / BPMN | `service.{key}` | `dispatch.py` / BPMN executor | **PASS** (PR #263) |
| `agent` provider | `agent.{key}` | `dispatch.py` | **PASS** (PR #263) |
| **`process` spawn** | `process.agent` | `work_orders/services.py` | **FAIL — not wired** |
| **MCP managed tools** | `mcp.{tool}` | `integrations/mcp/dispatch.py` | **FAIL — capability only** |
| Hermes (lab) | TBD in Paperclip harness | Paperclip adapter | **DEFERRED** to B-1 lab |

**B-0.3 gate:** Cannot pass until rows marked FAIL are wired and covered by tests.

---

## Audit correlation requirements

Every managed choke point must emit or participate in:

| Event | When |
|---|---|
| `agent_action_decision.allow` | Mint ALLOW |
| `agent_action_decision.deny` | Mint DENY |
| `agent_action_decision.consume` | Successful single-use consumption |
| `agent_action_decision.consume_deny` | Failed consumption (including missing nonce, replay, binding mismatch) |

QMS must reconstruct the full chain from `decision_id` alone (threshold #10).

---

## References

- Linear AAD-57, agents-os#257, agents-os PR #263
- Architecture Proposal v0.4 (`doc/agents-os/ARCHITECTURE-PROPOSAL-v0.1.md`)
- Rework patch bundle: `doc/agents-os/aad-57-slice-b0-rework/`
