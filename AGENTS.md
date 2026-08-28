Please also reference the following rules as needed. The list below is provided in TOON format, and `@` stands for the project root directory.

rules[3]:
  - path: @decks/_archive/AGENTS.md
    description: Rules for inactive decks with no current planned work.
    applyTo[1]: decks/_archive/**/*
  - path: @decks/_backlog/AGENTS.md
    description: Rules for decks with intended follow-up work that is not currently active.
    applyTo[1]: decks/_backlog/**/*
  - path: @decks/AGENTS.md
    description: Rules for learning decks and their state.
    applyTo[1]: decks/**/*

# Additional Conventions Beyond the Built-in Functions

As this project's AI coding tool, you must follow the additional conventions below, in addition to the built-in functions.

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

## Authority

- `.rulesync/` is the canonical source for portable agent Rules and Skills managed by Rulesync.
- `rulesync.jsonc` selects the repository-shared targets used for generated projections.
- `rulesync.local.jsonc` must remain untracked. If it defines `targets`, it replaces the shared target set, so include
  the shared targets alongside any local additions.
- `mise.toml` installs the repository toolchain and exposes repeatable Rulesync tasks.
- Treat generated vendor-native agent files as derived artifacts; change the canonical `.rulesync/` source instead.
- Prefer the `mise run rulesync:*` tasks for repository-wide Rulesync operations when mise is available.
- Generated Skills are local-only projections and must remain untracked; commit only generated projections that the
  repository explicitly keeps tracked.
- Generate from canonical source after agent asset changes; CI detects drift only for tracked projections in the
  resulting Git tree.

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
