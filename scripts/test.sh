#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

usage() {
  echo "Usage: scripts/test.sh [all|smoke|dataset-generator|openai-sdk-deck|langfuse-deck|opentelemetry-deck|opentelemetry-acceptance|scripts ...]" >&2
  echo "       scripts/test.sh --ci-scope [<base-ref>|--stdin]" >&2
}

resolve_ci_scope_from_stream() {
  local source_label="$1"
  local broaden=false
  local otel_acceptance=false
  local add_dataset=false
  local add_openai=false
  local add_langfuse=false
  local add_otel=false
  local reason=""
  local file_count=0
  local file
  local deck_dir

  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    file_count=$((file_count + 1))
    case "$file" in
      mise.toml|pyproject.toml|uv.lock|scripts/*|.github/workflows/*)
        broaden=true
        otel_acceptance=true
        reason="shared infrastructure changed (${file})"
        break
        ;;
      tools/dataset_generator/*)
        add_dataset=true
        ;;
      decks/ai-openai_sdk/*)
        add_openai=true
        ;;
      decks/llmops-langfuse/*)
        add_langfuse=true
        ;;
      decks/systems-opentelemetry/*)
        add_otel=true
        otel_acceptance=true
        ;;
      README.md|CHATBOT.md|AGENTS.md|.editorconfig|.gitattributes|.gitignore|.gitmessage|biome.json|lefthook.yml|rulesync.jsonc|rulesync.lock|docs/*|inbox/*|.vscode/*|.rulesync/*|.agents/*|.github/copilot-instructions.md|.github/instructions/*|.github/skills/*|.codex/*|.gemini/*|.opencode/*|decks/README.md|decks/AGENTS.md|decks/_archive/*|decks/_backlog/*|decks/computer-science/*|decks/data_engineering-apache_airflow/*)
        ;;
      decks/*/*)
        deck_dir="${file#decks/}"
        deck_dir="decks/${deck_dir%%/*}"
        if [[ ! -f "${deck_dir}/pyproject.toml" && ! -d "${deck_dir}/tests" && "$file" == *.md ]]; then
          :
        else
          broaden=true
          otel_acceptance=true
          reason="unclassified deck path (${file})"
          break
        fi
        ;;
      *)
        broaden=true
        otel_acceptance=true
        reason="unclassified path (${file})"
        break
        ;;
    esac
  done

  if [[ "$broaden" == true ]]; then
    printf 'test_targets=all\notel_acceptance=true\nscope_reason=%s\n' "$reason"
    return 0
  fi

  local targets=(smoke)
  [[ "$add_dataset" == true ]] && targets+=(dataset-generator)
  [[ "$add_openai" == true ]] && targets+=(openai-sdk-deck)
  [[ "$add_langfuse" == true ]] && targets+=(langfuse-deck)
  [[ "$add_otel" == true ]] && targets+=(opentelemetry-deck)
  targets+=(scripts)

  if [[ "$file_count" -eq 0 ]]; then
    reason="no changed files (${source_label})"
  else
    reason="routed from ${file_count} changed file(s) (${source_label})"
  fi

  printf 'test_targets=%s\notel_acceptance=%s\nscope_reason=%s\n' "${targets[*]}" "$otel_acceptance" "$reason"
}

if [[ "${1:-}" == "--ci-scope" ]]; then
  if [[ "$#" -ne 2 ]]; then
    usage
    exit 2
  fi
  if [[ "$2" == "--stdin" ]]; then
    resolve_ci_scope_from_stream "stdin"
    exit 0
  fi
  base_ref="$2"
  merge_base="$(git merge-base "$base_ref" HEAD 2>/dev/null || true)"
  if [[ -z "$merge_base" ]]; then
    printf 'test_targets=all\notel_acceptance=true\nscope_reason=merge-base with %s unavailable (fail-safe full scope)\n' "$base_ref"
    exit 0
  fi
  resolve_ci_scope_from_stream "diff against ${base_ref}" < <(
    {
      git -c core.quotePath=false diff --name-only "$merge_base" HEAD
      git -c core.quotePath=false diff --name-only HEAD
      git -c core.quotePath=false ls-files --others --exclude-standard
    } | sort -u
  )
  exit 0
fi

if command -v mise >/dev/null 2>&1; then
  eval "$(mise env -s bash 2>/dev/null)" || true
fi

if [[ "$#" -eq 0 ]]; then
  if [[ -n "${CI_TEST_TARGETS:-}" ]]; then
    read -r -a REQUESTED_TARGETS <<<"$CI_TEST_TARGETS"
  else
    REQUESTED_TARGETS=(all)
  fi
else
  REQUESTED_TARGETS=("$@")
