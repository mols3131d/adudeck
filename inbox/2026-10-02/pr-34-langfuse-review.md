# PR #34 Langfuse Deck Review

Review target: `mols3131d/adudeck#34` (`feat/langfuse-textbook-draft`)

Review date: 2026-10-02

Status recommendation: **keep Draft; do not merge yet**.

## Executive summary

PR #34 has a strong curriculum direction and a good teaching model. The central progression—observation → evaluation → dataset → experiment → improvement—fits the repository's learning principles better than a feature-by-feature Langfuse tutorial. Units 0–2 are especially promising because they separate application truth from observability/evaluation evidence and use prediction, observation, variation, and interpretation instead of simple command transcription.

The current branch is not merge-ready because two foundation gaps remain:

1. the deck dependency contract does not include the OpenAI package even though Units 3 and 7 use `langfuse.openai.OpenAI`;
2. the repository test path validates only local fake-client teaching contracts and does not execute the deck against a locked Langfuse 4.16 runtime.

The next increment should close this runtime foundation before expanding Unit 3 or later units.

## Review basis

The review used the repository's current guidance and deck skills, including:

- root `AGENTS.md`, `docs/VISON.md`, and `docs/decks.md`;
- `decks/AGENTS.md`;
- `adudeck-deck-curriculum` for the deck learning contract;
- `adudeck-textbook` for textbook quality;
- `adudeck-playground` for executable learning investigations;
- `adudeck-deck-build` for incremental build-state and acceptance boundaries;
- `mols-coding-context` / Python add-on for executable code and tests;
- `mols-loops` as the outer review loop.

Current Langfuse Python SDK v4.16.0 source/release behavior was cross-checked where version-sensitive claims materially affected the review.

## What is strong

### 1. Curriculum backbone

The deck is organized around an engineering loop rather than a list of Langfuse product features:

```text
LLM application
→ trace / observation
→ inspect failure
→ score
→ dataset
→ experiment
→ compare
→ improve
→ production observation
```

This is the right abstraction level for a primary learning resource. It teaches why the tool exists and how evidence moves through the workflow.

The deck overview also clearly separates:

- learner prerequisites;
- learning scope and explicit exclusions;
- observable outcomes;
- unit responsibilities;
- a version/authority baseline.

That makes the curriculum recoverable from the repository rather than only from conversation context.

### 2. Application truth vs observability/evaluation evidence

Unit 0's strongest idea is the explicit boundary between:

```text
application/domain code
= decides what is correct

Langfuse
= observes execution
+ stores evaluation evidence
+ accumulates reusable cases
+ compares changes
```

This prevents a common observability mistake: treating Langfuse as the source of truth for business state or correctness rules.

The same distinction is preserved through scores, datasets, experiments, and prompt management. That conceptual consistency is worth keeping.

### 3. Units 1–2 are real learning investigations

The first two units do more than show API syntax.

Unit 1 asks the learner to predict trace topology, compare IDs, inspect current context restoration, then vary one condition with `--detach-search`.

Unit 2 keeps application work stable while changing observation naming strategy, making the learner distinguish operation identity from run-specific correlation dimensions such as `user_id`, `session_id`, tags, and metadata.

This is aligned with the repository's playground contract:

```text
predict
→ run
→ observe
→ interpret
→ vary
→ re-observe
```

The credential-free tests are also correctly described as teaching-code contract tests, not proof of Langfuse Cloud behavior.

### 4. Version-sensitive Langfuse direction is mostly sound

The PR's choice to teach Python SDK v4, OpenTelemetry-based observations, `start_as_current_observation()`, `propagate_attributes()`, score APIs, prompt linkage, and OpenAI Responses integration is consistent with the reviewed Langfuse 4.16.0 source.

The deck also correctly avoids using older v2-style `Langfuse().trace()` tutorials as the default path.

## Merge blockers

### Blocker 1 — OpenAI dependency contract is incomplete

`decks/llmops-langfuse/pyproject.toml` currently contains only:

```toml
dependencies = [
  "langfuse>=4.16,<5",
]
```

However Units 3 and 7 teach:

```python
from langfuse.openai import OpenAI
```

Langfuse 4.16 does not install `openai` as a required runtime dependency. Its `langfuse.openai` module imports the OpenAI package and raises `ModuleNotFoundError` when it is unavailable.

Therefore a learner following the deck's own `uv sync` setup can reach Unit 3 with a broken environment.

This is a direct contradiction between the declared dependency contract and the textbook execution path, not merely an unverified edge case.

#### Required correction

Add an explicit OpenAI dependency compatible with the examples, preferably using the repository's current OpenAI SDK baseline unless the Langfuse deck has a justified narrower contract.

The dependency decision should be followed by lock generation and an import/API smoke check.

### Blocker 2 — no locked actual Langfuse runtime validation

`run_langfuse_deck()` currently runs repository-root Python for:

- compileall;
- `test_first_trace.py`;
- `test_trace_design.py`.

