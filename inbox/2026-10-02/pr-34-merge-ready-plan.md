# PR #34 Merge-Ready Repair Plan

Target: `mols3131d/adudeck#34`

Branch: `feat/langfuse-textbook-draft`

Date: 2026-10-02

Goal: move PR #34 from a strong Draft to a merge-recommended Langfuse textbook deck without overstating live/cloud validation.

## Acceptance gate

PR #34 is merge-ready only when all of the following are true:

1. The Langfuse deck is tested inside its own declared dependency environment, not the repository root environment.
2. A real deck-local `uv.lock` exists and deterministic tests run with `--project ... --locked`.
3. Credential-free installed-SDK smoke checks exercise the public Langfuse/OpenAI surfaces used by the textbook.
4. Unit 8 represents baseline and candidate evidence independently, preserves failure meaning, compares a well-defined paired population, and distinguishes critical failure from regression.
5. Unit 6 gives the learner a concrete path for pinning the same hosted dataset version across baseline/candidate runs.
6. Unit 7 provides bounded prompt bootstrap state, lets the learner compare label lookup with exact-version lookup, and explains fallback provenance loss.
7. The textbook/README and PR completion wording match the actual validation boundary.
8. Repository deterministic CI is green on the final head.

Live Langfuse Cloud ingestion and paid OpenAI calls are useful Level-3 evidence but are not required for merge if the textbook clearly labels them as unperformed live validation.

## Workstream A — deck-local runtime contract

### A1. Generate the lock from the real deck project

Generate `decks/llmops-langfuse/uv.lock` from the existing dependency contract:

```toml
langfuse>=4.16,<5
openai>=3.19.2,<4
```

Do not hand-author dependency resolution.

### A2. Make the repository test target use the deck environment

Change `scripts/test.sh` so `run_langfuse_deck` consistently uses:

```bash
env -u VIRTUAL_ENV uv run --project "$project_dir" --locked ...
```

for compile, contract tests, and SDK smoke.

### A3. Add actual installed-SDK smoke

Credential-free smoke should import and inspect only public surfaces used by the learning path. It must not require Cloud credentials or make provider calls.

Minimum contract surface:

```text
langfuse.get_client
langfuse.propagate_attributes
langfuse.Evaluation
Langfuse observation/client score/dataset/experiment/prompt methods used by examples
langfuse.openai.OpenAI
OpenAI.responses.create
```

Prefer callable/signature-compatible public-surface assertions over implementation internals.

## Workstream B — Unit 8 evidence model repair

Replace the shared row status with independent variant evidence.

Target model:

```text
EvidenceRow
├─ baseline: VariantEvidence(status, score)
└─ candidate: VariantEvidence(status, score)
```

Required invariants:

```text
status == scored   -> score exists
status != scored   -> score is absent
```

Comparison rules:

- quality delta is computed over an explicit paired-scored population;
- baseline/candidate coverage remains visible independently;
- required comparison gaps block release;
- `regression` means baseline pass -> candidate fail;
- an already-failing critical case is a critical failure, not a new regression;
- evaluator/application/missing-score states are never collapsed into score 0.

Required tests:

```text
baseline scored / candidate evaluator error
baseline evaluator error / candidate scored
baseline scored / candidate score missing
candidate scored / baseline score missing
critical pass -> fail
critical fail -> fail
critical fail -> pass
policy-satisfied pass case
```

Update Unit 8 prose/examples so the teaching model and code model agree exactly.

## Workstream C — Unit 6 reproducible hosted experiment

Keep the simple local comparison, but add a bounded hosted-dataset version path.

The learner should be able to:

1. obtain or choose one concrete dataset version/timestamp;
2. load that same version for baseline and candidate;
3. keep evaluator and surrounding conditions fixed;
4. change one application condition;
5. compare aggregate, changed items, and trace evidence.

Do not introduce general experiment infrastructure.

## Workstream D — Unit 7 prompt reproducibility and bootstrap

### D1. Bootstrap

Provide one minimal, synthetic prompt setup path for `support/refund-answer` with the variables used by the lab and a clear label. Prefer a small idempotent helper or exact bounded UI setup instructions.

### D2. Exact-version CLI

Support mutually exclusive selection:

```text
--label staging
--version 21
```

Teach the difference:

```text
label -> routing / movable pointer
version -> historical reproducibility / immutable identity
```

### D3. Fallback provenance

State explicitly that a local fallback can preserve application availability but does not provide the same remote Langfuse prompt-version provenance/linkage as a fetched Langfuse prompt object.

Add contract tests for label and exact-version lookup selection where practical without credentials.

## Workstream E — bounded cleanup from lower-severity findings

Only take changes that directly strengthen the same merge gate:

- strengthen Unit 5 synthetic privacy test by asserting the exact allowed payload structure rather than pretending to perform generic PII detection;
- add a Unit 3 runnable context-detach variation only if it remains small and does not distract from the runtime/dependency blockers.

A second full domain/capstone scenario is not required for this PR.

## Validation sequence

1. Generate lock from the deck project.
2. Run deck-local compile + all credential-free contract tests in the locked environment.
3. Run installed-SDK smoke in the same environment.
4. Run repository `mise run test:langfuse-deck` / equivalent.
5. Run the repository deterministic validation path applicable to the change.
6. Inspect final CI status on the latest branch head.
7. Re-run a strict integration review against `adudeck-textbook` completion criteria.

## Completion statement

Before this plan is accepted, wording remains:

> Textbook coverage and first full authoring pass are complete; strict quality-pass and runtime acceptance are pending.

After all mandatory gates pass, wording may become:

> The defined 0–8 textbook scope passes the repository's strict textbook quality gate and locked local runtime contract. Live Langfuse Cloud/OpenAI evidence remains an explicitly separate validation tier.
