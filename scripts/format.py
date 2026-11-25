"""Format or check repository-owned Markdown, Python, JSON/JSONC, and TOML files."""

from __future__ import annotations

import argparse
import sys

from _common import build_env, run


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scripts/format.py",
        description="Format or check repository-owned text formats.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check formatting and lint without modifying files.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    env = build_env()

    if args.check:
        print("==> [format:check] Checking Markdown formatting...")
        run(["rumdl", "fmt", "--check", "."], env=env)

        print("==> [format:check] Checking Python formatting and lint...")
        run(["ruff", "format", "--check", "."], env=env)
        run(["ruff", "check", "."], env=env)

        print("==> [format:check] Checking JSON / JSONC formatting and lint...")
        run(["biome", "check", "."], env=env)

        print("==> [format:check] Checking TOML formatting and lint...")
        run(["tombi", "format", "--check", "."], env=env)
        run(["tombi", "lint", "--error-on-warnings", "."], env=env)

        print("==> All format checks passed.")
    else:
        print("==> [format] Formatting Markdown...")
        run(["rumdl", "fmt", "."], env=env)

        print("==> [format] Formatting and linting Python...")
        run(["ruff", "check", "--fix", "."], env=env)
        run(["ruff", "format", "."], env=env)
        run(["ruff", "check", "."], env=env)

        print("==> [format] Formatting and checking JSON / JSONC...")
        run(["biome", "format", "--write", "."], env=env)
        run(["biome", "check", "."], env=env)

        print("==> [format] Formatting and linting TOML...")
        run(["tombi", "format", "."], env=env)
        run(["tombi", "lint", "--error-on-warnings", "."], env=env)

        print("==> Formatting complete.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
