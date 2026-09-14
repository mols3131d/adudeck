#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if command -v mise >/dev/null 2>&1; then
  eval "$(mise env -s bash 2>/dev/null)" || true
fi

CHECK_MODE=false
if [[ "${1:-}" == "--check" ]]; then
  CHECK_MODE=true
fi

MARKDOWN_EXCLUDES="AGENTS.md,**/AGENTS.md,AGENTS.override.md,**/AGENTS.override.md,.github/copilot-instructions.md,.github/instructions/**,.github/skills/**,.agents/**,.codex/**"

if [[ "$CHECK_MODE" == true ]]; then
  echo "==> [format:check] Checking Markdown formatting..."
  rumdl fmt --check --exclude "$MARKDOWN_EXCLUDES" .

  echo "==> [format:check] Checking JSON / JSONC..."
  biome check .

  echo "==> [format:check] Linting TOML..."
  tombi lint --error-on-warnings .

  echo "==> All format checks passed."
else
  echo "==> [format] Formatting Markdown..."
  rumdl fmt --exclude "$MARKDOWN_EXCLUDES" .

  echo "==> [format] Formatting JSON / JSONC..."
  biome format --write .

  echo "==> [format] Formatting TOML..."
  tombi format .

  echo "==> Formatting complete."
fi