fi

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
  trap 'rm -rf "${tmp_dir:-}"' RETURN
  env -u VIRTUAL_ENV uv run --project tools/dataset_generator --locked adudeck-data generate ecommerce --output "$tmp_dir" --users 2 --products 2 --orders 2 --seed 1
  echo "==> [test:dataset-generator] Dataset generator tests passed."
}

run_openai_sdk_deck() {
  echo "==> [test:openai-sdk-deck] Checking locked deck environment and local retry lab..."
  local project_dir="decks/ai-openai_sdk"
  local retry_output

  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked python -m compileall -q \
    "$project_dir/textbook" \
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
      python "$project_dir/textbook/03-failure-boundaries/failure_boundaries.py"
  )"
  printf '%s\n' "$retry_output"

  grep -Fq "exception: RateLimitError" <<<"$retry_output"
  grep -Fq "status: 429" <<<"$retry_output"
  grep -Fq "request id: req_adudeck_3" <<<"$retry_output"
  grep -Fq "HTTP attempts: 3" <<<"$retry_output"

  echo "==> [test:openai-sdk-deck] Locked deck validation passed."
}

run_langfuse_deck() {
  echo "==> [test:langfuse-deck] Checking locked deck environment and textbook contracts..."
  local project_dir="decks/llmops-langfuse"

  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python -m compileall -q "$project_dir/textbook"

  echo "==> [test:langfuse-deck] Checking installed Langfuse/OpenAI public API surface..."
  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked python - <<'PY'
import inspect

from langfuse import (
    Evaluation,
    Langfuse,
    LangfuseSpan,
    get_client,
    propagate_attributes,
)
from langfuse.api import NotFoundError
from langfuse.openai import OpenAI as LangfuseOpenAI

assert callable(get_client)
assert callable(propagate_attributes)
assert callable(Evaluation)
assert issubclass(NotFoundError, Exception)

for method_name in (
    "start_as_current_observation",
    "create_dataset_item",
    "get_dataset",
    "run_experiment",
    "get_prompt",
    "create_prompt",
    "flush",
):
    assert callable(getattr(Langfuse, method_name))

assert callable(LangfuseSpan.score)
assert callable(LangfuseSpan.score_trace)

get_dataset_params = inspect.signature(Langfuse.get_dataset).parameters
assert "version" in get_dataset_params

create_dataset_item_params = inspect.signature(Langfuse.create_dataset_item).parameters
assert "id" in create_dataset_item_params

get_prompt_params = inspect.signature(Langfuse.get_prompt).parameters
assert "version" in get_prompt_params
assert "label" in get_prompt_params
assert "cache_ttl_seconds" in get_prompt_params

create_prompt_params = inspect.signature(Langfuse.create_prompt).parameters
for parameter in ("name", "prompt", "labels", "type"):
    assert parameter in create_prompt_params

client = LangfuseOpenAI(api_key="local-test-key")
assert callable(client.responses.create)
PY

  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python "$project_dir/textbook/01-first-trace/test_first_trace.py"
  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python "$project_dir/textbook/02-trace-design/test_trace_design.py"
  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python "$project_dir/textbook/03-openai-integration/test_openai_integration.py"
  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python "$project_dir/textbook/04-scores/test_score_evidence.py"
  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python "$project_dir/textbook/05-datasets/test_dataset_case.py"
  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python "$project_dir/textbook/06-experiments/test_experiment_compare.py"
  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python "$project_dir/textbook/07-prompt-management/test_prompt_versioning.py"
  env -u VIRTUAL_ENV uv run --project "$project_dir" --locked \
    python "$project_dir/textbook/08-evaluation-loop/test_release_gate.py"

  echo "==> [test:langfuse-deck] Locked SDK and textbook contract validation passed."
}

run_opentelemetry_deck() {
  echo "==> [test:opentelemetry-deck] Validating locked core textbook evidence..."
  env -u VIRTUAL_ENV uv run --project decks/systems-opentelemetry --locked \
    python -m unittest discover -s decks/systems-opentelemetry/tests -p 'test_first_trace.py' -v
  env -u VIRTUAL_ENV uv run --project decks/systems-opentelemetry --locked \
    python -m unittest discover -s decks/systems-opentelemetry/tests -p 'test_textbook_examples.py' -v
}

run_opentelemetry_acceptance() {
  echo "==> [test:opentelemetry-acceptance] Running Flask zero-code and OTLP/Collector end-to-end acceptance..."
  env -u VIRTUAL_ENV uv run --project decks/systems-opentelemetry --locked \
    python decks/systems-opentelemetry/tests/test_external_runtime.py
  echo "==> [test:opentelemetry-acceptance] External runtime acceptance passed."
}

