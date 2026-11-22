"""Run static Python type checks with ty across the root and active subprojects."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Mapping
from pathlib import Path

from _common import REPO_ROOT, build_env, locked_subprojects, run


def check_project(target: str, *, base_env: Mapping[str, str] | None = None) -> None:
    if target in {".", "root"}:
        env = build_env() if base_env is None else dict(base_env)
        print("==> [typecheck] Checking root project...")
        run(["ty", "check"], env=env)
        return

    project_path = (REPO_ROOT / target).resolve()
    if not (project_path / "pyproject.toml").is_file():
        print(f"Error: '{target}' does not contain a pyproject.toml.", file=sys.stderr)
        raise SystemExit(2)

    sub_env = (
        build_env(unset_virtual_env=True)
        if base_env is None
        else {k: v for k, v in base_env.items() if k.lower() != "virtual_env"}
    )
    display_target = Path(target).as_posix()
    print(f"==> [typecheck] Checking {display_target}...")
    run(["ty", "check", "--project", str(project_path)], env=sub_env)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scripts/typecheck.py",
        description="Run ty type checks for the root and active Python projects.",
    )
    parser.add_argument(
        "targets",
        nargs="*",
        help="Optional project directory paths (or '.' / 'root'). Defaults to all active projects.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    base_env = build_env()

    if args.targets:
        for target in args.targets:
            check_project(target, base_env=base_env)
    else:
        check_project(".", base_env=base_env)
        for project in locked_subprojects():
            check_project(project.as_posix(), base_env=base_env)

    print("==> All type checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
