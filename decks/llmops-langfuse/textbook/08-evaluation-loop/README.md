# 8장 · Evaluation Loop: Production Evidence에서 Release Decision까지

이제 각각의 Langfuse 기능을 외우는 단계는 끝났다.

마지막 장에서는 지금까지의 artifact를 하나의 engineering loop로 연결한다.

```text
production observation
→ failure 발견
→ expectation 정의
→ dataset case로 보존
→ candidate 하나 변경
→ experiment
→ evaluation
→ regression 조사
→ release decision
→ production에서 다시 관찰
```

좋은 loop의 기준은 기능 수가 아니다.

> **"왜 이 변경을 배포했는가?"라는 질문에 evidence chain으로 답할 수 있는가?**

## 학습 목표

- online observation과 offline evaluation이 서로 대체 관계가 아닌 이유를 설명한다.
- production failure를 reusable regression case로 바꾸는 data flow를 추적한다.
- code evaluator, LLM-as-a-Judge, human review의 신뢰 경계를 구분한다.
- aggregate metric, item-level trace, evaluator status를 함께 읽는다.
- release policy를 결과를 보기 전에 정의한다.
- evaluator error/missing score를 score 0으로 바꾸지 않는다.
- 전체 loop에서 artifact identity와 provenance가 어디에서 이어지는지 설명한다.

## 1. Online과 offline은 서로 다른 uncertainty를 줄인다

### Online observation

Production은 실제 distribution을 보여 준다.

```text
real user input
real orchestration path
real provider behavior
real latency/cost
unexpected failure
```

강점:

```text
우리가 예상하지 못한 것을 발견
```

한계:

```text
같은 condition을 통제해서 다시 비교하기 어려움
```

### Offline evaluation

Dataset experiment는 같은 cases를 반복한다.

```text
fixed cases
fixed evaluator
controlled candidate
repeatable comparison
```

강점:

```text
known behavior를 재현하고 regression을 비교
```

한계:

```text
dataset이 production distribution 전체를 대표한다고 보장하지 않음
```

그래서 loop는 양쪽을 왕복한다.

```text
production에서 discovery
→ offline에서 controlled comparison
→ deploy
→ production에서 다시 discovery
```

## 2. End-to-end worked example

### Step 1 · Production failure를 관찰한다

Trace:

```text
support-turn
├─ retrieve-policy
│  └─ output: "14일 이내 환불 가능"
└─ answer-generation
   └─ output: "환불 기간이 지났습니다."
```

Question:

```text
배송 후 10일
```

여기서 먼저 failure mechanism을 설명한다.

```text
retrieval evidence는 올바른 정책을 포함
generation output은 정책을 반대로 해석
```

단순히 "score가 낮다"보다 훨씬 actionable하다.

### Step 2 · Expectation을 정의한다

```json
{
  "input": {
    "days_since_delivery": 10
  },
  "expected_output": {
    "eligible": true,
    "policy_days": 14
  }
}
```

### Step 3 · Dataset에 보존한다

```text
regression case
→ source_trace_id로 production evidence와 연결
```

### Step 4 · Candidate를 만든다

예를 들어 prompt version을 바꾼다.

```text
baseline: prompt v20
candidate: prompt v21
```

Model/retrieval/evaluator/dataset version은 가능한 한 고정한다.

### Step 5 · Experiment를 실행한다

```text
same dataset
same evaluator

v20
vs
v21
```

### Step 6 · Aggregate와 item-level 결과를 함께 본다

```text
overall correctness
critical cases
latency
evaluator errors
```

### Step 7 · Release policy로 판정한다

```text
critical cases must pass
overall correctness must not regress
p95 latency <= limit
evaluation gaps = 0
```

### Step 8 · 배포 후 다시 관찰한다

Offline pass는 끝이 아니다.

```text
new production distribution
→ new trace evidence
→ new failure modes
```

Loop가 다시 시작된다.

## 3. Evaluation strategy: cheapest reliable evaluator를 고른다

평가 질문마다 같은 도구를 쓰지 않는다.

### Deterministic code evaluator

적합한 질문:

```text
JSON schema valid?
field == expected?
citation id가 존재?
tool argument가 range 안에 있는가?
```

장점:

- 빠르다.
- 재현 가능하다.
- 판정 rule을 직접 읽을 수 있다.

### LLM-as-a-Judge

적합할 수 있는 질문:

```text
설명이 핵심 의미를 보존하는가?
답변이 주어진 context에 grounded되어 있는가?
style guideline을 충족하는가?
```

하지만 judge도 probabilistic model이다.

```text
judge score
≠ ground truth
```

사용하기 전에 human-labeled examples와 비교해 rubric과 judge behavior를 calibration해야 한다.

### Human review

필요한 경우:

