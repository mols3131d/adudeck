---
name: adudeck-deck-build
description: >-
  Create, continue, expand, or finish a learning deck through reviewed incremental learning slices.
  Use for deck-level implementation orchestration, selecting the next slice, calibrating the first
  slice, coordinating textbook and playground work, integration reviews, completion reviews, or
  surfacing deck-curriculum changes discovered during build work. Do not own curriculum decisions,
  textbook quality standards, prose authoring, playground experiment design, storage, or publishing.
targets: ["claudecode", "codexcli", "copilot", "copilotcli", "antigravity-ide", "antigravity-cli"]
---

# Adudeck Deck Build

## Contract

Own **how an accepted deck curriculum becomes a coherent deck over time**.

Do not generate a non-trivial deck as one unreviewed bulk artifact. Build through the smallest
coherent learning slices that can be authored, exercised where needed, reviewed, and accepted before
the deck grows further.

Require an adequate `adudeck-deck-curriculum` baseline before substantial implementation. Surface
curriculum delta candidates, but do not silently change learning scope, learner prerequisites,
outcomes, dependency order, or unit responsibility.

Compose with `adudeck-textbook` for quality decisions, `adudeck-textbook-write` for instructional
authoring, `adudeck-playground` for hands-on investigations, and `mols-rpi` for complex iterative
control. Deck learning scope and RPI execution `Active Scope` are distinct and both remain in force.

Reuse established deck storage and repository structure. Do not create planning namespaces,
placeholder chapter trees, or workflow scaffolding merely because this skill is active.

## Build State

Keep only state needed to choose and review the next increment:

```text
Deck Build State
- Deck curriculum baseline reference
- Accepted learning slices + validation boundary / material caveats
- Current slice, if any
- Pending curriculum delta candidates
- Material integration findings
- Remaining completion gaps
```

A learning slice is defined by coherent competence, not a file or chapter boundary. Transient state
may stay inline, but when work spans sessions, branches, or review increments, accepted curriculum,
validation limits, and progress needed for reliable resumption must be recoverable from the
established workspace. Prefer updating an existing deck overview surface when one already carries
goal, prerequisites, scope, or learning path; do not invent a mandatory build manifest when the deck
itself is sufficient.

## Start and Calibrate

1. Load applicable repository/deck guidance and the current deck curriculum baseline.
1. Inspect existing material; accepted work is state, not a prompt to regenerate it.
1. If the baseline is missing or materially inconsistent, route to `adudeck-deck-curriculum` before
   substantial authoring.
1. Reconstruct the minimum current Build State from persisted deck state and accepted decisions.
1. Select the smallest next slice that advances the curriculum without undeclared dependencies.

For a new deck, build one **calibration slice** end to end before scaling across chapters. Prefer an
early reachable slice that exercises a high-risk recurring teaching pattern while respecting
conceptual dependency order. Review explanation depth, terminology, practice, assessment evidence,
and hands-on approach while systemic mistakes are still cheap to fix.

A calibration slice may include:

```text
learning target
→ explanation / model
→ worked reasoning
→ prediction or active practice
→ playground evidence when needed
→ interpretation
→ assessment or checkpoint when required
→ review
```

If a materially different recurring instructional mode cannot appear in the first calibration slice
because of prerequisites, calibrate that mode when it first becomes reachable before replicating it
widely. Do not turn incidental choices from any calibration slice into rigid templates.

## Slice Loop

For each slice:

1. **Select** a bounded objective covered by the current baseline.
1. **Plan** learner prerequisites, target competence, explanation, practice, and assessment
   obligations; apply `adudeck-textbook` when a quality decision is needed, including whether
   hands-on evidence materially improves competence.
1. **Build** through `adudeck-textbook-write` and `adudeck-playground` as required.
1. **Validate** that owning skills established the correctness or runtime boundary actually claimed;
   syntax or CI does not become learner-visible runtime evidence.
1. **Review** the slice with `adudeck-textbook` and against already accepted material.
1. **Classify** findings as local material gaps or curriculum delta candidates.
1. **Accept** only when required obligations are met at the claimed validation level. Preserve that
   validation boundary and any material unverified caveat in Build State; if higher-level validation
   is required for a learning outcome, keep it as a completion gap rather than silently upgrading the
   claim.

Use `mols-rpi` when the slice needs explicit evidence, planning, replanning, or recursive blocker
resolution. This skill owns learning-increment selection and deck progression; RPI owns generic loop
control and execution scope.

