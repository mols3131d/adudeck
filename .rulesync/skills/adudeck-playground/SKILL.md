---
name: adudeck-playground
description: >-
  Design, write, revise, or review executable and interactive learning playgrounds that expose
  mechanisms through direct manipulation and observable system evidence. Use when asked for a
  playground or when learning requires runnable experiments, state inspection, controlled failure
  or variation, or lab artifacts. Do not own curriculum, textbook prose, storage, or publishing.
targets: ["claudecode", "codexcli", "copilot", "copilotcli", "antigravity-ide", "antigravity-cli"]
---

# Adudeck Playground

## Contract

A playground is a **hands-on learning environment for investigating a mechanism**, not a command
recipe whose success criterion is only that the final output appears.

Own the experiment design, hands-on learning surface, and experimental evidence needed to expose
the target mechanism. Treat scope, prerequisites, learning outcomes, terminology, and supplied
reference context as upstream inputs. Do not expand curriculum, choose curriculum sources, choose
storage, or replace the textbook explanation. Compose with `adudeck-textbook-write` when the
playground is embedded in a textbook chapter.

If the upstream scope, prerequisites, and learning outcomes are materially inconsistent, surface
the mismatch instead of using experiment design to silently redefine the learning contract.

`Playground` names a pedagogical responsibility, not a required directory, filename, or environment
shape. Reuse the smallest structure that already fits the deck; do not introduce a `playground/`
namespace or other abstraction merely because this skill is active.

The learner should be able to connect the conceptual model to observed evidence and explain what
the evidence means. When intervention improves causal understanding, the learner should also be
able to explain what changed and what remained invariant.

## Procedure

Use the smallest coherent investigation that exposes the target mechanism:

1. **Target** — identify the state transition, control flow, data flow, side effect, ownership,
   isolation, concurrency, or other mechanism that must become visible.
1. **Predict** — state the observable evidence expected before execution or investigation,
   including an invariant when one matters.
1. **Run or stage** — execute the smallest useful experiment, or select the smallest existing case
   that contains the evidence needed for a read-only investigation.
1. **Observe** — inspect only the surfaces that materially reveal the mechanism.
1. **Interpret** — connect observations back to the model and explain why they occurred.
1. **Vary or compare when useful** — change one meaningful condition or choose a contrasting case.
1. **Re-observe when varied** — if variation or comparison is used, explain the resulting difference
   and any invariant that remained true.

Do not require variation when a diagnostic or read-only investigation already provides sufficient
evidence. When observation differs from prediction, distinguish a wrong mental model from setup,
instrumentation, environmental state, or version differences before drawing a conclusion.

## Experimental Discipline

Decide whether the playground is primarily a **causal experiment**, **comparative investigation**,
or **diagnostic observation**. Do not claim stronger conclusions than the setup supports.

- For causal experiments, establish a baseline when needed and vary one learning-relevant dimension
  at a time while keeping other relevant conditions stable.
- For comparisons, state the differing dimensions and treat uncontrolled relevant differences as
  confounders rather than proof of causation.
- For diagnostic observations, a trace, explanation, or consistency check may be sufficient.
- Tie predictions to observable evidence rather than vague outcomes such as "works" or "fails".

## Observability

Expose meaningful intermediate evidence rather than only final success.

When useful, triangulate the **same logical execution or object** across complementary surfaces such
as UI, CLI, logs, metadata, filesystem state, database rows, metrics, traces, process state,
network evidence, or external output. Provide enough identity information for the learner to
explain why those observations refer to the same event or object.

Prefer a few complementary surfaces over unrelated diagnostic noise. Prefer read-only or
low-interference probes. If instrumentation materially changes timing, state, concurrency, resource
usage, or another relevant behavior, make that effect explicit.

Internal surfaces may be used as probes when they reveal the mechanism, but label them as internal.
Do not teach an internal schema, private API, or diagnostic hook as if it were a stable user-facing
contract.

## Instructional Instrumentation

Important transient state may disappear before a learner can inspect it. Make it human-observable
without changing the concept being taught.

Useful techniques include short delays, reduced concurrency, deterministic inputs, controlled pause
points, failure injection, retry delays, and temporary diagnostic markers. Treat these as teaching
instrumentation, not production recommendations, and disclose their material effects.

Use controlled failure when the happy path hides an important mechanism. Make the learner inspect
what changed, what did not, where execution resumes, whether a partial side effect occurred, what a
retry or rerun repeats, and which invariant must hold. Failure should expose a learning target and
be controlled enough to reason about reliably.

## Playground Artifacts

Keep setup, execution or investigation, observation, optional variation, reset, and output
boundaries understandable.

Automate incidental setup, reset, and cleanup when that removes noise, but do not automate away the
learner action, decision, or observation that exposes the target mechanism. Helpers should make the
mechanism easier to reach, not pre-solve the investigation.

Prefer:

- isolated, disposable, and reversible local environments when sufficient;
- least-privilege and non-destructive operations when they expose the same mechanism;
- deterministic inputs and identifiable outputs;
- explicit observation commands or probes;
- repeatable reset or cleanup for persistent state;
- cleanup scoped only to playground-owned state;
- visible failure context, minimal dependencies, and minimal topology;
- safe example data with no secrets or confidential material.

Do not use shared, production, or user-owned resources merely for realism. If destructive behavior
is itself the learning target, isolate it to disposable playground-owned resources and make that
boundary explicit. Apply repository coding guidance when code-facing implementation is required.

## Technical Verification and Validation

Do not turn playground work into curriculum research. When behavior depends on version-sensitive
APIs, commands, configuration, runtime support, or diagnostic interfaces, verify those details
against supplied authoritative context or an appropriate authoritative source; for versioned tools
and APIs, prefer current primary documentation. Use verification only to make the defined
playground correct; do not expand scope because additional features exist.

Make material runtime and version assumptions explicit. Pin a version when drift would make the
playground or its expected observations unreliable; otherwise avoid unnecessary pinning.

Distinguish documentation-backed facts from experimental evidence. If a material implementation
detail cannot be verified, preserve that uncertainty rather than guessing silently.

Validate at the cheapest meaningful level and report the boundary accurately. Keep distinct:

- static or syntax validation;
- setup or configuration validation;
- partial component execution;
- full playground execution or investigation;
- learner-visible observation and, where relevant, failure or recovery verification.

When persistent state matters, verify repeat execution from a known state or verify the reset path.
Do not imply end-to-end behavior was verified when only syntax, formatting, documentation review,
or repository CI was run.

## Quality Gate

Reject or revise a playground when a major learning path is primarily:

- command transcription followed only by confirmation that it worked;
- final success with no observation of the mechanism;
- prediction framed only as generic success or failure;
- logs, screenshots, or metrics with no interpretation;
- causal claims from uncontrolled comparisons;
- accidental failure or hidden state that makes results difficult to reason about;
- setup, automation, or instrumentation that obscures or materially distorts the learning target
  without explanation;
- internal implementation details presented as stable public contracts;
- a supplied artifact that the learner only runs without meaningful prediction, investigation, or
  interpretation.

The playground qualifies when execution or investigation produces observable evidence and the
learner must reason from it. Use variation or comparison when it tests the learner's model, not as
a mandatory ritual.

## Routing

- Use `adudeck-textbook` for the overall textbook standard and whether hands-on learning is needed
  for competence.
- Use `adudeck-textbook-write` for textbook prose, worked explanations, exercises, assessments, and
  integration of a playground into the surrounding learning narrative.
- Use this skill for the experiment or investigation, experimental controls, observation surfaces,
  instructional instrumentation, failure design, runnable artifacts, technical verification, and
  playground validation.
