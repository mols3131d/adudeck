---
name: adudeck-textbook
description: >-
  Define and enforce the adudeck textbook contract for structuring, reviewing, or deciding
  whether instructional material qualifies as a textbook. Use when a task concerns textbook
  architecture, chapter boundaries, instructional depth, worked examples, exercises,
  assessment, or textbook-quality review. Do not use for external research, curriculum
  design, source collection, repository or Notion placement, or writing the actual textbook
  prose; use adudeck-textbook-write for authoring.
---

# Adudeck Textbook

## Contract

Treat a textbook as a **primary learning resource**, not as a summary, outline, cheat sheet,
lecture note, glossary, blog post, or step-by-step tutorial.

Own only the textbook contract: instructional structure, depth, progression, practice, and
quality. Treat supplied scope, prerequisites, learning outcomes, and evidence as inputs from
upstream work. Do not expand the curriculum or perform research to fill missing scope.

## Textbook Model

A textbook should normally provide:

- purpose, prerequisites, learning outcomes, and guidance for using the book;
- a chapter sequence whose order follows conceptual dependency;
- progressive explanation of concepts rather than definition lists;
- worked examples that expose intermediate reasoning or state;
- misconceptions, counterexamples, edge cases, or failure modes where they improve learning;
- exercises that require active reasoning;
- chapter checkpoints;
- cumulative application across multiple concepts;
- assessment when completion or readiness must be judged.

Do not require every artifact to use the same visible template. Preserve instructional
responsibilities even when the presentation varies.

## Chapter Contract

For each major concept, develop enough of the following sequence for a learner to build and
use the concept:

1. establish the problem, motivation, or question;
1. connect the concept to prerequisite knowledge;
1. define the concept precisely before relying on its terminology or notation;
1. build a useful mental model, mechanism, or relationship;
1. develop the concept through explanation, derivation, comparison, or examples;
1. show worked examples with meaningful intermediate steps;
1. correct likely misconceptions with counterexamples, boundary cases, or contrasting cases;
1. provide practice that requires the learner to reason or act;
1. connect the concept to later material when the dependency matters;
1. provide a checkpoint that tests whether the learner can continue.

Do not force all ten elements into every small section. Apply them at the narrowest level that
creates a coherent learning progression.

## Depth

Make the material self-contained enough to serve as the main explanation for the defined
scope.

- Prefer explanation and reasoning over compressed definitions.
- Prefer derivation or causal/mechanical explanation over unexplained formulas and rules.
- Prefer state transitions and models over command or API lists.
- Use examples to reveal the concept, not to decorate prose.
- Introduce notation and terminology before assuming fluency.
- Explain important boundaries and exceptions instead of hiding them in exercises.
- Do not compress explanation merely to reduce length.
- Do not inflate length with repeated summaries, decorative prose, or redundant examples.

## Exercises and Assessment

Exercises should measure understanding rather than transcription. Mix appropriate forms such
as:

- prediction and tracing;
- explanation in the learner's own words;
- derivation and proof-like reasoning at the requested level;
- comparison and classification;
- modification and debugging;
- application to a new case;
- synthesis across concepts.

Use difficulty progression when the material benefits from it. Do not provide complete
solutions immediately unless requested; use hints, selected checks, or worked solutions when
they support self-study without replacing the learner's work.

Assessment should evaluate the stated learning outcomes, not incidental trivia.

## Quality Gate

Reject or revise the artifact if it could reasonably be described as any of the following:

- a blog post with examples;
- lecture or study notes;
- a bullet-point summary;
- an outline or glossary;
- a cheat sheet or reference page;
- a tutorial consisting mainly of steps;
- a collection of definitions followed by a small quiz.

The material qualifies as a textbook only when a learner can use it as the primary explanation
for the defined scope and can build competence through its examples and practice.

## Routing

Use `adudeck-textbook-write` when the task is to write or revise actual textbook prose,
chapters, worked examples, exercises, labs, or assessments.

Keep external research, curriculum design, source selection, fact checking, storage,
publishing, and workspace policy in their own upstream or downstream workflows. Do not copy
those responsibilities into this Skill.
