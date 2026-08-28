---
name: adudeck-deck-curriculum
description: >-
  Design, revise, or audit one deck's internal curriculum as a learning contract. Use for deck
  learning scope, learner prerequisites, learning outcomes, concept dependencies, unit sequence,
  chapter or unit architecture, outcome coverage, or curriculum changes discovered during
  learning-material work. Own the deck curriculum baseline and its deltas; do not own workspace
  curriculum metadata, textbook prose, playground experiments, storage, or deck build orchestration.
targets: ["claudecode", "codexcli", "copilot", "copilotcli", "antigravity-ide", "antigravity-cli"]
---

# Adudeck Deck Curriculum

## Contract

Own **what one deck teaches and in what conceptual order**.

A deck curriculum is an internal learning contract, not merely a table of contents. Keep an
inspectable baseline:

```text
Deck Curriculum Baseline
- Goal / learner assumptions
- Learning scope / out of scope
- Learner prerequisites
- Learning outcomes
- Concept dependencies
- Sequence / unit responsibilities
- Outcome development and assessment coverage
- Material version / authority assumptions, when relevant
```

`Learning scope` is the deck's content boundary, distinct from the execution `Active Scope` owned by
`mols-rpi`; changing one does not silently change the other.

Own where outcomes are developed or assessed, not individual assessment design. Do not write
textbook prose, exercises, assessments, or playground artifacts; choose storage or publishing; or
create chapter files merely because an architecture exists. Use `adudeck-deck-build` to implement an
accepted baseline.

Treat an accepted baseline as state. Do not silently change learner prerequisites, learning scope,
outcomes, sequence, unit responsibility, or a material version boundary because downstream work
becomes inconvenient.

For deck work that will continue across sessions or review increments, keep the accepted baseline
recoverable from the established workspace rather than only from chat memory. Prefer an existing deck
overview surface when one already carries goal, prerequisites, scope, or learning path; do not create
a mandatory planning manifest when the existing structure is sufficient.

## Workspace Curriculum Boundary

The deck curriculum baseline is intra-deck. Workspace curriculum/deck metadata is a separate layer.
When workspace metadata is relevant, read the live governing source or schema and preserve its
property semantics. Do not assume a property exists, infer one property from another, or project
internal deck structure onto a similarly named workspace field.

When the workspace defines fields such as `Prerequisites`, `Semester`, `Level`, `Tags`, or `State`,
keep their governed meanings separate from this baseline. In particular, a learner prerequisite
inside a deck does not automatically create or remove a cross-deck prerequisite relation, and deck
completion does not imply a work-state transition. Do not mutate workspace metadata merely to make
the deck baseline fit; route such changes through the applicable workspace authority and explicit
task scope.

## Evidence

Gather only evidence needed to make the learning contract trustworthy: concept dependencies,
learner-prerequisite relationships, canonical coverage, version-sensitive boundaries, or whether an
apparent gap is real. Prefer supplied authoritative context and appropriate authoritative sources;
for versioned tools and APIs, prefer current primary documentation when material.

Own this narrow deck-curriculum evidence work, not exhaustive source collection. Keep factual
evidence, pedagogical judgment, workspace metadata, and unresolved uncertainty distinct; narrow
uncertain decisions rather than guessing. When a version or source assumption materially changes
what belongs in scope or how concepts depend on one another, record that assumption in the baseline
rather than leaving it only in transient research context.

## Establish Baseline

Before substantial authoring when no adequate baseline exists:

1. Define learner-facing goal and intended competence.
1. Separate learner prerequisites to assume from material to teach inside the deck.
1. Define the smallest learning scope that supports the goal and explicit exclusions.
1. Express learning outcomes as observable capabilities, not topic labels.
1. Identify concepts, mechanisms, reasoning tools, and skills required by those outcomes.
1. Map what must be understood before dependent concepts can be taught well.
1. Group dependencies into the smallest coherent learning units.
1. Sequence units by conceptual dependency and assign unit responsibilities.
1. Map substantial outcomes to where they are developed and eventually assessed.
1. Record any version or authority assumption that materially constrains the curriculum.
1. Review coherence before handing the baseline to deck implementation.

Do not require one concept per chapter. Derive chapter or unit boundaries from learning structure,
not conventional domain categories.

### Baseline Gate

Reject or revise when:

- learner prerequisites, learning scope, and outcomes are materially inconsistent;
- dependent concepts are used before their prerequisites are established;
- a substantial outcome lacks a credible development or assessment path;
- units exist mainly because the domain has conventional categories;
- adjacent research findings are absorbed without necessity to the deck goal;
- a material version or authority assumption is missing or contradicted;
- unresolved dependency cycles, terminology conflicts, or factual uncertainty make the learning
  contract materially ambiguous.

The baseline should guide incremental authoring without pretending later evidence cannot improve it.

## Review Curriculum Delta

**Discovery is evidence for a curriculum change, not the curriculum change itself.**

Classify a downstream finding as:

- **local material gap** — curriculum is sound; return explanation, practice, assessment, or
  investigation work to `adudeck-deck-build` or its material owner;
- **curriculum delta candidate** — learner prerequisite, learning scope, outcome, dependency,
  sequence, unit responsibility, or a material version boundary may need change;
- **adjacent topic** — useful but not required; reject, defer, or propose a separate deck.

For a delta candidate retain only:

```text
Curriculum Delta
- Discovery / evidence
- Baseline affected
- Smallest proposed change
- Why local repair is insufficient
- Dependency / outcome impact
- Downstream material that may become stale
```

Evaluate whether the change is required for an existing outcome or contract correction, whether a
local fix is enough, how it affects dependencies and accepted material, and whether a separate deck
is the better boundary. Resolve as **accept**, **reject**, **defer**, or **split**.

An accepted delta must make the smallest justified baseline change, preserve unaffected learning
scope/outcomes/dependencies/sequence, update affected coverage, identify all downstream material made
stale through concept dependencies or outcome/assessment coverage, and hand the updated baseline plus
that stale-material set to `adudeck-deck-build`. Do not rewrite downstream material inside this skill.

### Delta Authority

Evidence does not authorize rewriting explicit user decisions. Do not widen a user-defined
out-of-scope boundary, replace the deck goal, relax a required outcome, or change another explicit
curriculum constraint without authority from its source. Keep such changes proposed until resolved.

A deck curriculum delta changes only the intra-deck learning contract. It does not expand
`mols-rpi` execution scope, grant repository/tool side-effect authority, or automatically update
workspace curriculum metadata.

## Audit

Audit after material curriculum change or when integration exposes systemic problems. Check that
goal → outcomes → concepts → sequence → assessment coverage forms a coherent chain, learner
prerequisites precede dependent use, scope stays cohesive, outcomes are not orphaned, terminology
and abstraction level do not drift, material version/authority assumptions remain valid, and
accepted deltas leave no contradictory old assumptions.

Audit the deck learning contract, not prose style, assessment task quality, playground
implementation, or workspace metadata consistency unless that metadata is explicitly in scope.

## RPI and Routing

Use `mols-rpi` when deck-curriculum work needs explicit Research → Plan → Implementation → Review,
replanning, or recursive resolution. This skill owns deck-curriculum state and delta semantics;
`mols-rpi` owns generic loop control, execution scope, and convergence.

- Use `adudeck-deck-build` to implement the baseline and surface delta candidates.
- Use `adudeck-textbook` for textbook quality requirements.
- Use `adudeck-textbook-write` for prose, examples, practice, and assessments.
- Use `adudeck-playground` for hands-on investigations.