## Build Run Boundary

Incremental review must create real handoff points, not merely internal checkpoints inside a disguised
bulk generation run. By default, a deck-build run should produce and review one calibration slice or
one small coherent increment plus repairs needed to accept it, then persist or report the updated
Build State before continuing later.

Continue through multiple increments in the same run only when the user explicitly requests continued
iterative build work and each increment still receives its own validation and review. A request to
"create a deck" alone does not authorize filling every planned unit in one pass.

## Discovery and Delta Handoff

Expect build work to reveal missing information. Do not suppress discovery or convert it directly
into scope growth.

- **local material gap** — fix explanation, practice, assessment, or integration inside the accepted
  deck curriculum;
- **playground gap** — route observability or experiment work to `adudeck-playground`;
- **curriculum delta candidate** — send learner-prerequisite, scope, outcome, dependency, sequence,
  or unit-responsibility evidence to `adudeck-deck-curriculum`;
- **adjacent topic** — keep it out unless an accepted curriculum delta brings it in.

Pause only work that depends on an unresolved delta. Independent work may continue only when valid
under the current baseline, execution scope, and plan.

When a delta is accepted, update the baseline reference and propagate staleness through the affected
concept-dependency and outcome/assessment paths, including cumulative or integration material that
indirectly relies on the changed contract. Repair from the earliest affected dependency as needed
and preserve material proven unaffected by that propagation.

## Integration Review

Slice quality does not prove deck quality. The calibration slice gets its own review; perform
cross-slice integration review when multiple accepted slices create material coupling or a delta
changes earlier assumptions.

Check:

- terminology and mental-model consistency;
- learner-prerequisite and dependency order;
- repeated explanation that signals a missing shared foundation;
- concepts used before introduction;
- progression toward more independent reasoning;
- practice and assessment coverage across outcomes;
- hands-on difficulty, observability, validation boundaries, and operational assumptions;
- stale material after curriculum change;
- local deck coherence and links where relevant.

Route defects to their owning skill. Trigger integration review by expected information gain or
cross-slice risk, not a fixed chapter count.

## Completion

Do not declare completion because every planned filename exists. Establish that:

- no accepted deck-curriculum delta remains unapplied;
- substantial outcomes have credible explanation, practice, and assessment paths;
- learner-prerequisite and dependency gaps are resolved;
- `adudeck-textbook` quality-passes the deck for its defined scope;
- required playgrounds meet their validation boundary;
- material validation caveats required for the claimed learning outcomes are resolved;
- material integration findings are resolved;
- optional ideas remain explicitly outside the completion claim.

If curriculum coherence is uncertain, route a deck-curriculum audit rather than deciding it locally.
Completion is an evidence-backed learning state, not structural fullness. It is also distinct from
workspace or storage state: do not move a deck to archive or change a `State` property merely because
its current learning scope is complete unless that state transition is separately requested and
authorized.

## Repository Increment Boundary

For Git-backed work, prefer reviewable changes containing one coherent slice or a small coupled set
plus required integration repair. Do not require one PR per slice or hold a whole non-trivial deck
unreviewed for one PR. Defer exact branch, commit, and PR mechanics to repository guidance.

## Quality Gate

Reject or revise a workflow that primarily:

- generates the whole non-trivial deck before a representative slice is reviewed;
- chains many nominally reviewed slices in one run to recreate bulk generation without meaningful
  handoff;
- creates placeholder chapters before their learning responsibility is justified;
- treats a table of contents as sufficient without concept dependencies and outcomes;
- appends discoveries directly into curriculum without delta review;
- rewrites valid accepted material instead of preserving state;
- relies on ephemeral conversation state for accepted decisions needed to resume persistent work;
- loses or overstates the validation boundary of accepted slices;
- repairs only direct delta effects while leaving transitively stale material accepted;
- accepts slices from prose existence, command success, syntax, or CI alone;
- ignores cross-slice terminology, prerequisite, or assessment drift;
- declares completion from file coverage or conflates it with deck storage/work state.

## Routing

- `adudeck-deck-curriculum` — baseline, audit, and delta decisions.
- `adudeck-textbook` — instructional and factual quality gate.
- `adudeck-textbook-write` — prose, examples, practice, and assessments.
- `adudeck-playground` — hands-on investigation and validation.
- `mols-rpi` — generic Research → Plan → Implementation → Review control when needed.
