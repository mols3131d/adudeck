# Langfuse

Langfuse를 단순한 LLM 로그 UI가 아니라 **production execution을 관찰하고, 중요한 실패를 평가 가능한 사례로 보존하고,
변경 전후를 비교해 다시 production으로 돌려보내는 AI engineering loop**로 배운다.

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

이 deck은 current Langfuse Python SDK의 **v4 / OpenTelemetry / observations-first** model을 기준으로 한다. 오래된
`Langfuse().trace()`, `start_span()`, `start_generation()` 중심 예제는 historical context로만 보고 core learning path로
사용하지 않는다.

교본을 처음 시작한다면 먼저 [Textbook Guide](textbook/README.md)를 읽는다. 이 guide는 장별 순서뿐 아니라 prediction,
observation, validation level, 누적 checkpoint와 final assessment 기준을 설명한다.

## Goal

이 deck을 마치면 다음을 할 수 있어야 한다.

- Langfuse가 관찰하는 execution evidence와 application이 소유하는 correctness/domain truth를 구분한다.
- trace, observation, generation, session의 관계를 설명하고 Python application을 직접 instrument한다.
- observation name, input/output, metadata, tags, user/session context를 설계한다.
- OpenAI integration이 자동으로 기록하는 provider evidence와 직접 instrument해야 하는 application meaning을 구분한다.
- evaluator의 결과를 올바른 trace/observation target의 score로 연결한다.
- `score=0`, `score missing`, evaluator error, application error를 구분한다.
- production failure를 privacy-aware dataset item으로 만들고 source evidence와 연결한다.
- dataset version, evaluator, application condition을 통제해 baseline/candidate experiment를 비교한다.
- aggregate metric이 숨기는 item-level regression을 찾아 trace까지 내려가 진단한다.
- prompt version/label/cache/fallback의 의미를 설명하고 실제 generation과 prompt version을 연결한다.
- deterministic evaluator, LLM-as-a-Judge, human review의 역할과 신뢰 경계를 설명한다.
- baseline/candidate evaluation state와 coverage를 독립적으로 보존해 release decision을 만든다.
- online observation과 offline evaluation을 하나의 반복 가능한 improvement loop로 연결한다.

## Prerequisites

- Python 함수, context manager, decorator, dataclass 정도를 읽고 작은 코드를 수정할 수 있다.
- environment variable과 Python dependency 설치의 기본 개념을 안다.
- LLM API 호출이 `input → model → output`을 만든다는 흐름을 이해한다.
- JSON object와 간단한 deterministic validation을 읽을 수 있다.

OpenTelemetry와 OpenAI SDK 경험은 도움이 되지만 필수 prerequisite는 아니다. 필요한 mechanism은 deck 안에서 먼저
설명한다.

## Learning scope

Core path:

```text
AI engineering loop
→ first trace
→ trace design
→ provider integration
→ evaluation scores
→ datasets
→ experiments
→ prompt management
→ evaluation/release loop
```

현재 core scope가 아닌 것:

- Langfuse self-hosting/Kubernetes 운영
- ClickHouse/PostgreSQL 등 내부 storage architecture
- 모든 framework integration 사용법
- LLM-as-a-Judge의 심화 통계/모델 선택 연구
- annotation workforce 운영
- custom dashboard 설계
- OpenTelemetry Collector 심화 구성
- provider별 cost optimization

## Learning path

