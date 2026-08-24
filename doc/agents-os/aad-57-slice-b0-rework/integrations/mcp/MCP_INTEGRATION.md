# integrations/mcp — authority at execution

## Context

PR #263 changed `integrations/mcp/authz.py` to add `has_agent_tool_grant()` used at
**mint time** in `core/agent_decisions/services.py`. MCP tool **execution** paths still
call `assert_agent_tool_grant()` only — capability without consumed Authority decision.

## Required architecture

```
Mint (agent API):
  capability check → has_agent_tool_grant
  authority check  → AgentMaterialAuthorityGrant
  → ALLOW row persisted

Execute (MCP handler):
  assert_mcp_tool_authorized → consume_agent_action_decision
  → invoke tool
```

Capability alone must **never** authorize material MCP effects.

## Integration steps

1. Add `integrations/mcp/dispatch.py` from rework bundle.

2. Find MCP tool invocation entry (grep):

```bash
rg -n 'assert_agent_tool_grant|invoke.*tool' integrations/mcp/
```

3. Wrap invocation:

```python
from integrations.mcp.dispatch import execute_mcp_tool_authorized

def handle_tool_call(agent, tool_name, arguments, work_order, run, inputs):
    return execute_mcp_tool_authorized(
        agent=agent,
        tool_name=tool_name,
        arguments=arguments,
        work_order=work_order,
        run=run,
        inputs=inputs,
        agent_profile_id=resolve_profile_id(agent, work_order),
        invoke=lambda: _invoke_tool_impl(tool_name, arguments),
    )
```

4. Do **not** remove `assert_agent_tool_grant` from unrelated validation paths, but
   ensure no execution path uses it as the sole gate.

## Normalized action naming

| MCP tool name | Normalized action | Grant tool_name |
|---|---|---|
| `filesystem.read` | `mcp.filesystem.read` | `mcp.filesystem.read` |
| `web.search` | `mcp.web.search` | `mcp.web.search` |

Mint and credential map must use identical strings.

## Credential transport

```json
{
  "__agent_action_credentials": {
    "mcp.filesystem.read": {
      "decision_id": "aad_…",
      "nonce": "…"
    }
  },
  "path": "/etc/hosts"
}
```

Arguments bound at mint must match execution arguments (path, query, etc.).

## Unmanaged MCP (out of scope)

External MCP servers not registered in QMS are documented in
`AAD-57-UNMANAGED-PATH-INVENTORY.md` gap G-2. This integration covers **managed**
QMS-hosted MCP only.
