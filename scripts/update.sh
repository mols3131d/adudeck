#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> [update] Upgrading toolchains with mise..."
if command -v mise >/dev/null 2>&1; then
  mise upgrade
  eval "$(mise env -s bash 2>/dev/null)" || true
else
  echo "Warning: 'mise' is not installed or not in PATH. Skipping 'mise upgrade'." >&2
fi

echo "==> [update] Updating root Python dependencies and lockfile..."
uv lock --upgrade
uv sync

if [[ -d "tools/dataset_generator" ]]; then
  echo "==> [update] Updating tools/dataset_generator dependencies and lockfile..."
  env -u VIRTUAL_ENV uv lock --upgrade --project tools/dataset_generator
  env -u VIRTUAL_ENV uv sync --project tools/dataset_generator
fi

echo "==> [update] Updating rulesync external dependencies..."
rulesync install

echo "==> [update] Regenerating agent projections..."
rulesync generate
rulesync generate --targets agentsmd,copilot --features rules
if [[ -f ".rulesync/scripts/project-root-agents.sh" ]]; then
  sh .rulesync/scripts/project-root-agents.sh
fi

echo "==> [update] Refreshing git hooks with lefthook..."
lefthook install

echo "==> Environment update successfully completed!"
