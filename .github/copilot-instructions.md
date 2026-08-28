# Repository Contract

## Required Context

- Before substantive repository work, read `docs/VISON.md` completely and follow its workspace and learning principles.
- For deck storage, state, naming, or content-boundary decisions, follow `docs/decks.md`.

## Storage

- Default to filesystem deck storage under this repository's `decks/`.
- Use another storage only when the user explicitly identifies or requests it for the current deck or task.
- Do not infer, migrate, mirror, split, or synchronize a deck across storages without explicit instruction.

## Authority

- `.rulesync/` is the canonical source for portable agent Rules and Skills; generated vendor-native files are derived
  artifacts and must not be edited as independent owners.
- For Agent Asset or Rulesync work, read `.rulesync/README.md` and prefer its `mise run rulesync:*` workflow.

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
