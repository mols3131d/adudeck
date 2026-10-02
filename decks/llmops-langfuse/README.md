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
- evaluator의 결과를 올바른 trace/observation/session target의 score로 연결한다.
- `score=0`, `score missing`, evaluator error, application error를 구분한다.
- production failure를 privacy-aware dataset item으로 만들고 source evidence와 연결한다.
- dataset version, evaluator, application condition을 통제해 baseline/candidate experiment를 비교한다.
- aggregate metric이 숨기는 item-level regression을 찾아 trace까지 내려가 진단한다.
- prompt version/label/cache를 설명하고 실제 generation과 prompt version을 연결한다.
- deterministic evaluator, LLM-as-a-Judge, human review의 역할과 신뢰 경계를 설명한다.
- online observation과 offline evaluation을 release decision까지 하나의 반복 가능한 loop로 연결한다.

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

이 주제들은 core loop를 이해한 뒤 extension deck으로 다룰 수 있다.

## Learning path

| Unit | 핵심 질문 | Material | Hands-on evidence |
| --- | --- | --- | --- |
| 0. AI Engineering Loop | 왜 trace만 보는 것으로는 개선 loop가 닫히지 않는가? | [0장](textbook/00-ai-engineering-loop/README.md) | failure → evaluation → reusable case reasoning |
| 1. First Trace | current context는 trace topology를 어떻게 만드는가? | [1장](textbook/01-first-trace/README.md) | nested vs detached observation |
| 2. Trace Design | 나중에 읽고 평가할 수 있는 trace는 어떻게 설계하는가? | [2장](textbook/02-trace-design/README.md) | stable names vs run identity |
| 3. OpenAI Integration | provider 자동 계측과 application 의미의 경계는 어디인가? | [3장](textbook/03-openai-integration/README.md) | explicit root + auto generation contract |
| 4. Scores | 실행을 어떤 질문으로 평가하고 어디에 score를 붙이는가? | [4장](textbook/04-scores/README.md) | trace vs observation score, no-score semantics |
| 5. Datasets | production failure를 어떻게 안전하고 재현 가능한 test case로 만드는가? | [5장](textbook/05-datasets/README.md) | structured case + source provenance |
| 6. Experiments | 같은 dataset에서 baseline/candidate를 어떻게 비교하는가? | [6장](textbook/06-experiments/README.md) | equal aggregate + critical regression |
| 7. Prompt Management | prompt identity를 generation/evaluation evidence와 어떻게 연결하는가? | [7장](textbook/07-prompt-management/README.md) | compile + exact prompt-version linkage |
| 8. Evaluation Loop | evidence를 어떻게 release decision으로 바꾸고 production으로 되돌리는가? | [8장](textbook/08-evaluation-loop/README.md) | regression-aware release gate |

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

예를 들어 환불 가능 여부를 결정하는 domain rule이 Python/service code에 있다면 Langfuse score는 그 rule의 결과를
execution evidence와 연결한다. Langfuse가 환불 정책 자체의 canonical owner가 되는 것은 아니다.

## Evidence roles

이 deck 전체에서 다음 구분을 유지한다.

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
= test-set condition identity

Experiment
= controlled comparison execution

Prompt Version
= application change identity의 한 종류

Release Policy
= evidence를 action으로 바꾸는 decision contract
```

## 학습 방식

각 장은 가능한 한 다음 흐름을 따른다.

```text
질문
→ mechanism / mental model
→ worked example
→ 실행 전에 prediction
→ learner-visible evidence
→ 한 조건을 바꿔 re-observe
→ failure/misconception
→ transfer / assessment
```

API 문법을 외우는 것보다 **어떤 state와 evidence가 어디에서 생기고, 무엇이 바뀌면 결과가 어떻게 달라지는지** 설명하는
것을 우선한다.

## Running the credential-free textbook contracts

Repository root에서:

```bash
mise run test:langfuse-deck
# 또는
bash scripts/test.sh langfuse-deck
```

현재 contract suite는 Units 1–8의 teaching code를 외부 credential 없이 실행한다.

이 test는 주로 다음을 검증한다.

- Unit 1: nesting/context variation
- Unit 2: stable naming/correlation attributes
- Unit 3: application span과 provider-call ownership
- Unit 4: score target과 no-score semantics
- Unit 5: dataset case/provenance contract
- Unit 6: aggregate가 숨기는 item-level regression
- Unit 7: compiled prompt와 exact prompt object linkage
- Unit 8: critical regression/evaluation gap을 고려하는 release gate

## Live labs

다음 장은 실제 Langfuse project 또는 OpenAI provider 호출을 통해 learner-visible evidence를 추가로 관찰할 수 있다.

```text
Unit 1–2
Langfuse trace tree / propagated attributes

