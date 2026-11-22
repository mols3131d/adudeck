"""Run repository verification targets and resolve change-proportional CI scope."""

from __future__ import annotations

import os
import py_compile
import sys
import tempfile
from collections.abc import Iterable, Mapping

from _common import REPO_ROOT, build_env, run
from typecheck import check_project

ALLOWED_TARGETS = (
    "all",
    "smoke",
    "dataset-generator",
    "langchain-deck",
    "openai-sdk-deck",
    "langfuse-deck",
    "opentelemetry-deck",
    "opentelemetry-acceptance",
    "scripts",
)

SHARED_INFRA_EXACT = frozenset({"mise.toml", "pyproject.toml", "uv.lock"})
SHARED_INFRA_PREFIXES = ("scripts/", ".github/workflows/")

NON_TEST_EXACT = frozenset(
    {
        "README.md",
        "AGENTS.md",
        ".editorconfig",
        ".gitattributes",
        ".gitignore",
        ".gitmessage",
        ".rumdl.toml",
        "biome.json",
        "lefthook.yml",
        "rulesync.jsonc",
        "rulesync.lock",
        ".github/copilot-instructions.md",
        ".github/pull_request_template.md",
        "decks/README.md",
        "decks/AGENTS.md",
    }
)

NON_TEST_PREFIXES = (
    "docs/",
    ".inbox/",
    ".vscode/",
    ".rulesync/",
    ".agents/",
    ".claude/",
    ".copilot/",
    ".github/agents/",
    ".github/instructions/",
    ".github/prompts/",
    ".github/skills/",
    ".codex/",
    ".gemini/",
    ".opencode/",
    "decks/_archive/",
    "decks/_backlog/",
    "decks/computer-science/",
    "decks/data_engineering-apache_airflow/",
)

UNEXPECTED_TRACKED_PROJECTIONS = (
    "CHATBOT.md",
    ".agents/route",
    ".github/copilot-instructions.md",
    ".github/instructions",
    "decks/AGENTS.md",
    "decks/_archive/AGENTS.md",
    "decks/_backlog/AGENTS.md",
)

OPENAI_SURFACE_CHECK = """\
from openai import OpenAI

client = OpenAI(api_key="local-test-key")
assert callable(client.responses.create)
assert callable(client.responses.parse)
assert callable(client.conversations.create)
assert callable(client.conversations.delete)
assert callable(client.conversations.items.list)
assert callable(client.conversations.items.delete)
"""

LANGFUSE_SURFACE_CHECK = """\
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
"""


def usage() -> None:
    print(
        "Usage: scripts/test.py [all|smoke|dataset-generator|openai-sdk-deck|"
        "langchain-deck|langfuse-deck|opentelemetry-deck|opentelemetry-acceptance|scripts ...]",
        file=sys.stderr,
    )
    print(
        "       scripts/test.py --ci-scope [<base-ref>|--stdin]",
        file=sys.stderr,
    )


def resolve_ci_scope(files: Iterable[str], source_label: str) -> str:
    broaden = False
    otel_acceptance = False
    add_dataset = False
    add_langchain = False
    add_openai = False
    add_langfuse = False
    add_otel = False
    reason = ""
    file_count = 0

    for raw_file in files:
        file_path = raw_file.strip().replace("\\", "/")
        if not file_path:
            continue
        file_count += 1

        if file_path in SHARED_INFRA_EXACT or file_path.startswith(
            SHARED_INFRA_PREFIXES
        ):
            broaden = True
            otel_acceptance = True
            reason = f"shared infrastructure changed ({file_path})"
            break
        if file_path.startswith("tools/dataset_generator/"):
            add_dataset = True
        elif file_path.startswith("decks/ai-langchain/"):
            add_langchain = True
        elif file_path.startswith("decks/ai-openai_sdk/"):
            add_openai = True
        elif file_path.startswith("decks/llmops-langfuse/"):
            add_langfuse = True
        elif file_path.startswith("decks/systems-opentelemetry/"):
            add_otel = True
            otel_acceptance = True
        elif file_path in NON_TEST_EXACT or file_path.startswith(NON_TEST_PREFIXES):
            continue
        elif file_path.startswith("decks/") and file_path.count("/") >= 2:
            deck_name = file_path.split("/", 2)[1]
            deck_dir = REPO_ROOT / "decks" / deck_name
            if (
                not (deck_dir / "pyproject.toml").is_file()
                and not (deck_dir / "tests").is_dir()
                and file_path.endswith(".md")
            ):
                continue
            broaden = True
            otel_acceptance = True
            reason = f"unclassified deck path ({file_path})"
            break
        else:
            broaden = True
            otel_acceptance = True
            reason = f"unclassified path ({file_path})"
            break

    if broaden:
        return f"test_targets=all\notel_acceptance=true\nscope_reason={reason}\n"

    targets = ["smoke"]
    if add_dataset:
        targets.append("dataset-generator")
    if add_langchain:
        targets.append("langchain-deck")
    if add_openai:
        targets.append("openai-sdk-deck")
    if add_langfuse:
        targets.append("langfuse-deck")
    if add_otel:
        targets.append("opentelemetry-deck")
    targets.append("scripts")

    if file_count == 0:
        reason = f"no changed files ({source_label})"
    else:
        reason = f"routed from {file_count} changed file(s) ({source_label})"

    otel_str = "true" if otel_acceptance else "false"
    return (
        f"test_targets={' '.join(targets)}\n"
        f"otel_acceptance={otel_str}\n"
        f"scope_reason={reason}\n"
    )


