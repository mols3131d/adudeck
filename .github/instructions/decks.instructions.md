---
description: Rules for learning decks and their lifecycle.
applyTo: decks/**/*
---

# Deck Rules

Apply only to work under `decks/`.

- Treat each directory directly under `decks/`, except `archive/`, as an active learning deck.
- Keep a deck self-contained and focused on its learning scope.
- Prefer relative links within a deck so moving it between active and archive locations preserves internal references.
- Do not create new decks or taxonomy layers without a concrete learning need.
- Move a deck to `decks/archive/` when it is no longer active.
- Treat content under `decks/archive/` as inactive and defer archive-specific behavior to the archive rule.