Unit 3
OpenAI generation, usage, latency

Unit 4
trace/observation scores

Unit 5
hosted dataset item + source link

Unit 6
Langfuse Experiment Runner

Unit 7
prompt label/version + generation linkage

Unit 8
experiment evidence를 release policy로 해석
```

Live API key와 customer data는 repository에 기록하지 않는다.

## Build state

2026-10-02 기준으로 **0–8장 textbook learning path와 Units 1–8의 hands-on teaching artifacts는 작성되어 있다.**

현재 branch에 기록된 deterministic validation evidence:

- Units 3–8의 credential-free contract tests는 Python 3.13에서 통과한 것으로 기록되어 있다.
- 새 Python files는 syntax compile을 통과한 것으로 기록되어 있다.
- Unit 6 local demo는 baseline/candidate aggregate가 같아도 critical regression이 존재하는 evidence를 출력한다.
- Unit 8 release gate는 critical regression과 evaluator error가 있는 candidate를 block한다.

이번 textbook review에서 추가로 확인한 것:

- Langfuse Python SDK latest release는 `v4.16.0`이며 current v4/OpenTelemetry path와 일치한다.
- Unit 3의 `answer-generation`은 wrapped OpenAI provider call 자체를 표현하는 generation으로 설명을 보정했다.
- Unit 8은 failure-driven eval design, evaluation coverage, human-reference calibration, release policy를 포함하도록 심화했다.
- `textbook/README.md`에 validation level, 누적 checkpoint, final assessment rubric을 추가했다.

아직 end-to-end acceptance로 주장하지 않는 것:

- deck-local `uv.lock`
- locked Langfuse/OpenAI runtime에서의 전체 suite
- Langfuse SDK 4.16.x actual import/API smoke in this execution environment
- Langfuse Cloud ingestion/UI behavior
- OpenAI live provider calls

현재 작업 환경에서 external package resolution이 보장되지 않으므로 lockfile을 추측해서 만들지 않는다.

Textbook content와 deterministic learning contracts가 작성되었다는 것과
**locked/live runtime acceptance가 완료되었다는 것**은 분리해서 기록한다.

## Dependency contract

현재 deck은 다음 integration을 core path에서 직접 사용한다.

```text
Langfuse Python SDK v4
OpenAI Python SDK
```

`langfuse.openai`는 OpenAI package가 별도로 설치되어 있어야 하므로 두 dependency를 모두 deck `pyproject.toml`에
명시한다.

## Version baseline

작성/검토 기준일: **2026-10-02**

- Python: 3.10+
- Langfuse Python SDK reviewed baseline: `4.16.0` (2026-09-30 latest release 확인)
- Langfuse Python SDK v4: OpenTelemetry 기반, observations-first model
- OpenAI SDK deck compatibility baseline: `openai>=3.19.2,<4`
- OpenAI provider example: Responses API

Version-sensitive API는 blog/tutorial보다 current SDK/reference/source를 우선한다.

## Source hierarchy

기술 contract는 다음 순서로 확인한다.

1. [Langfuse Python SDK reference](https://python.reference.langfuse.com/)
2. [Langfuse current documentation](https://langfuse.com/docs)
3. [Langfuse Python SDK source/releases](https://github.com/langfuse/langfuse-python)
4. [Langfuse Academy](https://langfuse.com/academy) — AI engineering lifecycle의 conceptual source
5. [Langfuse Workshop](https://github.com/langfuse/langfuse-workshop) — end-to-end teaching progression
6. [OpenAI API documentation](https://platform.openai.com/docs) — provider/evaluation practice
7. [Langfuse examples](https://github.com/langfuse/langfuse-examples) — integration examples

Source가 충돌하면 current SDK/reference와 actual source contract를 우선한다.