run_scripts() {
  echo "==> [test:scripts] Checking shell script syntax and CI scope routing..."
  bash -n scripts/*.sh

  local scope_out
  scope_out="$(printf '' | bash scripts/test.sh --ci-scope --stdin)"
  grep -Fxq "test_targets=smoke scripts" <<<"$scope_out"
  grep -Fxq "otel_acceptance=false" <<<"$scope_out"

  scope_out="$(printf 'docs/automation.md\n.rulesync/rules/overview.md\nrulesync.lock\ndecks/computer-science/README.md\n' | bash scripts/test.sh --ci-scope --stdin)"
  grep -Fxq "test_targets=smoke scripts" <<<"$scope_out"
  grep -Fxq "otel_acceptance=false" <<<"$scope_out"

  scope_out="$(printf 'decks/llmops-langfuse/README.md\ntools/dataset_generator/README.md\n' | bash scripts/test.sh --ci-scope --stdin)"
  grep -Fxq "test_targets=smoke dataset-generator langfuse-deck scripts" <<<"$scope_out"
  grep -Fxq "otel_acceptance=false" <<<"$scope_out"

  scope_out="$(printf 'decks/systems-opentelemetry/tests/test_first_trace.py\n' | bash scripts/test.sh --ci-scope --stdin)"
  grep -Fxq "test_targets=smoke opentelemetry-deck scripts" <<<"$scope_out"
  grep -Fxq "otel_acceptance=true" <<<"$scope_out"

  scope_out="$(printf 'docs/README.md\nmise.toml\n' | bash scripts/test.sh --ci-scope --stdin)"
  grep -Fxq "test_targets=all" <<<"$scope_out"
  grep -Fxq "otel_acceptance=true" <<<"$scope_out"

  scope_out="$(printf 'decks/unclassified-new-deck/lab.py\n' | bash scripts/test.sh --ci-scope --stdin)"
  grep -Fxq "test_targets=all" <<<"$scope_out"
  grep -Fxq "otel_acceptance=true" <<<"$scope_out"

  scope_out="$(printf 'unclassified-root-file.txt\n' | bash scripts/test.sh --ci-scope --stdin)"
  grep -Fxq "test_targets=all" <<<"$scope_out"
  grep -Fxq "otel_acceptance=true" <<<"$scope_out"

  scope_out="$(
    git -c core.quotePath=false ls-files \
      | grep -Ev '^(mise\.toml|pyproject\.toml|uv\.lock|scripts/|\.github/workflows/)' \
      | bash scripts/test.sh --ci-scope --stdin
  )"
  grep -Fxq "test_targets=smoke dataset-generator openai-sdk-deck langfuse-deck opentelemetry-deck scripts" <<<"$scope_out"
  grep -Fxq "otel_acceptance=true" <<<"$scope_out"
  grep -Fq "scope_reason=routed from " <<<"$scope_out"

  echo "==> [test:scripts] Shell script syntax and CI scope routing passed."
}

run_smoke_flag=false
run_dataset_flag=false
run_openai_flag=false
run_langfuse_flag=false
run_otel_flag=false
run_otel_acceptance_flag=false
run_scripts_flag=false
run_all_flag=false

for target in "${REQUESTED_TARGETS[@]}"; do
  case "$target" in
    smoke)
      run_smoke_flag=true
      ;;
    dataset-generator)
      run_dataset_flag=true
      ;;
    openai-sdk-deck)
      run_openai_flag=true
      ;;
    langfuse-deck)
      run_langfuse_flag=true
      ;;
    opentelemetry-deck)
      run_otel_flag=true
      ;;
    opentelemetry-acceptance)
      run_otel_acceptance_flag=true
      ;;
    scripts)
      run_scripts_flag=true
      ;;
    all)
      run_all_flag=true
      run_smoke_flag=true
      run_dataset_flag=true
      run_openai_flag=true
      run_langfuse_flag=true
      run_otel_flag=true
      run_scripts_flag=true
      ;;
    *)
      echo "Error: Unknown test target '$target'. Allowed: all, smoke, dataset-generator, openai-sdk-deck, langfuse-deck, opentelemetry-deck, opentelemetry-acceptance, scripts" >&2
      exit 1
      ;;
  esac
done

[[ "$run_smoke_flag" == true ]] && run_smoke
[[ "$run_dataset_flag" == true ]] && run_dataset_generator
[[ "$run_openai_flag" == true ]] && run_openai_sdk_deck
[[ "$run_langfuse_flag" == true ]] && run_langfuse_deck
[[ "$run_otel_flag" == true ]] && run_opentelemetry_deck
[[ "$run_otel_acceptance_flag" == true ]] && run_opentelemetry_acceptance
[[ "$run_scripts_flag" == true ]] && run_scripts

if [[ "$run_all_flag" == true ]]; then
  echo "==> All test suites passed."
fi
