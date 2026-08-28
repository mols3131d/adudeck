#!/usr/bin/env python3
"""Normalize and verify the repository's generated AGENTS.md projection."""

from __future__ import annotations

import argparse
import difflib
import subprocess
import tempfile
from pathlib import Path

REFERENCE_PREFIX = "Please also reference the following rules as needed."
CONTENT_MARKER = "# Additional Conventions Beyond the Built-in Functions"


def normalized(content: str) -> str:
    """Remove only the Rulesync-injected nested-AGENTS discovery preamble."""
    if not content.startswith(REFERENCE_PREFIX):
        return content

    marker = content.find(CONTENT_MARKER)
    if marker < 0:
        raise RuntimeError(
            "AGENTS.md contains the Rulesync discovery preamble but its expected content marker is missing"
        )

    prefix = content[:marker]
    if "AGENTS.md" not in prefix or "rules[" not in prefix:
        raise RuntimeError("Refusing to remove an unrecognized AGENTS.md preamble")

    return content[marker:].lstrip()


def normalize_file(path: Path) -> bool:
    before = path.read_text(encoding="utf-8")
    after = normalized(before)
    if before == after:
        return False
    path.write_text(after, encoding="utf-8")
    return True


def projection_text(content: str) -> str:
    """Ignore only terminal line-ending differences in generated Markdown."""
    return content.rstrip("\r\n")


def compare_projection(repo: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="adudeck-agents-") as tmp:
        output = Path(tmp)
        subprocess.run(
            [
                "rulesync",
                "generate",
                "--targets",
                "agentsmd",
                "--features",
                "rules",
                "--output-roots",
                str(output),
            ],
            cwd=repo,
            check=True,
        )

        generated_root = output / "AGENTS.md"
        if not generated_root.is_file():
            raise RuntimeError("Rulesync did not generate root AGENTS.md")
        normalize_file(generated_root)

        generated = sorted(output.rglob("AGENTS.md"))
        failed = False
        for candidate in generated:
            relative = candidate.relative_to(output)
            tracked = repo / relative
            if not tracked.is_file():
                print(f"missing tracked projection: {relative}")
                failed = True
                continue

            expected = candidate.read_text(encoding="utf-8")
            actual = tracked.read_text(encoding="utf-8")
            if projection_text(expected) == projection_text(actual):
                continue

            print(f"projection drift: {relative}")
            print(
                "".join(
                    difflib.unified_diff(
                        actual.splitlines(keepends=True),
                        expected.splitlines(keepends=True),
                        fromfile=str(relative),
                        tofile=f"generated/{relative}",
                    )
                ),
                end="",
            )
            failed = True

        return 1 if failed else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Generate a temporary agentsmd projection, normalize it, and compare it with tracked AGENTS.md files.",
    )
    args = parser.parse_args()

    repo = Path.cwd().resolve()
    if args.check:
        return compare_projection(repo)

    root = repo / "AGENTS.md"
    if not root.is_file():
        raise RuntimeError("root AGENTS.md does not exist")
    normalize_file(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
