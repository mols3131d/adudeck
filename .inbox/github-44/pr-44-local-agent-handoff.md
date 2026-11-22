# PR #44 — Local Agent Handoff

Date: 2026-11-22

## Target and current status

Continue [PR #44](https://github.com/mols3131d/adudeck/pull/44) on
`refactor/rulesync-gitexclude-local-projections`. It remains a **draft**; do not merge as part of the handoff.
Before this note was committed, the PR head was `c4e37142e21b02629e334fab0943d6879835d2f3` and `main` was
`b9ea2b051d365ababab89ece5f6b9dfdfda7c98e`. GitHub compare reported the branch **5 commits ahead,
0 behind** `main`; no integration commit or rebase was needed. Resolve the *current* refs again before further work.

The change has passed [GitHub Actions CI](https://github.com/mols3131d/adudeck/actions/runs/45025309533) at
`c4e37142e21b02629e334fab0943d6879835d2f3`. This is not proof of Antigravity IDE/CLI runtime activation or of any newer
commit.

## Goal and ownership

- Keep the root `AGENTS.md` tracked as repository-wide guidance.
- Keep scoped Rules and Skills canonical in `.rulesync/`; declare their native targets in `rulesync.jsonc`.
- Generate native agent assets locally, excluded from Git through Rulesync-managed `.git/info/exclude`, **not**
  via generated-path patterns in `.gitignore` (important for Antigravity discovery).
- Retire ChatGPT-only `CHATBOT.md`, `.agents/route/`, and custom route/root-AGENTS generators.
- Keep `mise` as the public task entrypoint and avoid redundant install/generation scripts.

Canonical references: `AGENTS.md`, `.rulesync/README.md`, `rulesync.jsonc`, `mise.toml`, and
`docs/automation.md`. This inbox note is **working context only**; it does not override those files.

## Implemented in the PR

The branch changed Rulesync target selection, stopped tracking generated scoped `AGENTS.md` and Copilot
instructions, removed ChatGPT-specific routing, and simplified the Rulesync calls in `scripts/setup.sh`,
`scripts/update.sh`, and `mise.toml`. The GitHub Actions workflow no longer auto-commits fixes.
`rulesync.jsonc` uses `"gitignoreDestination": "gitexclude"` and `"delete": false`.

A real CI regression initially removed the tracked root `AGENTS.md` under automatic stale-output deletion.
The root file was restored and `delete: false` was introduced. The earlier CI workflow also created a
`github-actions[bot]` auto-fix commit before automatic commits were removed; **do not rewrite that history**.

## Local agent next actions

1. Resolve the current branch and `main` refs; load the effective root/scoped guidance and relevant Skills.
   Respect unrelated local work. Verify that PR #44 still targets `main` and its diff matches the goal.
2. In a suitable authorized local checkout, run `mise run rulesync:doctor`,
   `mise run rulesync:generate`, and `mise run rulesync:check`. Generation must first configure
   local Git excludes, then restore frozen external Skills and generate projections.
3. Confirm `AGENTS.md` remains byte-for-byte tracked and unchanged after generation. Inspect
   `git status --short`, `git ls-files`, and `git check-ignore -v --no-index` for actual generated
   agent files. Confirm generated assets are not tracked; do not force-add them.
4. In **Antigravity IDE and/or CLI actually available**, test native Rule and Skill discovery using a
   representative applicable task. Record the runtime, its observed loaded path/content, task result,
   and evidence level: configured, reachable, or observed applied. A successful CLI projection check
   alone does not prove runtime loading. State which runtimes could not be tested.
5. Execute applicable repository checks (`mise run format:check`, `mise run test scripts`, broader
   checks when warranted). Inspect the final diff and GitHub Actions for the **latest** HEAD.
6. If a real blocking defect appears, repair the smallest canonical owner and recheck. Update the PR
   checklist and `Reviewed HEAD` **only after reviewing that exact current commit**. Leave the PR
   draft and unmerged unless a later authorized task explicitly changes that scope.

## Risks and boundaries

- `.git/info/exclude` is clone-local. Every new checkout needs the `rulesync gitignore` bootstrap
  before generating or staging assets.
- Exclude patterns do not remove already-tracked files; the PR explicitly removes old projections
  from the Git tree. Previously published Git history remains unchanged.
- `delete: false` protects the tracked root guidance but requires deliberate retirement of stale
  projections. Never broadly delete unknown local/user files.
- CI at `c4e37142e21b02629e334fab0943d6879835d2f3` passed formatting, Rulesync generation/check, project tests, and
  OpenTelemetry acceptance. Runtime activation of Antigravity is still **unverified**.
- A broader `scripts/test.sh` and environment update redesign was discussed but is not completed by
  this PR; avoid silent scope expansion.

Do not treat this note, prior chat assertions, or a successful check on an older SHA as current authority.
