# AAD-57 — Slice B-0 implementation plan

**Status:** PR #263 mint/consume **PASS**; rework bundle addresses open gaps. **Architecture NOT APPROVED.**

**Architecture remains NOT APPROVED.** ADR-0060 remains controlling. Paperclip backend remains lab comparator.

## Review verdict (2026-08-24)

Independent review of agents-os PR #263 (`cursor/aad-57-slice-b0-c417`, head `93caa0c`):

| Area | Verdict |
|---|---|
| Mint/consume core (endpoint, argument hash, TTL, nonce, row lock) | **PASS** — 44+9 tests |
| Workflow provider choke points | **PASS** |
| `work_orders/services.py` subprocess spawn | **FAIL** — Popen bypasses decision |
| MCP tool execution | **FAIL** — capability-only at execution |
| Unmanaged path inventory | **MISSING** → delivered in this PR |
| Lifecycle demotion matrix | **MISSING** → delivered in this PR |
| Slice B-1 harness/thresholds | **MISSING** → delivered in this PR |

## Deliverables map

| Deliverable | Location | Status |
|---|---|---|
| Callable agent-authenticated endpoint | agents-os PR #263 | **DONE** |
| Argument binding + replay/TTL | agents-os PR #263 | **DONE** |
| Workflow adapter choke points | agents-os PR #263 | **DONE** |
| Process spawn choke point | `aad-57-slice-b0-rework/` | **PATCH READY** |
| MCP authority at execution | `aad-57-slice-b0-rework/` | **PATCH READY** |
| Unmanaged path inventory | `AAD-57-UNMANAGED-PATH-INVENTORY.md` | **DONE** |
| Demotion matrix | `AAD-57-LIFECYCLE-DEMOTION-MATRIX.md` | **DONE** |
| B-1 harness plan | `AAD-57-SLICE-B1-HARNESS-PLAN.md` | **DONE** |

## Original patch bundle (superseded for implementation)

The initial bundle at `doc/agents-os/aad-57-slice-b0/` predates PR #263. **Use PR #263 as the implementation baseline**, then apply rework:

```text
doc/agents-os/aad-57-slice-b0-rework/
```

Tracking: https://github.com/aavendano/agents-os/issues/257, PR https://github.com/aavendano/agents-os/pull/263

## Objective (Linear AAD-57)

1. Callable agent-authenticated QMS decision endpoint — **PR #263**
2. Argument binding matching/exceeding Paperclip — **PR #263**
3. Material choke points across ≥3 adapters including `process` — **rework required**
4. Short-lived per-action decision semantics — **PR #263**
5. Revocation/outage semantics — **PR #263** (+ demotion matrix doc)
6. Lifecycle demotion matrix — **this PR**
7. Slice B-1 harness with strict PASS/FAIL thresholds — **this PR**

## Apply rework (agents-os)

```bash
# On PR #263 branch in agents-os
bash /path/to/paperclip/doc/agents-os/aad-57-slice-b0-rework/apply-rework.sh

# Follow REWORK.md manual steps (enforcement merge + services.py + MCP handler)

.venv/bin/python manage.py test work_orders.tests.test_spawn_authorization -v2
.venv/bin/python manage.py test integrations.mcp.tests.test_dispatch_authorization -v2
.venv/bin/python manage.py test core.agent_decisions.tests -v2
.venv/bin/python manage.py test workflows.tests.test_runtime -v1
make ci
```

## B-0 gate status

| Gate | Status |
|---|---|
| B-0.1 Agent-authenticated endpoint | **PASS** (PR #263) |
| B-0.2 Argument binding | **PASS** (PR #263) |
| B-0.3 ≥3 adapters incl. `process` | **REWORK** — spawn + MCP patches |
| B-0.4 Short-lived nonce/TTL | **PASS** (PR #263) |

## Acceptance criteria mapping

| AC | Evidence |
|---|---|
| No false claim of Core authorization without callable endpoint | PR #263 `POST /api/agent/action-decisions/` |
| QMS matches/exceeds Paperclip binding/expiry/replay | PR #263 tests + Paperclip comparator doc |
| Trust boundary + unmanaged paths documented | `AAD-57-UNMANAGED-PATH-INVENTORY.md` |
| B-1 executable on ≥3 adapters | After rework + `AAD-57-SLICE-B1-HARNESS-PLAN.md` |
| Architecture PR draft unmerged | Paperclip PR #1 remains NOT APPROVED |

## Cloud Agent note

Paperclip Cloud Agent cannot clone/write `aavendano/agents-os` (403). Rework is delivered as an exact patch bundle for apply in agents-os.

## Next steps

1. Apply rework to agents-os PR #263; push; re-request review.
2. When B-0.3 green, execute B-1 harness cases B0–B10.
3. Record CI evidence in Linear AAD-57.
4. Human Direction review before architecture approval.
