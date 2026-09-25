#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v mise >/dev/null 2>&1; then
  echo "Error: 'mise' must be installed before setting up this repository." >&2
  exit 1
fi

echo "==> [setup] Installing repository toolchain with mise..."
mise install
eval "$(mise env -s bash 2>/dev/null)" || true

echo "==> [setup] Syncing root Python environment with uv..."
uv sync --locked

if [[ -d "tools/dataset_generator" ]]; then
  echo "==> [setup] Syncing tools/dataset_generator environment..."
  env -u VIRTUAL_ENV uv sync --project tools/dataset_generator --locked
fi

echo "==> [setup] Configuring git commit template..."
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git config --local commit.template .gitmessage
fi

echo "==> [setup] Installing git hooks with lefthook..."
lefthook install

echo "==> [setup] Installing frozen rulesync dependencies..."
rulesync install --frozen

echo "==> Environment setup successfully completed!"