Those tests inject fake Langfuse objects. The teaching modules defer real `langfuse` imports until `main()`. As a result, the current suite can pass without proving that the declared deck environment can import or execute the Langfuse APIs used by the textbook.

The PR already states this validation boundary accurately, which is good, but it remains a merge-readiness gap.

The existing OpenAI SDK deck provides a useful repository precedent: deck-local `uv.lock`, `uv run --project ... --locked`, and direct SDK contract checks.

#### Required correction

Before accepting Units 1–2 as runtime-backed learning slices:

1. generate `decks/llmops-langfuse/uv.lock` in a network-capable environment;
2. run the Langfuse deck tests through `uv run --project decks/llmops-langfuse --locked ...`;
3. add a credential-free smoke that imports and checks the public API surfaces the deck depends on, at minimum:
   - `get_client`;
   - `propagate_attributes`;
   - `start_as_current_observation` availability on the client;
   - score/score-trace surfaces used by later units;
   - `langfuse.openai.OpenAI` once the OpenAI dependency is added.

A live Cloud/API smoke may remain outside fast CI, but the local dependency/API contract should not.

## Recommended conceptual correction

### Clarify the OpenTelemetry parent-context boundary in Unit 1

The current standalone `--detach-search` experiment is useful and correct for its setup, but its explanation can be slightly too broad if read as a universal rule:

```text
root closes
→ no current observation
→ detached search creates a new trace
```

Langfuse v4 builds on OpenTelemetry context. In a web server or another already-instrumented runtime, an outer active OpenTelemetry span can still exist after a Langfuse observation closes.

The teaching statement should therefore be narrowed to the actual experiment:

> In this standalone script, where no outer active OpenTelemetry parent remains, moving `search-policy` outside the root Langfuse observation causes it to start in a separate trace.

A stronger mental model is:

```text
current OpenTelemetry execution context
→ determines parentage

Langfuse observations
→ expose and enrich that context for LLM application observability
```

This is a refinement, not a reason to redesign the exercise.

## Units 3–8 status

Units 3–8 have a coherent sequence and mostly sound concepts, but they should remain **draft learning material**, not accepted textbook slices yet.

Compared with Units 1–2, most later units currently look like:

```text
explanation
→ API snippet
→ discussion questions
```

For textbook-level acceptance they need observable experiments and stronger assessment paths.

A good incremental target would be:

### Unit 3 — OpenAI integration

Compare:

```text
manual generation instrumentation
vs
Langfuse OpenAI auto-instrumentation
```

The learner should predict which data is automatic, inspect the resulting generation evidence, and identify which application-level spans/context still require manual ownership.

### Unit 4 — Scores

Create the same execution and attach:

- trace-level correctness;
- observation-level retrieval relevance.

The learner should explain why each target is different and distinguish `no score`, `score=0`, and evaluator failure.

### Unit 5 — Datasets

Turn a synthetic production-like failure into a dataset item with an explicit expected contract and source linkage.

### Unit 6 — Experiments

Run deterministic baseline and candidate variants on the same data and inspect an item-level regression that is hidden by an aggregate metric.

### Unit 7 — Prompt management

Run prompt version A and B under the same dataset/evaluators and verify the actual generation-to-prompt-version linkage.

### Unit 8 — Evaluation loop

Combine one production-like failure, dataset preservation, candidate change, evaluation, regression policy, and release decision into a small cumulative exercise.

## Recommended next sequence

Do not add more chapter breadth first. Close the runtime foundation, then continue slice-by-slice.

```text
1. add the OpenAI dependency
2. generate deck-local uv.lock
3. switch test:langfuse-deck to --project + --locked
4. add credential-free real SDK/API smoke
5. refine Unit 1's outer OTel-context wording
6. re-review Units 1–2 and accept them if green
7. implement Unit 3 as the next calibration slice
8. continue Units 4–8 incrementally with separate validation/review boundaries
```

## Merge-readiness matrix

| Area | Assessment |
| --- | --- |
| Curriculum / sequence | Strong |
| Core mental model | Strong |
| Current Langfuse v4 direction | Mostly verified |
| Unit 0 | Good foundation |
| Unit 1 | Good; OTel-context caveat recommended |
| Unit 2 | Good |
| Units 3–8 | Coherent drafts; not accepted slices yet |
| Dependency contract | **Blocked: OpenAI dependency missing** |
| Reproducibility | **Blocked: deck-local lock missing** |
| SDK validation | **Blocked: actual Langfuse runtime not exercised** |
| Live Cloud/UI validation | Explicitly pending; acceptable outside fast CI |
| PR state | Draft should remain Draft |

## Final assessment

The PR does not need a curriculum rewrite. Its main risk is not bad pedagogy or obsolete Langfuse concepts; it is a gap between a strong instructional design and the reproducible runtime evidence required to trust that design.

The highest-value next change is therefore **runtime foundation closure**, not additional prose. Once the dependency and locked-SDK validation boundary is closed, Units 1–2 are close to a strong accepted foundation and Unit 3 is the right next incremental learning slice.
