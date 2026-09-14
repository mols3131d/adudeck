#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

if command -v mise >/dev/null 2>&1; then
  eval "$(mise env -s bash 2>/dev/null)" || true
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

case "$TARGET" in
  smoke)
    run_smoke
    ;;
  dataset-generator)
    run_dataset_generator
    ;;
  all)
    run_smoke
    run_dataset_generator
    echo "==> All test suites passed."
    ;;
  *)
    echo "Error: Unknown test target '$TARGET'. Allowed: all, smoke, dataset-generator" >&2
    exit 1
    ;;
esac
