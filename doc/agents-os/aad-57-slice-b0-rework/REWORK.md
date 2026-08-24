# AAD-57 Rework — apply to agents-os PR #263

**Target branch:** `cursor/aad-57-slice-b0-c417` (or new branch from PR #263 head `93caa0c`)

**Review verdict:** REWORK_REQUIRED — mint/consume solid; process spawn + MCP + docs missing.

---

## Files in this bundle

| File | Destination in agents-os |
|---|---|
| `core/agent_decisions/enforcement_process_spawn.py` | Merge into `core/agent_decisions/enforcement.py` OR import from enforcement |
| `integrations/mcp/dispatch.py` | `integrations/mcp/dispatch.py` (new) |
| `work_orders/SPAWN_INTEGRATION.md` | Instructions only |
| `integrations/mcp/MCP_INTEGRATION.md` | Instructions only |
| `work_orders/tests/test_spawn_authorization.py` | `work_orders/tests/test_spawn_authorization.py` |
| `integrations/mcp/tests/test_dispatch_authorization.py` | `integrations/mcp/tests/test_dispatch_authorization.py` |

---

## Step 1 — Process spawn gate

### Option A (recommended): append to `enforcement.py`

Copy functions from `enforcement_process_spawn.py` into the bottom of
`core/agent_decisions/enforcement.py`. Export `assert_process_spawn_authorized` in `__all__`.

### Option B: separate module

```python
# core/agent_decisions/enforcement.py (add re-export)
from core.agent_decisions.enforcement_process_spawn import assert_process_spawn_authorized
```

### Wire `work_orders/services.py`

Locate the function that calls `subprocess.Popen` (review cites ~lines 478–486).
Insert **immediately before** `Popen`:

```python
from core.agent_decisions.enforcement import assert_process_spawn_authorized
from core.agent_decisions.exceptions import AgentActionAuthzError

# ... inside spawn function, before subprocess.Popen:
try:
    assert_process_spawn_authorized(
        work_order=work_order,
        run=run,
        command=command,  # argv list passed to Popen
        spawn_context=spawn_payload,  # dict containing __agent_action_credentials
        agent_profile_id=getattr(work_order.operational_state, 'assigned_agent_id', None),
    )
except AgentActionAuthzError as exc:
    # fail-closed: do NOT Popen; mark run failed / re-raise
    logger.warning('Process spawn denied: %s', exc.reason_code)
    raise
```

**Critical:** `spawn_payload` must be the same dict used at mint time for `arguments` binding
(including `command`, `cwd`, `env`).

See `work_orders/SPAWN_INTEGRATION.md` for grant alignment.

---

## Step 2 — MCP authority at execution

### Create `integrations/mcp/dispatch.py`

Copy from this bundle.

### Replace direct tool invocation

Find the MCP tool handler (search for `assert_agent_tool_grant` call sites outside mint).
Replace pattern:

```python
# BEFORE (capability only):
assert_agent_tool_grant(agent=agent, tool_name=tool_name)
return invoke_tool(...)

# AFTER (capability at mint + authority at execution):
from integrations.mcp.dispatch import execute_mcp_tool_authorized

return execute_mcp_tool_authorized(
    agent=agent,
    tool_name=tool_name,
    arguments=tool_arguments,
    work_order=work_order,
    run=run,
    inputs=inputs,
    agent_profile_id=agent_profile_id,
    invoke=lambda: invoke_tool(...),
)
```

**Keep** `has_agent_tool_grant` / `assert_agent_tool_grant` for mint-time capability checks only.

See `integrations/mcp/MCP_INTEGRATION.md`.

---

## Step 3 — Tests

```bash
.venv/bin/python manage.py test work_orders.tests.test_spawn_authorization --verbosity=2
.venv/bin/python manage.py test integrations.mcp.tests.test_dispatch_authorization --verbosity=2
.venv/bin/python manage.py test core.agent_decisions.tests --verbosity=2
.venv/bin/python manage.py test workflows.tests.test_runtime --verbosity=1
make ci
```

---

## Step 4 — Update PR #263 description

Add to PR body:

- Process spawn wired via `assert_process_spawn_authorized`
- MCP dispatch wired via `execute_mcp_tool_authorized`
- B-0.3 now covers ≥3 adapters: python/service/agent providers + process spawn + MCP
- Link Paperclip docs: unmanaged inventory, demotion matrix, B-1 harness

---

## Grant alignment checklist

For each material surface, these three must use the **same normalized action string**:

1. `AgentToolGrant.tool_name` (capability)
2. `AgentMaterialAuthorityGrant.normalized_action` (authority ticket)
3. Mint `action` + `__agent_action_credentials` map key

Examples:

| Surface | Normalized action |
|---|---|
| Process spawn | `process.agent` |
| Python provider | `python.{provider_key}` |
| BPMN service | `service.{service_key}` |
| MCP tool | `mcp.{tool_name}` |

---

## Verification against acceptance criteria

| AC | Evidence |
|---|---|
| Callable decision endpoint | Existing PR #263 tests (44+) |
| Argument binding parity | `test_services` binding mismatch |
| Trust boundary documented | Paperclip `AAD-57-UNMANAGED-PATH-INVENTORY.md` |
| ≥3 adapters with correlation | dispatch + spawn + MCP tests green |
| Architecture PR draft | Paperclip PR #1 unchanged, NOT APPROVED |