def handle_ci_scope(args: list[str]) -> int:
    if len(args) != 2:
        usage()
        return 2

    target = args[1]
    if target == "--stdin":
        sys.stdout.write(resolve_ci_scope(sys.stdin.read().splitlines(), "stdin"))
        return 0

    merge_base_result = run(
        ["git", "merge-base", target, "HEAD"],
        check=False,
        capture_output=True,
    )
    merge_base = merge_base_result.stdout.strip()
    if merge_base_result.returncode != 0 or not merge_base:
        sys.stdout.write(
            "test_targets=all\n"
            "otel_acceptance=true\n"
            f"scope_reason=merge-base with {target} unavailable (fail-safe full scope)\n"
        )
        return 0

    changed: set[str] = set()
    for git_cmd in (
        [
            "git",
            "-c",
            "core.quotePath=false",
            "diff",
            "--name-only",
            merge_base,
            "HEAD",
        ],
        ["git", "-c", "core.quotePath=false", "diff", "--name-only", "HEAD"],
        [
            "git",
            "-c",
            "core.quotePath=false",
            "ls-files",
            "--others",
            "--exclude-standard",
        ],
    ):
        res = run(git_cmd, capture_output=True)
        changed.update(line for line in res.stdout.splitlines() if line)

    sys.stdout.write(resolve_ci_scope(sorted(changed), f"diff against {target}"))
    return 0


def run_smoke(env: Mapping[str, str]) -> None:
    print("==> [test:smoke] Running minimal local runtime smoke test...")
    run(
        [
            "uv",
            "run",
            "python",
            "-c",
            'import sys; assert sys.version_info[:2] == (3, 14), f"Expected Python 3.14, got {sys.version}"',
        ],
        env=env,
    )
    check_project(".", base_env=env)
    print("==> [test:smoke] Smoke test passed.")


def run_dataset_generator(env: Mapping[str, str], sub_env: Mapping[str, str]) -> None:
    project_dir = "tools/dataset_generator"
    print("==> [test:dataset-generator] Running dataset generator unit tests...")
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            "-m",
            "unittest",
            "discover",
            "-s",
            f"{project_dir}/tests",
            "-v",
        ],
        env=sub_env,
    )

    print("==> [test:dataset-generator] Running CLI smoke test...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        run(
            [
                "uv",
                "run",
                "--project",
                project_dir,
                "--locked",
                "adudeck-data",
                "generate",
                "ecommerce",
                "--output",
                tmp_dir,
                "--users",
                "2",
                "--products",
                "2",
                "--orders",
                "2",
                "--seed",
                "1",
            ],
            env=sub_env,
        )

    check_project(project_dir, base_env=env)
    print("==> [test:dataset-generator] Dataset generator tests passed.")


