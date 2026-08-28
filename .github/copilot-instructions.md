# Repository Contract

## Required Context

- Before substantive repository work, read `docs/VISON.md` completely and follow its workspace and learning principles.
- For deck storage, state, naming, or content-boundary decisions, follow `docs/decks.md`.

## Storage

- Default to filesystem deck storage under this repository's `decks/`.
- Use another storage only when the user explicitly identifies or requests it for the current deck or task.
- Do not infer, migrate, mirror, split, or synchronize a deck across storages without explicit instruction.

## Authority

- `.rulesync/` is the canonical source for portable agent Rules and Skills managed by Rulesync; generated vendor-native
  files are derived artifacts.
- `rulesync.jsonc` owns the shared projection targets. Keep `rulesync.local.jsonc` untracked; if it defines `targets`,
  include the shared targets because the local list replaces them.
- Prefer `mise run rulesync:*` for repository-wide Rulesync operations when available.
- Generated Skills are local-only and untracked. After canonical agent-asset changes, regenerate projections; CI detects
  drift only in tracked generated files.

## Safety

Anything recorded in Git or GitHub may remain accessible after change or deletion.

- Do not record unsafe content first and plan to sanitize, delete, rewrite, or history-edit it later.
- Before recording files, commits, branches, PRs, issues, comments, logs, artifacts, or uploads, check secrets and
  confidential information, copyright/license and attribution requirements, and access or redistribution restrictions.
- Keep raw research, copied source material, and temporary content outside Git/GitHub until those checks pass. If
  required permission or safety cannot be determined, do not record it.

## Development

- Do not commit ordinary change work directly to `main`.
- Keep repository guidance concise and colocated with its real responsibility.
