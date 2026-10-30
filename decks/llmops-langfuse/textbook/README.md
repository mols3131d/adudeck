# Langfuse Textbook Guide

이 교본은 Langfuse 기능 목록보다
**실행을 관찰하고, 실패를 평가 가능한 사례로 보존하고, 변경을 비교해 release를 결정하는 과정**에 집중한다.

학습 흐름은 다음과 같다.

```text
Observe
→ Explain
→ Preserve
→ Change
→ Compare
→ Evaluate
→ Decide
→ Observe again
```

각 기능은 loop에서 맡는 **evidence 역할**로 이해한다.

| 개념 | 어떤 근거를 남기는가 |
| --- | --- |
| Trace / Observation | Application 실행 |
| Generation | Model/provider 호출 |
| Score | 평가 결과 |
| Dataset Item | 다시 검증할 case |
| Dataset Version | 비교 대상 집합의 조건 |
| Experiment | 통제된 변경 비교 |
| Prompt Version | 변경된 application 조건의 식별자 중 하나 |
| Release Policy | 평가 근거를 행동으로 바꾸는 기준 |

## 이 교본을 읽는 순서

가능하면 0장부터 8장까지 순서대로 진행한다.

| Unit | 핵심 competence | 다음 장에 필요한 이유 |
| --- | --- | --- |
| [0. AI Engineering Loop](00-ai-engineering-loop/README.md) | observation과 evaluation을 분리하고 전체 개선 loop를 설명한다 | 이후 기능을 product feature가 아니라 evidence 역할로 이해한다 |
| [1. First Trace](01-first-trace/README.md) | current execution context가 observation topology를 만드는 방식을 설명한다 | auto instrumentation과 distributed parentage를 이해하는 기반이다 |
| [2. Trace Design](02-trace-design/README.md) | stable operation identity와 run-specific correlation을 분리한다 | 나중에 filter, dataset promotion, evaluation target을 신뢰할 수 있다 |
| [3. OpenAI Integration](03-openai-integration/README.md) | provider telemetry와 application meaning의 ownership을 분리한다 | generation evidence를 평가와 experiment에 연결할 수 있다 |
| [4. Scores](04-scores/README.md) | evaluator 질문, target, score semantics를 설계한다 | 실행 결과를 평가 가능한 evidence로 바꾼다 |
| [5. Datasets](05-datasets/README.md) | production failure를 안전한 reusable case로 보존한다 | 같은 failure를 다음 변경에서도 다시 시험할 수 있다 |
| [6. Experiments](06-experiments/README.md) | 같은 cases와 evaluator 아래 baseline/candidate를 비교한다 | aggregate와 item-level regression을 함께 판단한다 |
| [7. Prompt Management](07-prompt-management/README.md) | prompt version identity를 실제 generation과 연결한다 | “무엇을 바꿨는가?”를 evidence chain에 포함한다 |
| [8. Evaluation Loop](08-evaluation-loop/README.md) | online/offline evidence를 release policy로 연결한다 | 전체 개선 loop를 독립적으로 설계하고 설명한다 |

## 학습 방법

각 장에서는 다음 순서로 실습한다.

1. **Target:** 무엇을 이해할지 정한다.
2. **Predict:** 예상 trace, score, ID, state를 기록한다.
3. **Run:** 최소 실험을 실행한다.
4. **Observe:** stdout, Langfuse UI, test 결과에서 실제 evidence를 찾는다.
5. **Interpret:** current context와 data flow로 원인을 설명한다.
6. **Vary:** 중요한 조건 하나를 바꾼다.
7. **Re-observe:** 바뀐 결과와 유지된 invariant를 비교한다.

**Command 성공은 학습 완료의 증거가 아니다.** 예상과 관찰의 차이를 설명할 수 있어야 한다.

## 검증 결과를 읽는 법

서로 다른 검증 수준을 같은 성공으로 취급하지 않는다.

| 수준 | 직접 확인하는 근거 | 증명하지 못하는 것 |
| --- | --- | --- |
| **1. Credential-free teaching contract** | 교본 코드의 control flow, payload, application ownership, comparison/release 로직 | 실제 SDK 또는 Cloud 동작 |
| **2. Installed SDK contract** | Langfuse/OpenAI import, public API, wrapper·experiment signature, prompt/dataset/score 표면 | Live project에서의 실행 성공 |
| **3. Live integration evidence** | Trace ingestion, auto generation, usage/latency, score, dataset provenance, experiment UI, prompt-version linkage | 실제 production 분포의 품질 |
| **4. Production evidence** | 실제 failure 분포, latency/cost, 예외 경로, 사용자 의견 불일치, 평가 누락 차원 | 통제된 비교 실험의 인과 관계 |

특히 **offline pass는 production success가 아니다.** 학습용 local test가 통과했다고 Langfuse Cloud나 provider를 실제로
호출한 것으로 설명하지 않는다.

## 핵심 invariants

교본 전체에서 다음 문장을 반복해서 확인한다.

### 1. Application truth와 observability evidence는 다르다

**Application/domain code**가 올바른 결과와 실패 의미를 결정한다. **Langfuse**는 실행을 관찰하고 evaluation evidence를
연결하며, 재사용할 case와 비교 결과를 관리한다.

### 2. Auto instrumentation은 application meaning을 발명하지 않는다

OpenAI integration은 provider call을 generation으로 기록할 수 있다.

```text
support-turn
└─ answer-generation
```

`answer-generation`은 **OpenAI provider call 자체를 나타내는 generation observation**이다. 그 아래 별도의 provider-call
child observation이 자동으로 하나 더 생긴다고 가정하지 않는다.

