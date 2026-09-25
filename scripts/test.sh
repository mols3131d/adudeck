#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if command -v mise >/dev/null 2>&1; then
  eval "$(mise env -s bash 2>/dev/null)" || true
fi

if [[ "$#" -gt 1 ]]; then
  echo "Usage: scripts/test.sh [all|smoke|dataset-generator|openai-sdk-deck|scripts]" >&2
  exit 2
fi

TARGET="${1:-all}"

run_smoke() {
  echo "==> [test:smoke] Running minimal local runtime smoke test..."
  uv run python -c 'import sys; assert sys.version_info[:2] == (3, 14), f"Expected Python 3.14, got {sys.version}"'
  echo "==> [test:smoke] Smoke test passed."
}

run_dataset_generator() {
  echo "==> [test:dataset-generator] Running dataset generator unit tests..."
  env -u VIRTUAL_ENV uv run --project tools/dataset_generator --locked python -m unittest discover -s tools/dataset_generator/tests -v

  echo "==> [test:dataset-generator] Running CLI smoke test..."
  local tmp_dir
  tmp_dir="$(mktemp -d)"
  trap 'rm -rf "${tmp_dir:-}"' EXIT
  env -u VIRTUAL_ENV uv run --project tools/dataset_generator --locked adudeck-data generate ecommerce --output "$tmp_dir" --users 2 --products 2 --orders 2 --seed 1
  rm -rf "$tmp_dir"
  trap - EXIT
  echo "==> [test:dataset-generator] Dataset generator tests passed."
}

run_openai_sdk_deck() {
  echo "==> [test:openai-sdk-deck] Checking locked deck environment and local retry lab..."
  local project_dir="decks/ai-openai_sdk"
  local retry_output

  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked python -m compileall -q \
    "$project_dir/playground" \
    "$project_dir/scripts"

  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked python - <<'PY'
from openai import OpenAI

client = OpenAI(api_key="local-test-key")
assert callable(client.responses.create)
assert callable(client.responses.parse)
assert callable(client.conversations.create)
assert callable(client.conversations.delete)
assert callable(client.conversations.items.list)
assert callable(client.conversations.items.delete)
PY

  retry_output="$(
    env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
      python "$project_dir/playground/failure_boundaries.py"
  )"
  printf '%s\n' "$retry_output"

  grep -Fq "exception: RateLimitError" <<<"$retry_output"
  grep -Fq "status: 429" <<<"$retry_output"
  grep -Fq "request id: req_adudeck_3" <<<"$retry_output"
  grep -Fq "HTTP attempts: 3" <<<"$retry_output"

  echo "==> [test:openai-sdk-deck] Locked deck validation passed."
}

run_scripts() {
  echo "==> [test:scripts] Checking shell script syntax..."
  bash -n scripts/*.sh
  echo "==> [test:scripts] Shell script syntax passed."
}

case "$TARGET" in
  smoke)
    run_smoke
    ;;
  dataset-generator)
    run_dataset_generator
    ;;
  openai-sdk-deck)
    run_openai_sdk_deck
    ;;
  scripts)
    run_scripts
    ;;
  all)
    run_smoke
    run_dataset_generator
    run_openai_sdk_deck
    run_scripts
    echo "==> All test suites passed."
    ;;
  *)
    echo "Error: Unknown test target '$TARGET'. Allowed: all, smoke, dataset-generator, openai-sdk-deck, scripts" >&2
    exit 1
    ;;
esac
