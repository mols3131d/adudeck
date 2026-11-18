# PR #34 · Langfuse textbook merge-readiness loops

Date: 2026-10-30  
Target: [PR #34](https://github.com/mols3131d/adudeck/pull/34)  
Branch: `feat/langfuse-textbook-draft` → `main`

## Goal and boundaries

Close the correctness, persistent-state-safety, instructional-contract, and branch-integration blockers identified in
the [2026-10-05 deep review](../2026-10-05/pr-34-deep-review.md). Keep the existing 0–8 textbook learning contract and
deck-local locked validation. Do not merge this PR or claim credentialed Langfuse/OpenAI Cloud execution from
credential-free CI.

## Loop 1 — Research → Plan → Implementation → Review: executable contracts

Reviewed Unit 5 producer, Unit 6 consumer and evaluator, Unit 8 release gate, and Codex findings. The producer used
`days_since_delivery` and expected `eligible` plus `policy_days`; the hosted Unit 6 task used `days` and returned
`eligible` only. The release gate allowed `NaN`/infinity to bypass numeric comparisons.

- Isolated a hosted task with the Unit 5 input/output contract; retained the separate local category experiment as a
  distinct teaching question.
- Added a credential-free test that imports the actual Unit 5 case builder and invokes the Unit 6 hosted task and
  baseline/candidate experiment callables.
- Rejected nonfinite/out-of-range correctness evidence; rejected nonfinite/negative candidate latency and invalid policy
  thresholds.
- Added regression tests for `NaN`, positive/negative infinity, negative latency, invalid policy thresholds, and the
  cross-unit payload.

Review disposition: the original Unit 5→6 integration mismatch and Unit 8 invalid-evidence approval paths are addressed
in code and executable contract tests.

## Loop 2 — Research → Plan → Implementation → Review: persistent state and provenance

Verified relevant Langfuse SDK contracts: `create_dataset_item(id=...)` upserts by globally unique ID;
`get_dataset(version=...)` needs an aware UTC datetime; prompt labels can be missing even when a prompt series exists,
while `latest` changes on version creation.

- Unit 5: deterministic UUIDv5 ID scoped to dataset name and logical case ID. Repeated identical promotion keeps one
  logical item; documentation states that upsert can update existing content/provenance.
- Unit 6: non-UTC aware ISO-8601 values normalize to UTC before SDK calls; test covers +09:00.
- Unit 7: moved bootstrap to `adudeck-lab/refund-answer`, disabled fetch caching for live bootstrap preflight, and
  refused to create a new version when the selected label is absent but the series exists under `latest`.
- Added a fake state transition for “existing series / missing staging / existing latest” and ensured no creation
  occurs.
- Clarified dedicated lab-project boundary and prompt/dataset state transitions in Units 5–7; updated Unit 8 explanation
  and removed the stale merge-ready claim from the deck README.

Review disposition: formerly uncovered state-safety branches are now covered by deterministic tests. Live Cloud writes
remain deliberately unexecuted.

## Loop 3 — Plan → Implementation → Review: integration and admission

The preceding `main` commit merged PR #33 (OpenTelemetry), diverging from the Langfuse feature branch. The merge had two
overlapping files: `mise.toml` and `scripts/test.sh`. A two-parent merge commit
[`7ce14c1`](https://github.com/mols3131d/adudeck/commit/7ce14c1a93589231b5d0f18525240359c04127fa) preserved the
OpenTelemetry deck and CI workflow, restored its test and acceptance commands, and kept Langfuse validation registered.

Evidence observed after that merge:

- GitHub: `mergeable=true`, branch ahead of `main` and `behind_by=0`.
- [Actions run 41041844067](https://github.com/mols3131d/adudeck/actions/runs/41041844067): `completed/success`,
  including `mise run ci:fast` and external OpenTelemetry runtime acceptance.
- `ci/validated=success` on the merge commit.
- Installed SDK smoke subsequently strengthened to check both `create_dataset_item(id=...)` and
  `get_prompt(cache_ttl_seconds=...)`. Revalidate the current head after this incremental change.

## Final acceptance boundary

Merge readiness requires the latest head to have GitHub `mergeable=true`, `ci/validated=success`, no outstanding
material review blockers, and truthful PR/deck documentation. Credential-free CI is **not** evidence that Langfuse
Cloud/OpenAI live operations succeeded or that production outcomes improved. Those remain separately documented
learning/validation tiers.

Do not merge as part of this loop. Mark ready for review only after verifying the latest head and resolving the three
original Codex threads against the implemented fixes.