```text
새 failure mode 발견
ambiguous criterion
high-stakes judgment
automated evaluator calibration
```

Human은 비싸고 느리지만 ground truth를 형성하거나 evaluator를 검증하는 데 중요하다.

### Mental model

```text
판정 가능한 것
→ code

주관적이지만 반복 가능한 rubric
→ calibrated LLM judge

새롭거나 애매하거나 책임이 큰 판단
→ human review
```

하나의 방법이 모든 dimension에 최선은 아니다.

## 4. Metric은 production failure와 product goal에서 출발한다

Metric을 많이 만들면 evaluation이 좋아지는 것이 아니다.

먼저 실제 질문을 적는다.

```text
goal metric
무엇을 더 잘해야 하는가?

guardrail
무엇은 절대 나빠지면 안 되는가?

operational metric
latency/cost/reliability가 허용 범위인가?
```

예:

```text
goal
refund correctness

guardrail
critical policy case 모두 pass

operational
p95 latency <= 1.6s
evaluator errors = 0
```

"industry에서 많이 쓰는 metric"이라는 이유만으로 추가하지 않는다.

## 5. Release policy는 결과를 보기 전에 쓴다

Candidate 결과를 본 뒤 기준을 정하면 interpretation을 candidate에 맞추기 쉽다.

예:

```text
Policy
- critical case: 100% pass
- overall correctness: baseline보다 낮아지지 않음
- p95 latency: 1.6s 이하
- application/evaluator/missing-score gap: 0
```

이 policy는 완벽한 universal rule이 아니다.

중요한 것은 **사전에 명시된 decision contract**가 있다는 점이다.

## 6. Code lab: score만 보지 않는 release gate

[`release_gate.py`](release_gate.py)는 evidence row를 다음 상태로 구분한다.

```text
scored
application_error
evaluator_error
score_missing
```

Score가 있는 row는 baseline/candidate score를 가진다.

```python
EvidenceRow(
    case_id="critical-refund",
    critical=True,
    baseline_score=1.0,
    candidate_score=0.0,
)
```

Evaluator failure는 다음처럼 score와 분리한다.

```python
EvidenceRow(
    case_id="judge-timeout",
    critical=False,
    baseline_score=None,
    candidate_score=None,
    status="evaluator_error",
)
```

실행:

```bash
python textbook/08-evaluation-loop/release_gate.py
```

이 lab의 중요한 invariant:

```text
evaluator_error
→ candidate_score = 0 으로 강제 변환하지 않음
```

왜냐하면 "품질이 낮음"과 "품질을 측정하지 못함"은 다른 사실이기 때문이다.

## 7. Final diagnosis: 평균이 올라도 release가 막힐 수 있다

다음 결과를 보자.

```text
average correctness   0.88 → 0.91
p95 latency           1.2s → 1.5s
critical refund case  pass → fail
evaluator errors      0 → 2
```

"평균이 0.03 올랐다"만 보면 좋아 보인다.

하지만 사전 policy가:

```text
critical case must pass
evaluator errors = 0
```

이면 결론은 명확하다.

```text
DO NOT RELEASE
```

그리고 다음 action은 "평균을 더 계산한다"가 아니다.

```text
critical refund item trace 조사
evaluator error 원인 조사
```

## 8. 어떤 trace를 먼저 열 것인가?

모든 trace를 무작위로 읽지 않는다.

Information gain이 큰 순서를 생각한다.

1. **critical regression**
2. **새 application error**
3. **evaluator error / missing score**
4. 큰 score delta가 난 item
5. aggregate trend의 대표 sample

Critical regression trace에서 확인한다.

```text
input은 같은가?
dataset expected output은 같은가?
prompt/model/retrieval condition은 의도대로 고정됐는가?
실제 prompt version linkage는 맞는가?
generation output은 어떻게 달라졌는가?
evaluator가 같은 evidence를 판정했는가?
```

이렇게 trace는 "예쁜 tree"가 아니라 experiment 결과를 설명하는 diagnostic evidence가 된다.

## 9. Evaluation error를 먼저 고쳐야 하는 이유

Evaluator가 두 건 실패한 상태에서 average를 계산하면 어떤 denominator를 사용해야 하는가?

```text
실패한 evaluator를 0으로 넣기
→ quality failure로 오염

제외하고 평균내기
→ 측정 coverage 감소가 숨을 수 있음
```

따라서 release report에서는 quality와 coverage를 분리한다.

```text
correctness among valid evaluations
evaluation coverage
evaluator error count
```

Coverage가 부족하면 score 자체의 confidence가 낮아진다.

## 10. LLM judge를 쓰면 calibration artifact가 필요하다

예를 들어 `groundedness` judge를 만든다고 하자.

먼저 human-labeled examples를 만든다.

```text
case A → grounded
case B → not grounded
case C → borderline
...
```

