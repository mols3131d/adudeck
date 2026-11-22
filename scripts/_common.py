"""Shared cross-platform helpers for repository automation scripts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _set_env_var(env: dict[str, str], key: str, value: str) -> None:
    if os.name == "nt":
        key_lower = key.lower()
        for existing in list(env):
            if existing.lower() == key_lower:
                del env[existing]
    env[key] = value


def _unset_env_var(env: dict[str, str], key: str) -> None:
    if os.name == "nt":
        key_lower = key.lower()
        for existing in list(env):
            if existing.lower() == key_lower:
                del env[existing]
    else:
        env.pop(key, None)


def _path_value(env: Mapping[str, str]) -> str | None:
    if "PATH" in env:
        return env["PATH"]
    if os.name == "nt":
        for key, value in env.items():
            if key.lower() == "path":
                return value
    return None


def build_env(
    *,
    load_mise: bool = True,
    unset_virtual_env: bool = False,
    extra_unset: Sequence[str] = (),
) -> dict[str, str]:
    """Return a copy of the process environment, optionally augmented with mise."""
    env = dict(os.environ)
    if load_mise:
        mise_bin = shutil.which("mise", path=_path_value(env))
        if mise_bin is not None:
            result = subprocess.run(
                [mise_bin, "env", "--json"],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(key, str) and isinstance(value, str):
                            _set_env_var(env, key, value)
    if unset_virtual_env:
        _unset_env_var(env, "VIRTUAL_ENV")
    for key in extra_unset:
        _unset_env_var(env, key)
    return env


def resolve_executable(program: str, env: Mapping[str, str]) -> str:
    """Resolve an executable name against env PATH (including Windows PATHEXT)."""
    if (
        Path(program).is_absolute()
        or os.sep in program
        or (os.altsep and os.altsep in program)
    ):
        return program
    return shutil.which(program, path=_path_value(env)) or program


def run(
    args: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path = REPO_ROOT,
    check: bool = True,
    capture_output: bool = False,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command with structured argv and cross-platform executable lookup."""
    effective_env = dict(os.environ) if env is None else dict(env)
    argv = [resolve_executable(args[0], effective_env), *args[1:]]
    result = subprocess.run(
        argv,
        cwd=cwd,
        env=effective_env,
        capture_output=capture_output,
        text=True,
        encoding="utf-8",
        input=input_text,
        check=False,
    )
    if check and result.returncode != 0:
        if capture_output:
            if result.stdout:
                sys.stdout.write(result.stdout)
            if result.stderr:
                sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return result


def locked_subprojects() -> list[Path]:
    """Return active locked Python subprojects relative to REPO_ROOT."""
    projects: list[Path] = []
    for base in ("tools", "decks"):
        base_dir = REPO_ROOT / base
        if not base_dir.is_dir():
            continue
        for child in sorted(base_dir.iterdir()):
            if not child.is_dir():
                continue
            if base == "decks" and child.name.startswith("_"):
                continue
            if (child / "pyproject.toml").is_file() and (child / "uv.lock").is_file():
                projects.append(child.relative_to(REPO_ROOT))
    return projects
