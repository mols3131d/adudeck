# Rulesync

`.rulesync/` owns portable scoped Rules and task-selected Skills. The checked-in root `AGENTS.md` owns repository-wide
guidance; it is not a Rulesync projection. Generated native rule/skill files stay local and are not checked into Git.

## Sources and generated outputs

- `.rulesync/rules/` — canonical scoped Rules; Rulesync generates supported native scoped instructions.
- `.rulesync/skills/` — canonical local Skills; external selection lives in `rulesync.jsonc`.
- `rulesync.lock` — committed external Skill revision and integrity selection.
- Native projections under `.agents/`, `.github/`, `.claude/`, `.codex/`, and scoped `AGENTS.md` are generated, not
  independently edited.

Rulesync writes generated path exclusions to Git's local `info/exclude`, **not** `.gitignore`. Antigravity does not load
agent assets when their paths are ignored by `.gitignore`. `info/exclude` is not committed or copied by Git clone; every
checkout must initialize it before generating any files.

## Commands

```bash
mise run rulesync:doctor    # read-only configuration diagnostics
mise run rulesync:generate  # set up local Git excludes, restore frozen Skills and generate
mise run rulesync:check     # read-only drift check, after generate
mise run rulesync:refresh   # explicitly update upstream Skill revisions and regenerate
```

The first command in generation/refresh is `rulesync gitignore`, so native projections cannot accidentally become
untracked candidates for a later `git add -A`. `rulesync install --frozen` restores from the committed lock without
updating revisions. Only `rulesync:refresh` intentionally updates them.

`rulesync.jsonc` disables automatic stale-output deletion: otherwise `rulesync generate` removes the checked-in root `AGENTS.md` when no root rule exists. Retire unused target outputs explicitly after reviewing their paths.

Do not run `git add -f` on generated paths. A local exclusion does not untrack files that are already in Git's index;
migration must explicitly remove previously tracked native projections. Avoid introducing additional custom projection
generators or chatbot routing shims.