Judge가 같은 rubric으로 얼마나 일치하는지 본다.

불일치 case를 조사한다.

```text
rubric ambiguity?
judge prompt issue?
human label disagreement?
reference context 부족?
```

그 다음에야 judge score를 experiment/online evaluation에 사용한다.

좋은 loop:

```text
human examples
→ judge calibration
→ automated evaluation
→ disagreement sampling
→ periodic human re-check
```

"LLM이 점수를 냈다"는 사실만으로 evaluator가 신뢰 가능한 것은 아니다.

## 11. Evidence chain을 끊지 않는다

최종적으로 하나의 regression case가 다음 artifact를 연결할 수 있어야 한다.

```text
production trace
      ↓ source link
dataset item
      ↓ dataset version
experiment run
      ↓ condition identity
prompt/model/app revision
      ↓
item trace
      ↓
score + evaluator identity
      ↓
release decision
      ↓
new production trace
```

각 화살표가 완벽하게 자동화될 필요는 없다.

하지만 사람이 "이 숫자가 어디서 왔지?"를 물었을 때 chain을 역추적할 수 있어야 한다.

## 12. 이 deck의 최종 mental model

기능 이름이 아니라 evidence role로 기억한다.

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
= test condition identity

Experiment
= controlled comparison execution

Prompt Version
= application change identity의 한 종류

Release Policy
= evidence를 action으로 바꾸는 decision contract
```

전체 loop:

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

## 13. Final assessment

아래 과제는 이 deck의 substantial outcomes를 한 번에 확인한다. 완성 코드보다 **설계와 evidence reasoning**이 중요하다.

### Scenario

Production support assistant에서 다음 문제가 발견됐다.

```text
특정 boundary 질문에서 policy answer가 틀림
retrieval은 올바른 document를 가져옴
현재 production prompt는 version 20
```

### 과제

다음 artifact를 설계한다.

1. **Trace diagnosis**
   - 어느 observation을 먼저 볼 것인가?
   - 어떤 evidence로 generation이 문제라고 판단하는가?

2. **Score**
   - 어떤 evaluator를 사용할 것인가?
   - trace-level인가 observation-level인가?
   - evaluator error는 어떻게 표현할 것인가?

3. **Dataset item**
   - 최소 input은 무엇인가?
   - expected output은 어떤 structured property인가?
   - 어떤 production data를 제거할 것인가?
   - source trace/observation을 어떻게 연결할 것인가?

4. **Candidate**
   - prompt version 21만 바꾼다고 가정한다.
   - 어떤 conditions를 고정할 것인가?

5. **Experiment**
   - dataset version을 어떻게 고정할 것인가?
   - 어떤 goal/guardrail/operational metric을 볼 것인가?

6. **Prompt evidence**
   - 실제 generation이 version 21을 썼다는 것을 어떻게 확인할 것인가?

7. **Release policy**
   - 결과를 보기 전에 최소 세 가지 criterion을 쓴다.

8. **Post-deploy**
   - offline pass 후 production에서 무엇을 다시 관찰할 것인가?

### 통과 기준

답안은 다음을 만족해야 한다.

```text
- execution evidence와 evaluation evidence를 섞지 않는다.
- application correctness owner를 Langfuse에 떠넘기지 않는다.
- raw production trace를 무비판적으로 dataset에 복사하지 않는다.
- baseline/candidate condition을 설명한다.
- aggregate score만으로 release를 결정하지 않는다.
- evaluator error를 score 0으로 바꾸지 않는다.
- 실제 prompt version linkage를 설명한다.
- offline evaluation이 production monitoring을 대체한다고 주장하지 않는다.
```

## 14. 이후 확장

Core loop를 이해한 뒤 별도 학습 주제로 확장할 수 있다.

- LLM-as-a-Judge rubric engineering과 statistical calibration
- Annotation Queues와 human review operations
- CI/CD regression gates
- OpenTelemetry Collector / direct OTLP ingestion
- LangChain, LlamaIndex, Agents SDK integrations
- self-hosted Langfuse operations
- dashboards / metrics API
- cost optimization

이 deck의 완료 조건은 이 기능을 모두 배우는 것이 아니다.

**현재 core scope의 AI engineering loop를 evidence와 reasoning으로 설명하고 직접 재현할 수 있는 것**이다.

## References

- [Langfuse Academy · AI Engineering Loop](https://langfuse.com/academy/ai-engineering-loop)
- [Langfuse Academy · Evaluation](https://langfuse.com/academy/evaluation)
- [Langfuse Evaluation Overview](https://langfuse.com/docs/evaluation/overview)
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)
- [OpenAI · Working with evals](https://platform.openai.com/docs/guides/evals)
- [OpenAI Graders](https://platform.openai.com/docs/guides/graders)
