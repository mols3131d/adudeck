---
name: adudeck-textbook-write
description: Write or revise textbook chapters, sections, worked examples, exercises, labs, and assessments from an already defined learning scope, prerequisites, outcomes, and supplied context. Use when the user asks to generate, write, expand, rewrite, or substantially deepen textbook content rather than notes or a summary. Follow the adudeck-textbook contract when available. Do not perform external research, design curriculum, choose sources, or decide storage and publishing policy unless those responsibilities are explicitly delegated by another active workflow.
---

# Adudeck Textbook Write

## Contract

Write instructional material that can function as the learner's **primary explanation** for
the supplied scope.

Preserve the given scope, prerequisites, learning outcomes, terminology, and evidence. Do not
quietly turn authoring into curriculum design or research. When the input leaves local
pedagogical choices open, choose the sequence that makes the concepts easiest to build on one
another without adding a new subject area.

Use the `adudeck-textbook` contract as the quality baseline when it is available.

## Authoring Procedure

1. Identify the learner level, scope, prerequisites, and outcomes from the supplied context.
1. Determine the smallest coherent chapter or section sequence needed to teach that scope.
1. Order concepts by dependency rather than by source order or arbitrary symmetry.
1. Write the explanation progressively from familiar ideas to new abstractions.
1. Add worked examples where intermediate reasoning, state, derivation, or decision-making is
   instructional.
1. Add misconceptions, counterexamples, boundary cases, or contrasts where a plausible wrong
   mental model exists.
1. Add practice that requires the learner to predict, explain, derive, modify, debug, compare,
   apply, or synthesize.
1. Add chapter checkpoints and cumulative work where the scope requires integration.
1. Review the result against the textbook quality gate and expand any section that still reads
   like notes or a summary.

Do not ask for extra inputs when the supplied scope is sufficient to make a sound local
teaching decision.

## Exposition

Develop ideas instead of naming them.

- Explain why a concept is needed before or while introducing it.
- Connect new concepts to prerequisite knowledge explicitly when the connection matters.
- Define terminology and notation before relying on it.
- Give the learner a mental model, mechanism, invariant, relationship, or other reasoning tool.
- Explain important consequences and boundaries in prose, not only in examples.
- Use transitions to show how one concept creates the need for the next.
- Prefer paragraphs for conceptual development; use lists for genuinely parallel items.
- Avoid turning every section into `definition → bullets → tiny example → quiz`.
- Avoid repeated summaries that substitute for deeper explanation.

A short section may be correct. A shallow section is not acceptable merely because it is
concise.

## Worked Examples

A worked example should expose how an informed learner moves from problem to result.

When relevant:

1. state the problem and assumptions;
1. identify the concept or model being applied;
1. show meaningful intermediate steps, states, transformations, or decisions;
1. explain why each important step is valid;
1. verify or interpret the result;
1. contrast with a nearby case when that reveals a boundary.

Do not present an answer followed by a retrospective explanation and call it worked reasoning.

For code, trace execution state and control flow when they are the learning target. For
mathematics, show transformations or derivations at the requested level instead of dropping
an unexplained formula. For systems and tools, explain state and data flow before listing
commands.

## Misconceptions and Boundaries

Actively repair likely wrong mental models.

Use a misconception section, inline contrast, counterexample, or edge case when useful. Prefer
specific failure cases over generic warnings such as "be careful".

Distinguish:

- similar terms that learners commonly conflate;
- a useful beginner model from the point where that model stops being accurate;
- syntax from semantics;
- mechanism from convention;
- mathematical identity from programming notation;
- conceptual behavior from a particular tool's interface.

## Practice

Build practice from local understanding toward transfer.

Use an appropriate mix of:

- trace or predict before executing;
- explain why an answer or behavior occurs;
- complete a derivation or missing reasoning step;
- find and correct an error;
- modify an example while preserving an invariant;
- compare two cases and identify the meaningful difference;
- apply the concept to an unfamiliar example;
- combine concepts in a cumulative exercise, lab, or project.

Avoid exercises that can be completed by copying the preceding sentence with different nouns.
Do not reveal complete solutions immediately unless requested. Supply hints, selected answer
checks, or worked solutions when they improve independent study.

## Revision from Thin Material

When the input is an outline, summary, lecture note, or existing shallow chapter, do not merely
polish or paraphrase it.

Preserve its valid scope and facts, then rebuild missing instructional layers:

- motivation and prerequisite bridge;
- conceptual development;
- intermediate reasoning;
- worked examples;
- misconceptions and boundary cases;
- active practice;
- checkpoints and cumulative integration.

Do not mistake more headings, more bullets, or more examples for deeper teaching.

## Final Review

Before finalizing, check that:

- the learner can follow the chapter without another primary explanation for the same scope;
- each major concept is developed rather than merely defined;
- worked examples expose intermediate reasoning where it matters;
- terminology and notation appear only after adequate introduction;
- exercises test understanding and transfer;
- later sections actually depend on earlier ones in a visible way;
- the prose does not collapse into blog, notes, glossary, cheat-sheet, or tutorial form;
- added length serves learning rather than repetition.

If any major section fails these checks, revise the material before treating it as textbook
content.