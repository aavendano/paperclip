#!/usr/bin/env bash
# Apply AAD-57 rework bundle on top of agents-os PR #263 checkout.
set -euo pipefail

if [[ ! -f manage.py ]]; then
  echo "Run from agents-os repository root." >&2
  exit 1
fi

SRC="${1:-../paperclip/doc/agents-os/aad-57-slice-b0-rework}"

if [[ ! -f "$SRC/REWORK.md" ]]; then
  echo "Rework bundle not found: $SRC" >&2
  exit 1
fi

mkdir -p integrations/mcp/tests work_orders/tests

# MCP dispatch module
cp "$SRC/integrations/mcp/dispatch.py" integrations/mcp/dispatch.py

# Tests (adjust fixture imports after copy if needed)
cp "$SRC/work_orders/tests/test_spawn_authorization.py" work_orders/tests/test_spawn_authorization.py
cp "$SRC/integrations/mcp/tests/test_dispatch_authorization.py" integrations/mcp/tests/test_dispatch_authorization.py

echo "Rework modules copied."
echo ""
echo "Manual steps required (see $SRC/REWORK.md):"
echo "  1. Merge enforcement_process_spawn.py into core/agent_decisions/enforcement.py"
echo "  2. Wire assert_process_spawn_authorized in work_orders/services.py before Popen"
echo "  3. Route MCP tool calls through integrations.mcp.dispatch.execute_mcp_tool_authorized"
echo "  4. Run tests:"
echo "       .venv/bin/python manage.py test work_orders.tests.test_spawn_authorization -v2"
echo "       .venv/bin/python manage.py test integrations.mcp.tests.test_dispatch_authorization -v2"
echo "       make ci"
