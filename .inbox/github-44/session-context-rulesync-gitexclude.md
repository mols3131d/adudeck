# Session Context — Rulesync, Git Exclude, and PR #44

Date: 2026-11-22

## Decisions and rationale

The workspace should no longer maintain a special ChatGPT compatibility harness. Portable Rules and Skills
are managed by Rulesync, while the repository's own `AGENTS.md` remains a minimal checked-in bootstrap.
This keeps learning-deck policies independent of a specific conversational runtime.

Antigravity may skip agent assets excluded by `.gitignore`. Therefore the chosen native Rulesync mechanism
is `gitignoreDestination: "gitexclude"`, writing generated-asset exclusions to Git's local
`info/exclude`. Local generation remains necessary after cloning because that exclude file is not versioned.

Project script design should favor `mise` entrypoints and native tooling rather than duplicate wrappers.
The decision was informed by these public sources, not copied verbatim:

- [Repository template](https://github.com/mols3131d/new-repository-template) — Rulesync `gitexclude`,
  task entrypoints, and agent-asset lifecycle.
- [Agent Assets repository](https://github.com/mols3131d/mols-agent-assets) — task/command design,
  bootstrap boundaries, and agent-asset ownership.
- [Adudeck PR #44](https://github.com/mols3131d/adudeck/pull/44) — actual implementation and review record.

## PR implementation timeline

1. Initial change: target-scoped Rulesync configuration, generated asset untracking, chatbot route removal,
   setup/update simplification, and updated docs.
2. First GitHub Actions validation surfaced unintended deletion of the tracked root `AGENTS.md` by
   Rulesync's stale-output deletion. The former CI auto-fix workflow committed that deletion.
3. Repair: restore `AGENTS.md`, use `"delete": false`, replace CI auto-commit/push with read-only
   formatting and tracked-source drift checks.
4. Follow-up formatting fixes passed the final checked CI at
   `c4e37142e21b02629e334fab0943d6879835d2f3`
   ([run](https://github.com/mols3131d/adudeck/actions/runs/45025309533)).
5. A branch synchronization check found `main` at
   `b9ea2b051d365ababab89ece5f6b9dfdfda7c98e`, which is already an ancestor of the PR branch
   (5 commits ahead, 0 behind). No merge/rebase was performed.

The user then requested two `.inbox/` records: a local-agent handoff and this session-context note.
The note-creation commit is subsequent to the CI-validated SHA above and requires its own latest-HEAD review.

## Files and state boundaries

- `rulesync.jsonc` — native target/feature selection, external source reference,
  `gitignoreDestination: gitexclude`, and `delete: false`.
- `rulesync.lock` — pinned external Skill revision/integrity selection.
- `.rulesync/rules/` and `.rulesync/skills/` — portable canonical authoring.
- Root `AGENTS.md` — tracked repository guidance, not generated.
- `.git/info/exclude` — non-versioned local generated-artifact exclusions.
- `mise.toml` — `rulesync:doctor`, `rulesync:generate`, `rulesync:check`, and
  `rulesync:refresh` task entrypoints.
- `scripts/setup.sh` / `scripts/update.sh` — call the shared Rulesync tasks.
- `.github/workflows/ci.yml` — checks without automatic commits.
- `.inbox/` — temporary non-canonical working context; see `.inbox/README.md`.

## What is verified vs. outstanding

Verified on the prior PR HEAD: GitHub Actions ran formatting, Rulesync local exclude + frozen generation,
projection validation, repository tests, OpenTelemetry external-runtime acceptance, and a clean tracked-source
check. The CI status was successful.

Outstanding: representative Antigravity IDE/CLI discovery/activation evidence, review of the latest PR HEAD
after the handoff commit, and any genuinely needed correction revealed by that runtime test.
The large-scale script restructuring is a separate prospective task, **not** already delivered.

## Continuation rule

Start from current GitHub refs, effective repository guidance, and PR/CI status. Use the companion handoff
note for bounded next steps. Do not assume this record is up to date after further commits; authoritative
sources and observable runtime behavior take precedence. Do not merge or rewrite history as an implicit
step of documentation or local testing.
