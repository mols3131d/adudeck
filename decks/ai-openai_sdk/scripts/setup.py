#!/usr/bin/env python3

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

MIN_PYTHON = (3, 10)
DECK_ROOT = Path(__file__).resolve().parent.parent
PROJECT_FILE = DECK_ROOT / "pyproject.toml"
LOCK_FILE = DECK_ROOT / "uv.lock"
FIRST_PLAYGROUND = DECK_ROOT / "textbook" / "01-client-request-response" / "request_response.py"


def main() -> int:
    ok = True

    current = sys.version_info[:2]
    if current < MIN_PYTHON:
        print(f"[fail] Python 3.10+ required; found {current[0]}.{current[1]}")
        ok = False
    else:
        print(f"[ok] Python {current[0]}.{current[1]}")

    uv = shutil.which("uv")
    if uv is None:
        print("[fail] uv not found in PATH")
        ok = False
    else:
        print(f"[ok] uv: {uv}")

    if PROJECT_FILE.is_file():
        print(f"[ok] deck project: {PROJECT_FILE}")
    else:
        print(f"[fail] missing project file: {PROJECT_FILE}")
        ok = False

    if LOCK_FILE.is_file():
        print(f"[ok] deck lockfile: {LOCK_FILE}")
    else:
        print(f"[fail] missing lockfile: {LOCK_FILE}")
        ok = False

    if os.getenv("OPENAI_API_KEY"):
        print("[ok] OPENAI_API_KEY is set")
    else:
        print("[fail] OPENAI_API_KEY is not set")
        ok = False

    if FIRST_PLAYGROUND.is_file():
        print(f"[ok] first playground: {FIRST_PLAYGROUND}")
    else:
        print(f"[fail] missing playground: {FIRST_PLAYGROUND}")
        ok = False

    if ok:
        print("\nReady:")
        print("  uv sync --locked")
        print("  uv run textbook/01-client-request-response/request_response.py")
        return 0

    print("\nFix the failed checks, then run this script again.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
