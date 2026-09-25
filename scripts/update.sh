#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v mise >/dev/null 2>&1; then
  echo "Error: 'mise' is required to update the repository toolchain." >&2
  exit 1
fi

echo "==> [update] Updating Python within the repository-supported 3.14 series..."
mise use --pin python@3.14

echo "==> [update] Updating other repository-local tool pins with mise..."
mise upgrade --bump --local --exclude python
eval "$(mise env -s bash 2>/dev/null)" || true

echo "==> [update] Updating root Python dependencies and lockfile..."
uv lock --upgrade
uv sync --locked

if [[ -d "tools/dataset_generator" ]]; then
  echo "==> [update] Updating tools/dataset_generator dependencies and lockfile..."
  env -u VIRTUAL_ENV uv lock --upgrade --project tools/dataset_generator
  env -u VIRTUAL_ENV uv sync --project tools/dataset_generator --locked
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
