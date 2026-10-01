# Langfuse

Langfuse를 단순한 LLM 로그 화면이 아니라 **LLM application을 관찰하고, 실패 사례를 재사용 가능한 평가 사례로 바꾸고,
변경 전후를 비교하는 AI engineering loop**로 배우는 deck이다.

이 deck의 중심 흐름은 다음과 같다.

```text
LLM application
→ trace / observation
→ inspect failure
→ score
→ dataset
→ experiment
→ compare
→ improve
→ 다시 production trace
```

공식 Langfuse Academy와 Workshop이 설명하는 tracing → dataset → experiment → evaluation 흐름을 참고하되,
현재 Python SDK의 실제 contract에 맞춰 **Python SDK v4 / observations-first / OpenTelemetry 기반**으로 설명한다.
오래된 `Langfuse().trace()`, `start_span()`, `start_generation()` 중심 튜토리얼은 기본 학습 경로로 사용하지 않는다.

## Goal

이 deck을 마치면 다음을 할 수 있어야 한다.

- Langfuse가 무엇을 관찰하고 무엇을 결정하지 않는지 설명한다.
- trace, observation, generation, session의 관계를 설명하고 Python application을 직접 instrument한다.
- 좋은 trace를 만들기 위해 observation name, input/output, metadata, tags, user/session context를 설계한다.
- OpenAI integration이 자동으로 수집하는 정보와 직접 instrument해야 하는 application logic을 구분한다.
- deterministic evaluator가 만든 결과를 score로 연결하고 score의 대상과 의미를 설명한다.
- production trace의 실패 사례를 dataset item으로 바꾸고 dataset version의 의미를 설명한다.
- 같은 task를 dataset에 반복 실행해 experiment를 만들고 baseline과 candidate를 비교한다.
- prompt version/label을 사용해 prompt 변경을 코드 변경과 분리하면서 trace와 experiment에 연결한다.
- online observation과 offline evaluation을 하나의 반복 가능한 개선 loop로 연결한다.

## Prerequisites

- Python 함수, context manager, decorator를 읽고 작은 코드를 수정할 수 있다.
- environment variable과 Python dependency 설치의 기본 개념을 안다.
- LLM API 호출이 `input → model → output`을 만든다는 기본 흐름을 이해한다.
- JSON object와 간단한 deterministic validation을 읽을 수 있다.

OpenTelemetry를 미리 알면 Langfuse Python SDK v4의 내부 경계를 이해하는 데 도움이 되지만 필수 prerequisite는 아니다.
OpenAI SDK 경험도 도움이 되지만 Langfuse의 핵심 개념은 특정 provider에 종속되지 않는다.

## Learning scope

Core path:

```text
AI engineering loop
→ first trace
→ trace design
→ LLM integration
→ scores
→ datasets
→ experiments
→ prompt management
→ evaluation loop
```

현재 core scope가 아닌 것:

- Langfuse self-hosting 운영과 Kubernetes 배포
- ClickHouse/PostgreSQL 등 Langfuse 내부 storage architecture
- framework별 모든 integration 사용법
- LLM-as-a-Judge calibration의 심화 통계
- annotation workforce 운영
- custom dashboard 설계
- OpenTelemetry Collector의 심화 구성
- provider별 cost 최적화

이 주제들은 core loop를 이해한 뒤 필요한 경우 extension으로 다룬다.

## Learning path

