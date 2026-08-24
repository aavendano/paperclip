# work_orders/services.py — process spawn integration

## Context

Independent review (AAD-57, 2026-08-24) verified that `work_orders/services.py` reaches
`subprocess.Popen` without calling `consume_agent_action_decision`. PR #263 wired
workflow providers but **did not modify** this file.

## Locate integration point

```bash
rg -n 'subprocess\.Popen' work_orders/services.py
```

Expected: one function handling agent/worker subprocess spawn for assigned work orders.

## Required change

```python
def _spawn_agent_subprocess(work_order, run, command, spawn_payload, ...):
    from core.agent_decisions.enforcement import assert_process_spawn_authorized
    from core.agent_decisions.exceptions import AgentActionAuthzError

    assert_process_spawn_authorized(
        work_order=work_order,
        run=run,
        command=command,
        spawn_context=spawn_payload,
        agent_profile_id=_resolve_spawn_agent_profile_id(work_order),
    )

    proc = subprocess.Popen(
        command,
        ...
    )
```

## Mint side (agent caller)

Before spawn, agent must mint with matching arguments:

```http
POST /api/agent/action-decisions/
{
  "request_id": "...",
  "scope": {
    "work_order_id": 1,
    "run_id": 2,
    "process_id": 3,
    "agent_profile_id": 4
  },
  "action": "process.agent",
  "arguments": {
    "command": ["/path/to/agent", "--run", "2"],
    "cwd": "/workspace",
    "env": {"KEY": "value"}
  },
  "nonce": "unique-per-spawn"
}
```

## Spawn payload credential transport

```python
spawn_payload = {
    '__agent_action_credentials': {
        'process.agent': {
            'decision_id': minted['decision_id'],
            'nonce': minted['nonce'],
        },
    },
    'command': ["/path/to/agent", "--run", "2"],
    'cwd': '/workspace',
}
```

## Failure handling

| Error | Behavior |
|---|---|
| `AgentActionAuthzError` | Do not Popen; fail run/work order; log `reason_code` |
| Missing credential | `REASON_CONSUME_MISSING` |
| Missing nonce | `REASON_CONSUME_NONCE_MISSING` + `consume_deny` audit |
| Replay | `REASON_CONSUME_REPLAY` |

## Grants required

```python
AgentToolGrant(tool_name='process.agent', agent=...)
AgentMaterialAuthorityGrant(normalized_action='process.agent', agent=...)
```
