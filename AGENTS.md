# Repository Contract

## Purpose

- `adudeck` is a personal agentic learning workspace. This repository is its default filesystem workspace and canonical
  home for repository-managed policies and agent assets.
- The workspace itself is the learning platform. Do not assume or introduce an application product unless explicitly
  requested.
- Prefer small, reversible structures with a current responsibility. Avoid speculative directories and abstractions.

## Storage

- Default to filesystem deck storage under this repository's `decks/`.
- Use another storage only when the user explicitly identifies or requests it for the current deck or task.
- Do not infer, migrate, mirror, split, or synchronize a deck across storages without explicit instruction.
- Preserve a deck as one cohesive learning workspace unit regardless of storage.
- For Notion deck storage, follow `docs/notion.md` and represent deck state through properties rather than filesystem
  paths.

## Authority

- `.rulesync/` is the canonical source for portable agent Rules and Skills managed by Rulesync.
- `rulesync.jsonc` selects repository-shared targets and features whose generated outputs are tracked in Git.
- `rulesync.local.jsonc` may override generation for local tools and must remain untracked.
- `mise.toml` installs the repository toolchain and exposes repeatable Rulesync tasks.
- Treat generated vendor-native agent files as derived artifacts; change the canonical `.rulesync/` source instead.
- Prefer the `mise run rulesync:*` tasks for repository-wide Rulesync operations when mise is available.
- Commit outputs selected by the shared `rulesync.jsonc`; keep local-only projections untracked.
- Generate from canonical source after agent asset changes; CI detects tracked projection drift from the resulting Git
  tree.

## Safety

Anything recorded in Git or GitHub may remain accessible after it is changed or deleted.

- Apply these rules to intermediate, generated, and final content, including AI-generated content.
- Do not record content in Git or GitHub first and plan to remove, rewrite, or sanitize it later.
- Do not rely on file deletion, history rewriting, force-push, branch deletion, PR closure, or retention expiry to
  remove content that fails the checks below.
- These rules apply to files, commits, commit messages, branches, pull requests, issues, comments, uploads, CI logs, and
  CI artifacts.
- Keep raw research, copied source material, and other temporary content outside Git and GitHub unless it passes the
  checks below.
- Before recording content, check copyright and license restrictions, required attribution, personal or confidential
  information, secrets or credentials, and access or redistribution restrictions.
- If you cannot determine that required permission exists or that these checks pass, do not record the content in Git
  or GitHub.

## Learning

- Teach from fundamentals and make important prerequisites explicit.
- Prefer concrete examples and clear explanations over unnecessary jargon.

## Language

- Use natural Korean for prose by default. Keep technical terms, APIs, code, and standard names in English when that is
  clearer or more precise.

## Development

- Do not commit ordinary change work directly to `main`.
- Keep repository guidance concise and colocated with its real responsibility.

# Archive Rules

Apply only to work under `decks/_archive/`.

- Treat archived decks as inactive material with no current planned work, not as permanently finished content.
- Preserve archived content unless cleanup is explicitly requested.
- When follow-up work becomes intended, move the deck to `_backlog/` or directly to the active location instead of
  creating a second copy.

# Backlog Rules

Apply only to work under `decks/_backlog/`.

- Treat backlog decks as inactive for now but carrying explicit intent for future study, supplementation, or change.
- Do not assume a backlog deck is new or never studied; it may have moved from active or archive.
- When the work becomes current, move the deck to the active location instead of creating a second copy.

# Deck Rules

Apply only to work under `decks/`.

- Treat each directory directly under `decks/` that does not start with `_` as an active learning deck.
- Treat `_backlog/` and `_archive/` as management namespaces, not decks.
- Keep a deck self-contained and focused on its learning scope.
- Prefer relative links within a deck so moving it between state locations preserves internal references.
- Do not create new decks or management namespaces without a concrete learning need.
- Move the whole deck directory when its state changes; do not keep copies in multiple states.
- Defer `_backlog/` and `_archive/` behavior to their state-specific rules.
