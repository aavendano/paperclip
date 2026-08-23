#!/usr/bin/env bash
# Apply Slice B-0 patch bundle from Paperclip experiment docs into a local agents-os checkout.
set -euo pipefail

if [[ ! -f manage.py ]]; then
  echo "Run from agents-os repository root (manage.py not found)." >&2
  exit 1
fi

SRC="${1:-../paperclip/doc/agents-os/aad-57-slice-b0}"
if [[ ! -d "$SRC/core/agent_decisions" ]]; then
  echo "Patch source not found: $SRC" >&2
  exit 1
fi

cp -R "$SRC/core/agent_decisions" core/
cp "$SRC/processes/material_execution.py" processes/

echo "Copied Slice B-0 modules. Next steps:"
echo "  1. Register core.agent_decisions in INSTALLED_APPS"
echo "  2. Wire router per doc/agents-os/aad-57-slice-b0/PATCHES.md"
echo "  3. .venv/bin/python manage.py makemigrations core.agent_decisions"
echo "  4. .venv/bin/python manage.py migrate"
echo "  5. .venv/bin/python manage.py test core.agent_decisions.tests --verbosity=2"
echo "  6. make ci"