def run_openai_sdk_deck(env: Mapping[str, str], sub_env: Mapping[str, str]) -> None:
    project_dir = "decks/ai-openai_sdk"
    print(
        "==> [test:openai-sdk-deck] Checking locked deck environment and local retry lab..."
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            "-m",
            "compileall",
            "-q",
            f"{project_dir}/textbook",
            f"{project_dir}/scripts",
        ],
        env=sub_env,
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            "-c",
            OPENAI_SURFACE_CHECK,
        ],
        env=sub_env,
    )
    retry = run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{project_dir}/textbook/03-failure-boundaries/failure_boundaries.py",
        ],
        env=sub_env,
        capture_output=True,
    )
    print(retry.stdout, end="")
    for expected in (
        "exception: RateLimitError",
        "status: 429",
        "request id: req_adudeck_3",
        "HTTP attempts: 3",
    ):
        if expected not in retry.stdout:
            print(
                f"Error: expected '{expected}' in OpenAI retry output.",
                file=sys.stderr,
            )
            raise SystemExit(1)

    check_project(project_dir, base_env=env)
    print("==> [test:openai-sdk-deck] Locked deck validation passed.")


def run_langchain_deck(env: Mapping[str, str], sub_env: Mapping[str, str]) -> None:
    project_dir = "decks/ai-langchain"
    lab_dir = f"{project_dir}/playground/01-agent-loop"
    state_lab_dir = f"{project_dir}/playground/02-state-context"
    structured_lab_dir = f"{project_dir}/playground/03-structured-output"
    trace_lab_dir = f"{project_dir}/playground/04-observation-verification"
    live_lab_dir = f"{project_dir}/playground/05-live-provider"

    print(
        "==> [test:langchain-deck] Validating locked deck environment and offline LangChain labs..."
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            "-m",
            "compileall",
            "-q",
            f"{project_dir}/playground",
        ],
        env=sub_env,
    )

    print("==> [test:langchain-deck] Executing the first LangChain agent-loop lab...")
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{lab_dir}/test_first_agent.py",
        ],
        env=sub_env,
    )
    for scenario in ("model-only", "no-tool", "tool", "error"):
        run(
            [
                "uv",
                "run",
                "--project",
                project_dir,
                "--locked",
                "python",
                f"{lab_dir}/first_agent.py",
                "--scenario",
                scenario,
            ],
            env=sub_env,
        )

    print("==> [test:langchain-deck] Running state/context/middleware checks...")
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{state_lab_dir}/test_state_context.py",
        ],
        env=sub_env,
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{state_lab_dir}/state_context.py",
        ],
        env=sub_env,
    )

    print(
        "==> [test:langchain-deck] Verifying structured-output validation and recovery..."
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{structured_lab_dir}/test_structured_response.py",
        ],
        env=sub_env,
    )
    for rating_scenario in ("valid", "repair", "reject"):
        run(
            [
                "uv",
                "run",
                "--project",
                project_dir,
                "--locked",
                "python",
                f"{structured_lab_dir}/structured_response.py",
                "--scenario",
                rating_scenario,
            ],
            env=sub_env,
        )

    print(
        "==> [test:langchain-deck] Observing streaming steps and tool-error middleware..."
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{trace_lab_dir}/test_trace_and_recovery.py",
        ],
        env=sub_env,
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{trace_lab_dir}/trace_and_recovery.py",
        ],
        env=sub_env,
    )

    print("==> [test:langchain-deck] Running safe live-provider boundary checks...")
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{live_lab_dir}/test_live_agent.py",
        ],
        env=sub_env,
    )
    no_key_env = build_env(unset_virtual_env=True, extra_unset=("OPENAI_API_KEY",))
    live_gate = run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            f"{live_lab_dir}/live_agent.py",
            "--model",
            "dummy-model",
        ],
        env=no_key_env,
        check=False,
        capture_output=True,
    )
    if live_gate.returncode == 0:
        print("Error: live_agent.py succeeded without --execute.", file=sys.stderr)
        raise SystemExit(1)
    live_gate_output = live_gate.stdout + live_gate.stderr
    if "No API call made." not in live_gate_output:
        print(
            f"Error: unexpected live gate output:\n{live_gate_output}", file=sys.stderr
        )
        raise SystemExit(1)

    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "--extra",
            "live",
            "python",
            "-c",
            "from langchain_openai import ChatOpenAI; assert callable(ChatOpenAI)",
        ],
        env=sub_env,
    )
    check_project(project_dir, base_env=env)
    print(
        "==> [test:langchain-deck] All offline LangChain learning slices and live safety checks validated."
    )


