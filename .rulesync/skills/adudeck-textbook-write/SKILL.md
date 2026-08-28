---
name: adudeck-textbook-write
description: >-
  Write or revise textbook chapters, sections, worked examples, exercises, and assessments from
  an already defined learning scope, learner prerequisites, outcomes, and supplied context. Use for
  actual textbook authoring or substantial deepening of thin material. Do not own deck curriculum
  research or decisions, deck build orchestration, storage, publishing policy, or playground
  investigation design; use adudeck-deck-curriculum for deck curriculum work, adudeck-deck-build
  for deck-level implementation, and adudeck-playground for hands-on learning investigations.
targets: ["claudecode", "codexcli", "copilot", "copilotcli", "antigravity-ide", "antigravity-cli"]
---

# Adudeck Textbook Write

## Contract

Write instructional material that can serve as the learner's **primary explanation** for the
supplied scope.

Preserve upstream learning scope, learner prerequisites, and learning outcomes. Reuse supplied
terminology when it is valid and treat authoritative context as a constraint, but do not silently
propagate material conflicts, unsupported claims, or known stale details. Make local pedagogical
choices when needed without turning authoring into curriculum design or broad research.

If supplied learning scope, learner prerequisites, and learning outcomes are materially
inconsistent, surface the mismatch instead of silently repairing it by expanding scope, redefining
prerequisites, or changing outcomes. Route the deck curriculum decision to
`adudeck-deck-curriculum`.

Follow `adudeck-textbook` when available. Otherwise preserve the same minimum standard: develop
concepts progressively, expose reasoning in examples, require active practice, and revise
material that still reads like notes or a summary.

When competence requires direct execution or observation, integrate the surrounding explanation
with an `adudeck-playground` rather than treating the hands-on work as a prose-only exercise. This
skill owns the learning narrative around that playground; `adudeck-playground` owns the hands-on
investigation, observation surfaces, meaningful variation or comparison, failure design, and
playground validation.

## Correctness Boundary

Do not own deck curriculum research or source selection. When material correctness depends on a
version-sensitive, unstable, conflicting, or otherwise uncertain externally verifiable detail,
verify that narrow detail against supplied authoritative context or an appropriate authoritative
source, preferring primary sources when they materially improve correctness; for versioned tools
and APIs, prefer current primary documentation. Use verification only to make the defined material
correct; do not expand scope because additional facts or features exist.

If a material detail cannot be verified with the available sources or capabilities, preserve the
uncertainty rather than inventing or silently resolving it.

Do not perform fresh verification by default when supplied context and stable foundational
knowledge are sufficient. Load additional sources only when they resolve a material correctness
question for the current scope.

Keep source-backed facts, unresolved uncertainty, and playground-produced experimental evidence
distinct.

## Procedure

1. Identify the learner level, learning scope, learner prerequisites, and outcomes from the supplied
   context.
1. Preserve the accepted deck curriculum unit order. Within the assigned unit or slice, choose the
   smallest coherent local section sequence, ordered by conceptual dependency.
1. Develop each major concept from motivation or prerequisite connection into a precise model,
   explanation, worked application, and practice.
1. Add misconceptions, counterexamples, boundaries, or failure cases where a plausible wrong
   mental model exists.
1. When direct interaction materially improves understanding, connect the explanation to a
   playground at the point where the learner needs observable system evidence rather than
   postponing it as a detached appendix.
1. Add checkpoints or cumulative work when the learner must integrate multiple concepts.
1. Review the result against the textbook quality gate and deepen only the parts that fail it.

Across sections, preserve conceptual continuity: reuse established terminology and invariants
consistently, and do not rely on a prerequisite before it has been introduced or declared.

Reduce scaffolding as the learner is expected to become more independent. Prefer moving from
worked support toward prediction, explanation, transfer, and independent judgment rather than
making later work harder through unrelated complexity.

Do not ask for extra inputs when the supplied scope is sufficient for a sound local teaching
decision.

## Teaching Moves

Use only the moves that materially improve learning.

### Explain

- Show why a concept is needed and how it connects to prior knowledge.
- Define terminology and notation before relying on them.
- Give the learner a mental model, mechanism, invariant, relationship, or other reasoning tool.
- Explain important consequences and boundaries in prose, not only in examples.
- Use transitions when one concept creates the need for the next.

### Work Examples

A worked example should show how an informed learner moves from problem to result:

1. state the problem and relevant assumptions;
1. identify the concept or model being used;
1. expose meaningful intermediate steps, states, transformations, or decisions;
1. explain why important steps are valid;
1. verify or interpret the result.

For code, expose execution state or control flow when that is the learning target. For
mathematics, show the needed derivation or transformation. For systems and tools, explain state
and data flow before relying on commands.

### Practice

Practice is for forming, testing, and repairing understanding with useful feedback.

Prefer tasks that require the learner to:

- predict or trace;
- explain or compare;
- derive or justify;
- find and correct an error;
- modify while preserving a property;
- apply the concept to a new case;
- synthesize multiple concepts.

Do not use transcription as evidence of understanding. Do not reveal complete solutions
immediately unless requested; use hints, selected checks, or worked solutions when they support
independent study.

When practice must manipulate or investigate a live, runnable, or diagnostic system to expose the
mechanism, route the investigation design to `adudeck-playground` and keep this skill focused on why
the investigation appears where it does in the learning progression and what the learner must
explain from it.

### Assess

Assessment is for determining whether the stated learning outcomes can be demonstrated with less
instructional support than ordinary practice.

- Map each substantial assessment task to one or more stated learning outcomes and ensure the
  assessment set covers the material outcomes it is intended to judge.
- Prefer transfer, explanation, tracing, derivation, debugging, comparison, design, or justified
  modification over replaying a worked example with superficial substitutions.
- Require evidence of understanding appropriate to the target rather than success by memorizing
  textbook wording.
- Distinguish formative checks from cumulative assessment when both are present.
- Make correctness or quality judgeable through expected properties, reasoning criteria, tests,
  observable evidence, or a rubric appropriate to the task.
- Do not expose a complete solution before the learner has a meaningful opportunity to attempt the
  assessment unless the user explicitly requests it.

When an assessment depends on a live or diagnostic system, this skill owns what competence is being
assessed and how performance is judged; route the executable environment, observation surface, and
experimental controls to `adudeck-playground`.

## Revision

When the input is an outline, summary, lecture note, or shallow chapter, preserve valid scope and
facts but rebuild the missing teaching layers. Do not merely paraphrase, add headings, or add more
examples.

When supplied facts or terminology materially conflict with authoritative context, preserve the
scope and learning intent but surface the conflict instead of embedding it more deeply in the
rewrite.

A short section is acceptable. A shallow section is not.

## Routing

- Use `adudeck-deck-curriculum` when authoring exposes a learner-prerequisite, learning-scope,
  outcome, dependency, or sequence problem in the upstream deck learning contract.
- Use `adudeck-deck-build` to choose and integrate incremental learning slices across the deck.
- Use `adudeck-textbook` for the overall textbook quality contract.
- Use `adudeck-playground` for hands-on investigation design and validation.
