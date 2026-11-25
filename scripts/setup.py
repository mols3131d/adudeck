"""Set up the local adudeck workspace from pinned tool and dependency locks."""

from __future__ import annotations

import shutil
import sys

from _common import build_env, locked_subprojects, run


def main() -> int:
    if shutil.which("mise") is None:
        print(
            "Error: 'mise' must be installed before setting up this repository.",
            file=sys.stderr,
        )
        return 1

    print("==> [setup] Installing repository toolchain with mise...")
    run(["mise", "install"])
    env = build_env()
    sub_env = build_env(unset_virtual_env=True)

    print("==> [setup] Syncing root Python environment with uv...")
    run(["uv", "sync", "--locked"], env=env)

    for project in locked_subprojects():
        project_posix = project.as_posix()
        print(f"==> [setup] Syncing {project_posix} environment with uv...")
        run(["uv", "sync", "--project", project_posix, "--locked"], env=sub_env)

    print("==> [setup] Configuring git commit template...")
    in_repo = run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        env=env,
        check=False,
        capture_output=True,
    )
    if in_repo.returncode == 0:
        run(["git", "config", "--local", "commit.template", ".gitmessage"], env=env)

    print("==> [setup] Installing git hooks with lefthook...")
    run(["lefthook", "install"], env=env)

    print(
        "==> [setup] Restoring Rulesync dependencies and generating excluded local agent assets..."
    )
    run(["mise", "run", "rulesync:generate"], env=env)

    print("==> Environment setup successfully completed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