| Unit | 핵심 질문 | Material |
| --- | --- | --- |
| 0. AI Engineering Loop | 왜 trace만 보는 것으로는 LLM application을 개선하기 어려운가? | [0장](textbook/00-ai-engineering-loop/README.md) |
| 1. First Trace | Python 실행을 Langfuse의 trace와 observation으로 어떻게 표현하는가? | [1장](textbook/01-first-trace/README.md) |
| 2. Trace Design | 나중에 디버깅·평가에 쓸 수 있는 trace는 어떻게 설계하는가? | [2장](textbook/02-trace-design/README.md) |
| 3. OpenAI Integration | 자동 instrumentation은 무엇을 기록하고 무엇은 모르는가? | [3장](textbook/03-openai-integration/README.md) |
| 4. Scores | “좋다/나쁘다”는 판단을 trace와 어떻게 연결하는가? | [4장](textbook/04-scores/README.md) |
| 5. Datasets | 관찰한 실패를 어떻게 재현 가능한 test case로 바꾸는가? | [5장](textbook/05-datasets/README.md) |
| 6. Experiments | 변경 전후를 같은 dataset에서 어떻게 비교하는가? | [6장](textbook/06-experiments/README.md) |
| 7. Prompt Management | prompt를 versioned artifact로 다루면서 실행과 어떻게 연결하는가? | [7장](textbook/07-prompt-management/README.md) |
| 8. Evaluation Loop | production trace에서 개선과 회귀 방지까지 어떻게 한 loop로 닫는가? | [8장](textbook/08-evaluation-loop/README.md) |

## 핵심 mental model

Langfuse를 source of truth로 오해하지 않는다.

```text
application / domain code
= 무엇이 올바른지 결정

Langfuse
= 무엇이 실행되었는지 관찰
+ 평가 결과를 연결
+ 사례를 축적
+ 변경 전후를 비교
```

예를 들어 deterministic correctness rule이 Python 코드에 있다면 Langfuse score는 그 결과를 저장하고 비교하는 역할을
한다. Langfuse가 그 domain rule 자체를 대신 소유한다고 가정하지 않는다.

## 학습 방식

각 장은 가능한 한 다음 흐름을 따른다.

```text
질문
→ mental model
→ 작은 worked example
→ 실행/관찰 전에 예측
→ learner-visible evidence 확인
→ 한 조건을 바꿔 비교
→ 설명 또는 transfer 문제
```

## Build state

현재 textbook 0–8장은 초안 상태다. 전체를 한 번에 runnable tutorial로 확장하지 않고 각 hands-on mode를 작은 calibration
slice로 검증한 뒤 다음 단위로 진행한다.

현재 calibration slice는 **1장 First Trace**다.

- deck-local `pyproject.toml`에 `langfuse>=4.16,<5` dependency contract를 추가했다.
- `first_trace.py`는 nested baseline과 `--detach-search` variation을 같은 code path에서 비교한다.
- stdout의 `trace_id`, `observation_id`, current-context evidence와 Langfuse UI를 함께 관찰하도록 구성했다.
- `test_first_trace.py`는 external credential 없이 teaching code의 nesting/variation contract를 검증한다.
- local syntax compile과 contract test 2개는 통과했다.
- 현재 작업 환경의 network 제한 때문에 `uv.lock` 생성, Langfuse SDK 4.16.x 실제 실행, Cloud ingestion/UI 확인은 아직
  검증하지 않았다. 이 항목을 완료하기 전에는 First Trace slice의 end-to-end acceptance를 선언하지 않는다.

## Version baseline

작성/검토 기준일: **2026-10-01**

- Python: 3.10+
- Langfuse Python SDK reviewed baseline: `4.16.0` (2026-09-30)
- Python SDK v4는 OpenTelemetry 기반이며 observations-first data model을 사용한다.
- Python SDK v2 client API는 deprecated이며 새 instrumentation의 기본 경로로 사용하지 않는다.
- v3 → v4 migration에서 observation API와 attribute propagation 방식이 바뀌었으므로 오래된 예제를 그대로 복사하지
  않는다.

## Source hierarchy

기술 contract는 다음 순서로 확인한다.

1. [Langfuse Python SDK reference](https://python.reference.langfuse.com/)
2. [Langfuse current documentation](https://langfuse.com/docs)
3. [Langfuse Academy](https://langfuse.com/academy) — AI engineering lifecycle의 conceptual source
4. [Langfuse Workshop](https://github.com/langfuse/langfuse-workshop) — end-to-end teaching progression 참고
5. [Langfuse examples](https://github.com/langfuse/langfuse-examples) — 실제 integration 사례 참고

Tutorial이나 blog가 위 source와 충돌하면 current SDK/reference를 우선한다.