| Unit | 핵심 질문 | Material | Hands-on evidence |
| --- | --- | --- | --- |
| 0. AI Engineering Loop | 왜 trace만 보는 것으로는 개선 loop가 닫히지 않는가? | [0장](textbook/00-ai-engineering-loop/README.md) | failure → evaluation → reusable case reasoning |
| 1. First Trace | current context는 trace topology를 어떻게 만드는가? | [1장](textbook/01-first-trace/README.md) | nested vs detached observation |
| 2. Trace Design | 나중에 읽고 평가할 수 있는 trace는 어떻게 설계하는가? | [2장](textbook/02-trace-design/README.md) | stable names vs run identity |
| 3. OpenAI Integration | provider 자동 계측과 application 의미의 경계는 어디인가? | [3장](textbook/03-openai-integration/README.md) | explicit root + auto generation contract |
| 4. Scores | 실행을 어떤 질문으로 평가하고 어디에 score를 붙이는가? | [4장](textbook/04-scores/README.md) | trace vs observation score, no-score semantics |
| 5. Datasets | production failure를 어떻게 안전하고 재현 가능한 case로 만드는가? | [5장](textbook/05-datasets/README.md) | payload allowlist + source provenance |
| 6. Experiments | 같은 case population에서 baseline/candidate를 어떻게 비교하는가? | [6장](textbook/06-experiments/README.md) | pinned dataset snapshot + item regression |
| 7. Prompt Management | prompt identity를 generation/evaluation evidence와 어떻게 연결하는가? | [7장](textbook/07-prompt-management/README.md) | bootstrap + label/version + exact linkage |
| 8. Evaluation Loop | evidence를 어떻게 release decision으로 바꾸고 production으로 되돌리는가? | [8장](textbook/08-evaluation-loop/README.md) | paired evidence + regression-aware release gate |

## 핵심 mental model

Langfuse를 application source of truth로 오해하지 않는다.

```text
application / domain code
= 무엇이 올바른지 결정
= business state와 failure semantics를 소유

Langfuse
= 무엇이 실행되었는지 관찰
= evaluation evidence를 execution과 연결
= 중요한 사례를 축적
= controlled change를 비교
```

Evidence role도 분리한다.

```text
Trace / Observation
= execution evidence

Generation
= model/provider execution evidence

Score
= evaluation evidence

Dataset Item
= 반복할 case

Dataset Version
= comparison case-population identity

Experiment
= controlled comparison execution

Prompt Version
= application change identity의 한 종류

Variant Evaluation State
= 각 variant에서 평가가 실제로 완료됐는지에 대한 evidence

Release Policy
= evidence를 action으로 바꾸는 decision contract
```

## 학습 방식

각 장은 가능한 한 다음 흐름을 따른다.

```text
질문
→ mechanism / mental model
→ worked example
→ 실행 전 prediction
→ learner-visible evidence
→ 중요한 condition 하나를 변경
→ re-observe
→ misconception / failure boundary
→ transfer / assessment
```

API 문법을 외우는 것보다 **어떤 state와 evidence가 어디에서 생기고, 무엇이 바뀌면 결과가 어떻게 달라지는지** 설명하는
것을 우선한다.

## Locked local validation

Repository root에서:

```bash
mise run test:langfuse-deck
# 또는
bash scripts/test.sh langfuse-deck
```

이 target은 `decks/llmops-langfuse/pyproject.toml`과 deck-local [`uv.lock`](uv.lock)을 사용한다.

```text
env -u VIRTUAL_ENV
uv run --project decks/llmops-langfuse --locked ...
```

따라서 repository root Python environment가 우연히 test를 통과시키는 구조가 아니다.

Credential 없이 다음 두 층을 검증한다.

### Installed SDK contract

실제 locked environment에서 다음 public surface를 import/inspect한다.

```text
Langfuse client
get_client / propagate_attributes / Evaluation
observation + score surface
create_dataset_item
get_dataset(version=...)
run_experiment
get_prompt(label=..., version=...)
create_prompt
langfuse.openai.OpenAI
Responses API create surface
```

### Teaching contracts

- Unit 1: nesting/context variation
- Unit 2: stable naming/correlation attributes
- Unit 3: application span과 provider-call ownership
- Unit 4: score target과 no-score semantics
- Unit 5: exact dataset payload/provenance contract
- Unit 6: equal aggregate regression + hosted dataset version pinning
- Unit 7: compiled prompt linkage + label/version selection + bounded bootstrap
- Unit 8: independent variant states + paired comparison + regression semantics + release gate

