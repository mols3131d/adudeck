---
root: true
description: Repository-wide contract for the adudeck agentic learning workspace.
---

# Repository Contract

## Purpose

- `adudeck` is a personal agentic learning workspace organized as a monorepo of decks.
- The workspace itself is the learning platform. Do not assume or introduce an application product unless explicitly
  requested.
- Prefer small, reversible structures with a current responsibility. Avoid speculative directories and abstractions.

## Authority

- `.agentsmesh/` is the canonical source for portable agent Rules and Skills managed by AgentsMesh.
- `agentsmesh.yaml` selects active targets and features.
- `mise.toml` pins repository bootstrap tools and exposes repeatable repository tasks.
- Treat generated vendor-native agent files as derived artifacts; change the canonical `.agentsmesh/` source instead.
- Use the AgentsMesh version pinned by the schema directive in `agentsmesh.yaml`; upgrade it intentionally before
  regenerating outputs.
- Prefer the `mise run agents:*` tasks for repository-wide AgentsMesh operations when mise is available.
- When AgentsMesh generation is used, commit the generated lock file and target outputs with the canonical change so
  drift remains reviewable.

## Learning

- Teach from fundamentals and make important prerequisites explicit.
- Prefer concrete examples and clear explanations over unnecessary jargon.

## Language

- Use natural Korean for prose by default. Keep technical terms, APIs, code, and standard names in English when that is
  clearer or more precise.

## Development

- Do not commit ordinary change work directly to `main`.
- Keep repository guidance concise and colocated with its real responsibility.
