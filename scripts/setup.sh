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

for proj in tools/*/pyproject.toml decks/[!_]*/pyproject.toml; do
  if [[ -f "$proj" ]]; then
    proj_dir="$(dirname "$proj")"
    if [[ -f "$proj_dir/uv.lock" ]]; then
      echo "==> [setup] Syncing $proj_dir environment with uv..."
      env -u VIRTUAL_ENV uv sync --project "$proj_dir" --locked
    fi
  fi
done

echo "==> [setup] Configuring git commit template..."
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git config --local commit.template .gitmessage
fi

echo "==> [setup] Installing git hooks with lefthook..."
lefthook install

echo "==> [setup] Installing frozen rulesync dependencies and local skill projections..."
rulesync install --frozen
rulesync generate

echo "==> Environment setup successfully completed!"