2026-10-02의 merge-readiness run에서는 Python 3.14.6의 새 deck-local virtual environment를 만들고 lock에서 dependencies를
설치한 뒤 위 SDK smoke와 Unit 1–8 tests가 모두 통과했다. Repository `ci/validated`도 같은 validated tree에서 성공했다.

## Live labs

Locked local validation과 live integration evidence는 같은 수준이 아니다.

실제 Langfuse project 또는 OpenAI provider를 사용하면 다음을 추가로 관찰할 수 있다.

```text
Unit 1–2
Cloud trace tree / propagated attributes

Unit 3
OpenAI generation, usage, latency, provider error evidence

Unit 4
trace/observation scores in Langfuse

Unit 5
hosted dataset item + source link

Unit 6
hosted dataset snapshot + Experiment Runner UI

Unit 7
prompt label/version + generation linkage

Unit 8
experiment evidence를 실제 release policy로 해석
```

이 live tier는 credential, project state, provider 비용을 요구하므로 deterministic merge gate와 분리한다. Live API key와
customer data는 repository에 기록하지 않는다.

## Build state

2026-10-02 기준으로 **정의된 0–8 textbook scope는 strict local textbook/runtime gate를 통과한 상태**다.

완료된 merge gate:

- 0–8장 primary textbook learning path
- Units 1–8 hands-on teaching artifacts
- deck-local `uv.lock`
- declared Langfuse/OpenAI dependency environment에서 `--locked` validation
- installed Langfuse/OpenAI public API smoke
- Unit 6 hosted dataset snapshot pinning contract
- Unit 7 prompt bootstrap + mutable label / immutable version comparison
- Unit 8 independent baseline/candidate evaluation state와 paired comparison semantics
- repository deterministic CI validation

Merge completion claim에 포함하지 않는 것:

- 실제 Langfuse Cloud ingestion/rendering을 이번 CI가 증명했다는 주장
- 실제 OpenAI provider call이 이번 CI에서 성공했다는 주장
- production workload distribution에서 품질이 개선됐다는 주장

즉 이 deck은 **학습 자료와 locked local runtime contract의 merge-ready 상태**이며, live/cloud evidence는 교본이 명시적으로
분리해 가르치는 상위 validation tier다.

## Dependency contract

현재 core path가 직접 사용하는 dependency:

```toml
langfuse>=4.16,<5
openai>=3.19.2,<4
```

`langfuse.openai`는 OpenAI package를 별도로 요구하므로 둘을 deck `pyproject.toml`에 명시하고 `uv.lock`으로 해석 결과를
고정한다.

## Version baseline

작성/최종 merge-readiness 검토 기준일: **2026-10-02**

- Python learner contract: 3.10+
- repository validation runtime: Python 3.14.6
- Langfuse Python SDK reviewed baseline: `4.16.0` — 2026-09-30 latest release
- Langfuse Python SDK v4: OpenTelemetry 기반, observations-first model
- OpenAI SDK dependency contract: `openai>=3.19.2,<4`
- OpenAI provider example: Responses API

Version-sensitive API는 blog/tutorial보다 current SDK reference/source와 locked runtime evidence를 우선한다.

## Source hierarchy

기술 contract는 다음 순서로 확인한다.

1. [Langfuse Python SDK reference](https://python.reference.langfuse.com/)
2. [Langfuse current documentation](https://langfuse.com/docs)
3. [Langfuse Python SDK source/releases](https://github.com/langfuse/langfuse-python)
4. [Langfuse Academy](https://langfuse.com/academy)
5. [Langfuse Workshop](https://github.com/langfuse/langfuse-workshop)
6. [OpenAI API documentation](https://platform.openai.com/docs)
7. [Langfuse examples](https://github.com/langfuse/langfuse-examples)

Source가 충돌하면 current SDK/reference, source contract, locked runtime evidence를 우선한다.
