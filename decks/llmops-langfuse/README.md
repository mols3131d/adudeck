# Langfuse

이 deck은 Langfuse를 **LLM 실행을 관찰하고 실패를 재현 가능한 평가 사례로 바꿔, 변경의 효과를 검증하는 도구**로 배운다.

```text
실행 관찰 → 실패 진단 → 평가 기준 정의 → Dataset 보존
→ Baseline/Candidate 비교 → Release 결정 → 다시 관찰
```

학습 기준은 **Langfuse Python SDK v4 · OpenTelemetry · observations-first** 모델이다.
구형 `Langfuse().trace()`, `start_span()`, `start_generation()` 중심 예제는 현재 기본 학습 경로로 사용하지 않는다.

**처음이라면 [교본 안내](textbook/README.md) → [0장](textbook/00-ai-engineering-loop/README.md) 순서로 시작한다.**
각 장은 개념을 이해한 뒤 결과를 예측하고, 코드를 실행해 evidence를 확인하도록 구성했다.

## 학습 목표와 선수 지식

완료 후에는 다음을 직접 설명하고 실습할 수 있어야 한다.

- **관찰 설계:** trace, observation, generation, session의 관계를 이해하고 Python application에 계측을 추가한다.
  안정적인 observation 이름, input/output, metadata, tags, user/session context를 설계한다.
- **책임 구분:** provider 자동 계측과 application 의미, domain truth, evaluation evidence를 분리한다.
- **평가:** trace/observation에 올바르게 score를 연결하고 `score=0`, missing score, evaluator error, application error를
  구분한다. Deterministic evaluator, LLM-as-a-Judge, human review의 역할과 한계를 설명한다.
- **실패 보존과 비교:** privacy-aware dataset item과 source provenance를 만들고, dataset version 및 evaluator 조건을
  고정해 baseline/candidate를 비교한다. Aggregate에 숨은 item-level regression을 trace로 조사한다.
- **변경 식별과 배포 판단:** prompt version/label/cache/fallback을 구분하고 실제 generation과 연결한다. 각 variant의
  evaluation state, coverage, paired quality를 보존해 release decision을 내린다.
- **반복 개선:** online observation과 offline evaluation을 연결하고 다음 production observation에서 새 실패를 찾는다.

필요한 사전 지식은 Python의 함수·context manager·decorator·dataclass, 환경 변수와 dependency 설치, JSON과 간단한 검증,
`input → model → output` 흐름이다. OpenTelemetry와 OpenAI SDK 경험은 필수가 아니다.

## 학습 순서

| 장 | 핵심 질문 | 실습에서 확인할 것 |
| --- | --- | --- |
| [0. AI Engineering Loop](textbook/00-ai-engineering-loop/README.md) | 왜 trace만으로 개선이 끝나지 않는가? | failure → evaluation → reusable case |
| [1. First Trace](textbook/01-first-trace/README.md) | Current context는 trace 구조를 어떻게 만드는가? | nested / detached observation |
| [2. Trace Design](textbook/02-trace-design/README.md) | 나중에 찾고 평가하기 쉬운 trace는? | operation name / run identity |
| [3. OpenAI Integration](textbook/03-openai-integration/README.md) | 자동 계측과 application 책임의 경계는? | application span / provider generation |
| [4. Scores](textbook/04-scores/README.md) | 무엇을 평가하고 어디에 score를 붙이는가? | score target / missing score |
| [5. Datasets](textbook/05-datasets/README.md) | 실패를 안전하게 다시 실행하려면? | minimal payload / provenance |
| [6. Experiments](textbook/06-experiments/README.md) | 같은 조건에서 변경 효과를 어떻게 비교하는가? | pinned snapshot / item regression |
| [7. Prompt Management](textbook/07-prompt-management/README.md) | 실제 사용된 prompt version을 어떻게 증명하는가? | label / version / generation linkage |
| [8. Evaluation Loop](textbook/08-evaluation-loop/README.md) | 어떤 근거로 release를 결정하는가? | paired evidence / release gate |

각 개념의 자세한 역할, 학습 방법, 검증 수준, 누적 checkpoint와 최종 평가 기준은 [교본 안내](textbook/README.md)에서
확인한다.

**범위 밖:** self-hosting/Kubernetes, Langfuse의 ClickHouse/PostgreSQL 내부 구조, 모든 framework integration, 심화 LLM
judge 통계·모델 선택, annotation workforce 운영, custom dashboard, OpenTelemetry Collector 심화, provider별 cost
optimization.

## 실행과 검증

Repository root에서 다음 중 하나를 실행한다.

```bash
mise run test:langfuse-deck
# 또는
bash scripts/test.sh langfuse-deck
```

이 target은 `decks/llmops-langfuse/pyproject.toml`과 [deck-local `uv.lock`](uv.lock)을 사용해
`uv run --project decks/llmops-langfuse --locked` 환경에서 검사한다. Repository root의 우연한 dependency에 의존하지
않는다.

검증하는 것은 다음 두 층이다.

1. **설치된 SDK 계약:** Langfuse client, `get_client`, `propagate_attributes`, `Evaluation`, observation/score,
   `create_dataset_item`, `get_dataset(version=...)`, `run_experiment`, `get_prompt(label=..., version=...)`,
   `create_prompt`, `langfuse.openai.OpenAI`와 Responses API 표면
2. **교본 테스트:** Unit 1–8의 context, trace 설계, provider 계측, score semantics, dataset payload, hosted experiment와
   snapshot, prompt linkage·bootstrap, paired evaluation·release gate

실제 Langfuse Cloud와 OpenAI API를 사용하는 **live lab은 별도 단계**다. 그때 trace tree, generation·usage·latency,
score, hosted dataset provenance, experiment 결과, prompt-version linkage를 직접 관찰한다. Credential-free CI는 이러한
Cloud 동작이나 production 개선 효과를 증명하지 않는다. API key와 customer data를 repository에 기록하지 말고,
dataset·prompt 변경은 별도 학습용 Langfuse project에서 실습한다.

## 버전과 출처

이 교본의 **2026-10-02 작성·검토 기준**은 Langfuse Python SDK `4.16.0`(2026-09-30 출시)이었다. 이는 당시 검토한 재현
기준이며 현재 최신 버전이라는 뜻은 아니다.

- 학습자 Python 계약: 3.10+ / repository CI: Python 3.14.6
- Langfuse: `langfuse>=4.16,<5` / OpenTelemetry 기반 SDK v4
- OpenAI: `openai>=3.19.2,<4` / Responses API
- `langfuse.openai`를 사용하므로 OpenAI package도 별도 dependency로 명시하고 lock에 고정한다.

Version-sensitive 내용은 블로그보다 [Langfuse Python SDK Reference](https://python.reference.langfuse.com/),
[공식 문서](https://langfuse.com/docs), [SDK source·releases](https://github.com/langfuse/langfuse-python), locked
runtime evidence를 우선해 확인한다. 보충 학습 자료로 [Langfuse Academy](https://langfuse.com/academy),
[Workshop](https://github.com/langfuse/langfuse-workshop), [Examples](https://github.com/langfuse/langfuse-examples),
[OpenAI API 문서](https://platform.openai.com/docs)를 활용한다.