def run_langfuse_deck(env: Mapping[str, str], sub_env: Mapping[str, str]) -> None:
    project_dir = "decks/llmops-langfuse"
    print(
        "==> [test:langfuse-deck] Checking locked deck environment and textbook contracts..."
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            "-m",
            "compileall",
            "-q",
            f"{project_dir}/textbook",
        ],
        env=sub_env,
    )

    print(
        "==> [test:langfuse-deck] Checking installed Langfuse/OpenAI public API surface..."
    )
    run(
        [
            "uv",
            "run",
            "--project",
            project_dir,
            "--locked",
            "python",
            "-c",
            LANGFUSE_SURFACE_CHECK,
        ],
        env=sub_env,
    )

    chapter_tests = (
        "01-first-trace/test_first_trace.py",
        "02-trace-design/test_trace_design.py",
        "03-openai-integration/test_openai_integration.py",
        "04-scores/test_score_evidence.py",
        "05-datasets/test_dataset_case.py",
        "06-experiments/test_experiment_compare.py",
        "07-prompt-management/test_prompt_versioning.py",
        "08-evaluation-loop/test_release_gate.py",
    )
    for test_rel in chapter_tests:
        run(
            [
                "uv",
                "run",
                "--project",
                project_dir,
                "--locked",
                "python",
                f"{project_dir}/textbook/{test_rel}",
            ],
            env=sub_env,
        )

    check_project(project_dir, base_env=env)
    print(
        "==> [test:langfuse-deck] Locked SDK and textbook contract validation passed."
    )


def run_opentelemetry_deck(env: Mapping[str, str], sub_env: Mapping[str, str]) -> None:
    project_dir = "decks/systems-opentelemetry"
    print("==> [test:opentelemetry-deck] Validating locked core textbook evidence...")
    for pattern in ("test_first_trace.py", "test_textbook_examples.py"):
        run(
            [
                "uv",
                "run",
                "--project",
                project_dir,
                "--locked",
                "python",
                "-m",
                "unittest",
                "discover",
                "-s",
                f"{project_dir}/tests",
                "-p",
                pattern,
                "-v",
            ],
            env=sub_env,
        )
    check_project(project_dir, base_env=env)


def run_opentelemetry_acceptance(sub_env: Mapping[str, str]) -> None:
    print(
        "==> [test:opentelemetry-acceptance] Running Flask zero-code and OTLP/Collector end-to-end acceptance..."
    )
    run(
        [
            "uv",
            "run",
            "--project",
            "decks/systems-opentelemetry",
            "--locked",
            "python",
            "decks/systems-opentelemetry/tests/test_external_runtime.py",
        ],
        env=sub_env,
    )
    print("==> [test:opentelemetry-acceptance] External runtime acceptance passed.")


