"""Explicitly update repository tool pins, Python locks, hooks, and agent projections."""

from __future__ import annotations

import shutil
import sys

from _common import build_env, locked_subprojects, run


def main() -> int:
    if shutil.which("mise") is None:
        print(
            "Error: 'mise' is required to update the repository toolchain.",
            file=sys.stderr,
        )
        return 1

    print("==> [update] Updating Python within the repository-supported 3.14 series...")
    run(["mise", "use", "--pin", "python@3.14"])

    print("==> [update] Updating other repository-local tool pins with mise...")
    run(["mise", "upgrade", "--bump", "--local", "--exclude", "python"])
    env = build_env()
    sub_env = build_env(unset_virtual_env=True)

    print("==> [update] Updating root Python dependencies and lockfile...")
    run(["uv", "lock", "--upgrade"], env=env)
    run(["uv", "sync", "--locked"], env=env)

    for project in locked_subprojects():
        project_posix = project.as_posix()
        print(f"==> [update] Updating {project_posix} dependencies and lockfile...")
        run(["uv", "lock", "--upgrade", "--project", project_posix], env=sub_env)
        run(["uv", "sync", "--project", project_posix, "--locked"], env=sub_env)

    print(
        "==> [update] Explicitly refreshing external Rulesync assets and local projections..."
    )
    run(["mise", "run", "rulesync:refresh"], env=env)

    print("==> [update] Refreshing git hooks with lefthook...")
    run(["lefthook", "install"], env=env)

    print("==> Environment update successfully completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
