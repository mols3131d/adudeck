---
name: adudeck-textbook
description: >-
  Define and review the adudeck textbook contract. Use for textbook structure, instructional
  depth, chapter quality, exercises, assessment, hands-on learning integration, or deciding
  whether material qualifies as a textbook. Do not use for external research, curriculum design,
  source collection, storage, or writing the textbook prose; use adudeck-textbook-write for
  authoring and adudeck-playground for hands-on learning investigations.
targets: ["claudecode", "codexcli", "copilot", "copilotcli", "antigravity-ide", "antigravity-cli"]
---

# Adudeck Textbook

## Contract

A textbook is a **primary learning resource for a defined scope**, not a summary, outline,
reference page, lecture note, blog post, or step-by-step tutorial.

Own only the textbook standard and quality gate. Treat scope, prerequisites, learning outcomes,
and supplied authoritative context as upstream inputs. Do not research, expand the curriculum,
choose sources, write the actual textbook prose, design hands-on playgrounds, or decide where it is
stored or published.

If scope, prerequisites, and learning outcomes are materially inconsistent, treat the learning
contract as unresolved. Do not quality-pass material that silently compensates by redefining or
expanding those upstream decisions; require the inconsistency to be surfaced for upstream
resolution.

Do not quality-pass material merely because it is pedagogically complete when important claims
conflict with supplied authoritative context, rely on unsupported detail, or conceal a material
uncertainty that affects the learning target.

## Standard

A textbook should let the learner build competence without needing another primary explanation
for the same scope.

Require, where the material needs them:

- concepts developed progressively from prerequisite knowledge;
- chapter and section order based on conceptual dependency;
- precise terminology supported by useful mental models or mechanisms;
- worked examples that expose meaningful intermediate reasoning or state;
- misconceptions, counterexamples, boundaries, or failure cases that repair likely wrong models;
- practice that requires reasoning, transfer, modification, debugging, derivation, or synthesis;
- hands-on investigation when direct interaction and observed system evidence materially improve
  competence;
- checkpoints, cumulative work, and assessment aligned with the stated learning outcomes and
  collectively sufficient to judge the material outcomes they are meant to assess.

Hands-on work should participate in the conceptual progression rather than exist only as a detached
command recipe. When the learning target is executable, stateful, interactive, diagnostic, or
operational, prefer a path where the learner predicts behavior, observes meaningful evidence, and
interprets it. Use variation or comparison when it materially improves causal understanding rather
than requiring modification for its own sake. Use `adudeck-playground` to design or review that
hands-on learning surface.

These are instructional responsibilities, not a mandatory visible template. Apply them at the
smallest level that creates a coherent learning progression.

## Depth

Prefer teaching value over either compression or length.

- Explain important causes, relationships, derivations, states, and boundaries instead of only
  naming them.
- Introduce terminology and notation before assuming fluency.
- Use examples to reveal the concept rather than decorate the prose.
- Do not hide essential explanation inside exercises or playgrounds.
- Do not compress material merely to make it short.
- Do not inflate material with repeated summaries, decorative prose, or redundant examples.

## Evidence Fidelity

Judge factual integrity separately from instructional depth.

- Keep material claims consistent with supplied authoritative context unless a conflict is made
  explicit and resolved by an appropriate upstream owner.
- Do not invent specific facts, versions, guarantees, or implementation details merely to make an
  explanation feel complete.
- Do not silently flatten conflicting evidence or known uncertainty into a single confident claim.
- Treat source-dependent, contested, version-sensitive, or otherwise unstable claims as needing
  appropriate verification before they become stable textbook assertions.

Do not require fresh research or source attachment for every stable foundational statement. Apply
this gate where supplied context, instability, conflict, or uncertainty makes factual correctness a
material part of the learning target.

This skill does not own research or source selection; it owns refusing to qualify material whose
material factual foundation remains unresolved.

## Quality Gate

Reject or revise the material when any major part is still primarily:

- definitions or bullet points without conceptual development;
- answers or examples without the reasoning needed to learn from them;
- exercises solvable by transcription rather than understanding;
- hands-on work that only reproduces commands and checks final success without exposing the
  mechanism being taught;
- assessment unrelated to the stated outcomes, dominated by replaying worked examples, or lacking
  a meaningful way to judge the targeted competence;
- materially unsupported or unresolved claims presented as settled facts;
- notes, glossary, cheat sheet, tutorial, outline, or blog-style explanation presented as a
  textbook.

The material qualifies only when its explanation, examples, practice, and any necessary hands-on
investigation together can serve as the learner's main path to competence for the defined scope,
and its material claims are consistent with the authoritative context available for that work.

## Routing

Use `adudeck-textbook-write` to write or revise textbook prose, chapters, worked examples,
exercises, and assessments. Use `adudeck-playground` to design, implement, revise, or review
hands-on learning investigations.
