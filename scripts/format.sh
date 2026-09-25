#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if command -v mise >/dev/null 2>&1; then
  eval "$(mise env -s bash 2>/dev/null)" || true
fi

usage() {
  echo "Usage: scripts/format.sh [--check]" >&2
}

CHECK_MODE=false
case "$#" in
  0)
    ;;
  1)
    if [[ "$1" != "--check" ]]; then
      usage
      exit 2
    fi
    CHECK_MODE=true
    ;;
  *)
    usage
    exit 2
    ;;
esac

MARKDOWN_EXCLUDES="AGENTS.md,**/AGENTS.md,AGENTS.override.md,**/AGENTS.override.md,.github/copilot-instructions.md,.github/instructions/**,.github/skills/**,.agents/**,.codex/**"

if [[ "$CHECK_MODE" == true ]]; then
  echo "==> [format:check] Checking Markdown formatting..."
  rumdl fmt --check --exclude "$MARKDOWN_EXCLUDES" .

  echo "==> [format:check] Checking JSON / JSONC formatting..."
  biome format .

  echo "==> [format:check] Checking TOML formatting..."
  tombi format --check .

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