하지만 wrapper는 request의 business 의미, retrieval step의 목적, correctness rule, release guardrail, 기록을 피해야 할
customer data를 스스로 정하지 못한다.

### 3. `score=0`과 `score missing`은 다르다

`score=0`은 **평가를 마쳤고 결과가 나쁨**, missing score나 evaluator error는 **평가가 완료되지 않음**을 뜻한다. 둘을
합치면 실험 결과를 잘못 해석한다.

### 4. Aggregate와 item-level evidence를 함께 본다

평균이 좋아졌다는 이유만으로 release하지 않는다.
**Aggregate → changed items → critical regression → item trace → failure mechanism** 순서로 내려가 원인을 확인한다.

### 5. Dataset은 로그 복사본이 아니다

Production trace에서 중요한 failure condition을 추출해 **작고 판정 가능한 case**로 보존한다.

Raw production data는 reusable evaluation case와 같지 않다.

Dataset versioning도 정확히 이해한다. 현재 Langfuse dataset version은 item 변경 시점의 dataset state를
**timestamp 기반 version**으로 추적한다. Dataset schema 변화는 같은 방식의 item-version snapshot으로 간주하지 않는다.

### 6. Prompt version과 label은 다르다

`version`은 **immutable history identity**, `label`은 특정 version을 가리키는 **mutable pointer**다.

`latest`와 `production`은 같은 의미가 아니다. 요청한 label이 없으면 Langfuse가 조용히 `production`이나 `latest`로
fallback한다고 가정하지 않는다.

## 연습과 평가의 기준

이 교본의 exercise는 API 암기보다 다음 능력을 본다.

- **Prediction** — 실행 전에 topology/state/evidence를 예상한다.
- **Tracing** — ID와 current context의 관계를 추적한다.
- **Explanation** — 결과가 나온 이유를 mechanism으로 설명한다.
- **Comparison** — baseline/candidate의 controlled difference를 구분한다.
- **Debugging** — score가 아니라 trace로 내려가 failure mechanism을 찾는다.
- **Design** — observation/score/dataset/evaluator boundary를 설계한다.
- **Transfer** — support/refund 예제를 새로운 application에 적용한다.
- **Synthesis** — production failure부터 release decision까지 전체 loop를 연결한다.

## 누적 checkpoint

### Checkpoint A · Observability foundation

0–2장을 마친 뒤 다음을 설명할 수 있어야 한다.

```text
trace vs observation
current OpenTelemetry context
stable operation name
user/session/tags/metadata
root input/output
privacy/export boundary
```

### Checkpoint B · Provider + evaluation

3–4장을 마친 뒤 다음을 설명할 수 있어야 한다.

```text
application span vs provider generation
provider telemetry vs business meaning
trace-level vs observation-level score
score 0 vs no score
deterministic evaluator ownership
```

### Checkpoint C · Reusable regression loop

5–6장을 마친 뒤 다음을 설계할 수 있어야 한다.

```text
production failure
→ minimal dataset item
→ fixed dataset condition
→ baseline/candidate
→ evaluator
→ aggregate + item-level comparison
```

### Checkpoint D · Change identity + release decision

7–8장을 마친 뒤 다음 evidence chain을 설명할 수 있어야 한다.

```text
production trace
→ dataset item
→ dataset version
→ experiment
→ prompt/model/app condition
→ item trace
→ score/evaluator
→ release policy
→ production observation
```

## Final assessment rubric

8장의 final assessment를 수행할 때 다음 네 가지를 기준으로 스스로 검토한다.

### 1. Evidence fidelity

- 관찰한 사실과 추정한 원인을 구분했는가?
- fake/local contract와 live runtime evidence를 구분했는가?
- evaluator failure를 low score로 위장하지 않았는가?

### 2. Experimental discipline

- baseline/candidate가 같은 cases를 사용하는가?
- material condition을 고정하거나 차이를 명시했는가?
- aggregate만 보지 않고 item regression을 조사했는가?

### 3. Ownership clarity

- domain truth의 owner가 분명한가?
- provider telemetry와 application context를 구분했는가?
- prompt/dataset/evaluator version identity가 재현 가능하게 남아 있는가?

### 4. Decision quality

- release criterion이 결과를 본 뒤 즉흥적으로 만들어지지 않았는가?
- critical regression과 evaluation coverage를 별도로 확인했는가?
- offline evidence의 한계를 인정하고 production observation으로 loop를 다시 닫는가?

## Source strategy

Version-sensitive contract는 blog post보다 현재 primary source를 우선한다.

권장 우선순위:

1. [Langfuse Python SDK Reference](https://python.reference.langfuse.com/)
2. [Langfuse Documentation](https://langfuse.com/docs)
3. [Langfuse Python SDK source/releases](https://github.com/langfuse/langfuse-python)
4. [Langfuse Academy](https://langfuse.com/academy)
5. [Langfuse Workshop](https://github.com/langfuse/langfuse-workshop)
6. [OpenAI API Documentation](https://platform.openai.com/docs)

교수법과 evaluation practice를 보완하는 참고 자료:

- [Hamel Husain · Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)
- [Hamel Husain · Using LLM-as-a-Judge For Evaluation](https://hamel.dev/blog/posts/llm-judge/)

이 외부 자료에서 특히 유지할 원칙은 다음이다.

```text
failure mode에서 eval을 시작한다
product-specific behavior를 평가한다
가능하면 deterministic check를 먼저 쓴다
LLM judge는 human labels와 calibration한다
평균 metric보다 실제 failure examples를 계속 본다
```

이 원칙들은 Langfuse 기능을 많이 쓰기 위한 규칙이 아니라 **신뢰할 수 있는 AI engineering loop를 만들기 위한 규칙**이다.
