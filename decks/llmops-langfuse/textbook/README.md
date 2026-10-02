# Langfuse Textbook Guide

이 디렉터리는 Langfuse 기능 목록을 외우는 자료가 아니라, **production execution을 관찰하고 평가 가능한 evidence로 바꾸며, 변경 전후를 비교해 release decision까지 연결하는 AI engineering loop**를 배우기 위한 교본이다.

교본 전체에서 사용하는 가장 중요한 흐름은 다음이다.

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

Langfuse의 각 기능은 이 loop에서 맡는 evidence role로 이해한다.

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

각 장에서 코드를 바로 실행하기 전에 prediction을 먼저 만든다.

```text
1. Target
   무엇을 이해하려는가?

2. Predict
   어떤 trace / score / ID / state가 보여야 하는가?

3. Run
   최소한의 실험을 실행한다.

4. Observe
   stdout, Langfuse UI, test result 중 필요한 evidence만 본다.

5. Interpret
   왜 이런 결과가 나왔는지 current context와 data flow로 설명한다.

6. Vary
   한 가지 중요한 조건만 바꾼다.

7. Re-observe
   무엇이 바뀌었고 무엇이 invariant인지 설명한다.
```

단순히 command가 성공했다는 것은 학습 완료의 evidence가 아니다.

## Evidence level을 구분한다

이 deck에는 서로 다른 validation level이 함께 존재한다. 같은 수준으로 말하지 않는다.

### Level 1 · Credential-free teaching contract

각 chapter의 local test가 주로 검증하는 것:

```text
teaching code의 control flow
payload shape
application ownership boundary
comparison/release logic
```

이 test가 통과해도 실제 Langfuse SDK나 Cloud 동작이 증명되는 것은 아니다.

### Level 2 · Installed SDK contract

Deck dependency를 실제로 설치한 환경에서 확인할 것:

```text
Langfuse/OpenAI import
public API surface
wrapper method availability
experiment API signatures
prompt/dataset/score surface
```

이 단계는 version-sensitive API drift를 잡는다.

### Level 3 · Live integration evidence

실제 Langfuse project와 필요한 provider credential을 사용해 확인할 것:

```text
trace ingestion
auto-instrumented generation
usage / latency evidence
score attachment
dataset provenance link
experiment UI
prompt-version linkage
```

### Level 4 · Production evidence

실제 workload에서만 알 수 있는 것:

```text
실제 failure distribution
real latency / cost
unexpected orchestration path
real user disagreement
missing evaluation dimensions
```

Offline pass는 production success와 동의어가 아니다.

## 핵심 invariants

교본 전체에서 다음 문장을 반복해서 확인한다.

### 1. Application truth와 observability evidence는 다르다

```text
application / domain code
= 무엇이 올바른지 결정

Langfuse
= 무엇이 실행되었는지 관찰
= evaluation evidence를 execution과 연결
= reusable cases와 comparison evidence를 관리
```

### 2. Auto instrumentation은 application meaning을 발명하지 않는다

OpenAI integration은 provider call을 generation으로 기록할 수 있다.

```text
support-turn
└─ answer-generation
```

`answer-generation`은 **OpenAI provider call 자체를 나타내는 generation observation**이다. 그 아래 별도의 provider-call child observation이 자동으로 하나 더 생긴다고 가정하지 않는다.

하지만 wrapper는 다음을 스스로 알 수 없다.

```text
왜 이 request가 business 상 중요한가
retrieval step의 의미
correctness rule
release guardrail
어떤 customer data를 기록하면 안 되는가
```

### 3. `score=0`과 `score missing`은 다르다

```text
score = 0
→ 평가를 수행했고 결과가 나쁨

score missing / evaluator error
→ 평가 자체가 완료되지 않음
```

둘을 합치면 experiment 결과를 해석할 수 없게 된다.

### 4. Aggregate와 item-level evidence를 함께 본다

```text
average ↑
```

만으로 release를 결정하지 않는다.

```text
aggregate
→ changed items
→ critical regression
→ item trace
→ failure mechanism
```

순서로 내려간다.

### 5. Dataset은 로그 복사본이 아니다

Production trace에서 중요한 failure condition을 추출해 **작고 판정 가능한 case**로 보존한다.

```text
raw production data
≠ reusable evaluation case
```

Dataset versioning도 정확히 이해한다. 현재 Langfuse dataset version은 item 변경 시점의 dataset state를 **timestamp 기반 version**으로 추적한다. Dataset schema 변화는 같은 방식의 item-version snapshot으로 간주하지 않는다.

### 6. Prompt version과 label은 다르다

```text
version
= immutable history identity

label
= 특정 version을 가리키는 mutable pointer
```

`latest`와 `production`은 같은 의미가 아니다. 요청한 label이 없으면 Langfuse가 조용히 `production`이나 `latest`로 fallback한다고 가정하지 않는다.

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
