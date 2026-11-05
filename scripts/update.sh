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

for proj in tools/*/pyproject.toml decks/[!_]*/pyproject.toml; do
  if [[ -f "$proj" ]]; then
    proj_dir="$(dirname "$proj")"
    if [[ -f "$proj_dir/uv.lock" ]]; then
      echo "==> [update] Updating $proj_dir dependencies and lockfile..."
      env -u VIRTUAL_ENV uv lock --upgrade --project "$proj_dir"
      env -u VIRTUAL_ENV uv sync --project "$proj_dir" --locked
    fi
  fi
done

echo "==> [update] Updating rulesync external dependencies..."
rulesync install --update
if [[ -f "rulesync.lock" && -f ".agents/route/skills.jsonl" ]]; then
  uv run python - <<'PY'
import json, pathlib, re
ref = json.loads(pathlib.Path("rulesync.lock").read_text())["sources"]["mols3131d/mols-agent-assets"]["resolvedRef"]
p = pathlib.Path(".agents/route/skills.jsonl")
p.write_text(re.sub(r"(https://raw\.githubusercontent\.com/mols3131d/mols-agent-assets/)[0-9a-f]+/", rf"\g<1>{ref}/", p.read_text()))
PY
fi

echo "==> [update] Regenerating agent projections..."
rulesync generate
rulesync generate --targets agentsmd,copilot --features rules
if [[ -f ".rulesync/scripts/project-root-agents.sh" ]]; then
  sh .rulesync/scripts/project-root-agents.sh
fi

echo "==> [update] Refreshing git hooks with lefthook..."
lefthook install

echo "==> Environment update successfully completed!"