def _assert_scope(
    stdin_text: str,
    *,
    expected_targets: str,
    expected_otel: str,
    expected_reason_prefix: str | None = None,
    env: Mapping[str, str],
) -> None:
    result = run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "test.py"),
            "--ci-scope",
            "--stdin",
        ],
        env=env,
        capture_output=True,
        input_text=stdin_text,
    )
    lines = result.stdout.splitlines()
    if f"test_targets={expected_targets}" not in lines:
        print(
            f"CI scope mismatch: expected test_targets={expected_targets}\nGot:\n{result.stdout}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if f"otel_acceptance={expected_otel}" not in lines:
        print(
            f"CI scope mismatch: expected otel_acceptance={expected_otel}\nGot:\n{result.stdout}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if expected_reason_prefix is not None and not any(
        line.startswith(expected_reason_prefix) for line in lines
    ):
        print(
            f"CI scope mismatch: expected prefix '{expected_reason_prefix}'\nGot:\n{result.stdout}",
            file=sys.stderr,
        )
        raise SystemExit(1)


def run_scripts(env: Mapping[str, str]) -> None:
    print("==> [test:scripts] Checking Python script syntax and CI scope routing...")
    for script_path in sorted((REPO_ROOT / "scripts").glob("*.py")):
        py_compile.compile(str(script_path), doraise=True)

    # Rulesync projections must never be tracked after the migration.
    tracked = run(
        ["git", "ls-files", "--", *UNEXPECTED_TRACKED_PROJECTIONS],
        env=env,
        capture_output=True,
    )
    if tracked.stdout.strip():
        print(
            f"Unexpected tracked agent projections:\n{tracked.stdout}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    _assert_scope(
        "",
        expected_targets="smoke scripts",
        expected_otel="false",
        env=env,
    )
    _assert_scope(
        "docs/automation.md\n.rumdl.toml\n.rulesync/rules/overview.md\nrulesync.lock\ndecks/computer-science/README.md\n",
        expected_targets="smoke scripts",
        expected_otel="false",
        env=env,
    )
    _assert_scope(
        ".inbox/2026-11-18/review.md\n",
        expected_targets="smoke scripts",
        expected_otel="false",
        env=env,
    )
    _assert_scope(
        "decks/ai-langchain/playground/01-agent-loop/first_agent.py\n",
        expected_targets="smoke langchain-deck scripts",
        expected_otel="false",
        env=env,
    )
    _assert_scope(
        "decks/llmops-langfuse/README.md\ntools/dataset_generator/README.md\n",
        expected_targets="smoke dataset-generator langfuse-deck scripts",
        expected_otel="false",
        env=env,
    )
    _assert_scope(
        "decks/systems-opentelemetry/tests/test_first_trace.py\n",
        expected_targets="smoke opentelemetry-deck scripts",
        expected_otel="true",
        env=env,
    )
    _assert_scope(
        "docs/README.md\nmise.toml\n",
        expected_targets="all",
        expected_otel="true",
        env=env,
    )
    _assert_scope(
        "decks/unclassified-new-deck/lab.py\n",
        expected_targets="all",
        expected_otel="true",
        env=env,
    )
    _assert_scope(
        "unclassified-root-file.txt\n",
        expected_targets="all",
        expected_otel="true",
        env=env,
    )

    ls_files = run(
        ["git", "-c", "core.quotePath=false", "ls-files"],
        env=env,
        capture_output=True,
    )
    non_shared = [
        line
        for line in ls_files.stdout.splitlines()
        if line not in SHARED_INFRA_EXACT and not line.startswith(SHARED_INFRA_PREFIXES)
    ]
    _assert_scope(
        "\n".join(non_shared) + "\n",
        expected_targets="smoke dataset-generator langchain-deck openai-sdk-deck langfuse-deck opentelemetry-deck scripts",
        expected_otel="true",
        expected_reason_prefix="scope_reason=routed from ",
        env=env,
    )
    print("==> [test:scripts] Python script syntax and CI scope routing passed.")


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in {"-h", "--help"}:
        usage()
        return 0
    if args and args[0] == "--ci-scope":
        return handle_ci_scope(args)

    if args:
        requested = args
    else:
        ci_targets = os.environ.get("CI_TEST_TARGETS", "").strip()
        requested = ci_targets.split() if ci_targets else ["all"]

    flags = {
        "smoke": False,
        "dataset-generator": False,
        "langchain-deck": False,
        "openai-sdk-deck": False,
        "langfuse-deck": False,
        "opentelemetry-deck": False,
        "opentelemetry-acceptance": False,
        "scripts": False,
    }
    run_all = False

    for target in requested:
        if target == "all":
            run_all = True
            for key in (
                "smoke",
                "dataset-generator",
                "langchain-deck",
                "openai-sdk-deck",
                "langfuse-deck",
                "opentelemetry-deck",
                "scripts",
            ):
                flags[key] = True
        elif target in flags:
            flags[target] = True
        else:
            allowed = ", ".join(ALLOWED_TARGETS)
            print(
                f"Error: Unknown test target '{target}'. Allowed: {allowed}",
                file=sys.stderr,
            )
            return 1

    env = build_env()
    sub_env = build_env(unset_virtual_env=True)

    if flags["smoke"]:
        run_smoke(env)
    if flags["dataset-generator"]:
        run_dataset_generator(env, sub_env)
    if flags["langchain-deck"]:
        run_langchain_deck(env, sub_env)
    if flags["openai-sdk-deck"]:
        run_openai_sdk_deck(env, sub_env)
    if flags["langfuse-deck"]:
        run_langfuse_deck(env, sub_env)
    if flags["opentelemetry-deck"]:
        run_opentelemetry_deck(env, sub_env)
    if flags["opentelemetry-acceptance"]:
        run_opentelemetry_acceptance(sub_env)
    if flags["scripts"]:
        run_scripts(env)

    if run_all:
        print("==> All test suites passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
