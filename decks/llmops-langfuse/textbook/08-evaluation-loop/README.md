# 8장 · Evaluation Loop: Production Evidence에서 Release Decision까지

이제 각각의 Langfuse 기능을 따로 외우는 단계는 끝났다.

마지막 장의 목표는 trace, score, dataset, experiment, prompt version을 하나의 **evidence-preserving improvement loop**로 연결하는 것이다.

```text
production observation
→ failure 발견
→ failure를 설명
→ expectation 정의
→ dataset case로 보존
→ candidate 하나 변경
→ experiment
→ evaluation
→ regression 조사
→ release decision
→ production에서 다시 관찰
```

좋은 loop의 기준은 feature를 몇 개 사용했는지가 아니다.

> **"왜 이 변경을 배포했는가?"라는 질문에 evidence chain으로 답할 수 있는가?**

## 학습 목표

이 장을 마치면 다음을 할 수 있어야 한다.

- online observation과 offline evaluation이 서로 다른 uncertainty를 줄인다는 것을 설명한다.
- production trace에서 실제 failure mode를 찾아 product-specific eval로 바꾸는 흐름을 설명한다.
- deterministic evaluator, LLM-as-a-Judge, human review의 역할과 한계를 구분한다.
- human label도 절대적인 ground truth가 아닐 수 있고 disagreement 자체가 rubric 개선 evidence가 될 수 있음을 설명한다.
- aggregate metric, item-level regression, evaluation coverage를 함께 읽는다.
- release policy를 결과를 보기 전에 정의한다.
- evaluator error와 missing score를 quality score로 위장하지 않는다.
- artifact identity와 provenance를 production → dataset → experiment → release까지 역추적한다.

## 1. Online과 offline은 서로 다른 uncertainty를 줄인다

### Online observation

Production은 실제 distribution을 보여 준다.

```text
real user input
real orchestration path
real provider behavior
real latency / cost
unexpected failure
```

강점은 **우리가 예상하지 못한 failure를 발견할 수 있다는 것**이다.

하지만 production traffic은 실험실처럼 통제되지 않는다.

```text
같은 input인가?
같은 prompt인가?
같은 model인가?
같은 retrieval state인가?
같은 external condition인가?
```

이 질문에 항상 답할 수 있는 것은 아니다.

### Offline evaluation

Dataset experiment는 같은 cases를 반복할 수 있게 한다.

```text
fixed cases
fixed evaluator contract
controlled candidate
repeatable comparison
```

강점은 known behavior를 재현하고 regression을 비교할 수 있다는 것이다.

한계도 분명하다.

```text
dataset
≠ production distribution 전체
```

그래서 좋은 loop는 한쪽만 쓰지 않는다.

```text
production에서 discovery
→ offline에서 controlled comparison
→ deploy
→ production에서 다시 discovery
```

## 2. Metric보다 failure를 먼저 본다

평가를 시작할 때 가장 흔한 실수는 먼저 metric 이름을 정하는 것이다.

```text
accuracy
helpfulness
quality
relevance
```

이름만 늘어놓으면 무엇을 실패로 보는지 모호하다.

더 좋은 순서는 다음이다.

```text
trace review
→ 반복되거나 중요한 failure mode 발견
→ failure를 구체적인 판정 질문으로 바꿈
→ evaluator 선택
→ score / experiment에 연결
```

예를 들어:

```text
failure
"환불 정책 문서를 retrieval했는데 answer가 기간을 반대로 말함"

판정 질문
"최종 답변의 refund eligibility가 expected policy outcome과 일치하는가?"

가능한 evaluator
structured deterministic check
```

이렇게 하면 `quality=0.7` 같은 추상적인 metric보다 무엇을 고쳐야 하는지가 훨씬 분명하다.

Product-specific eval은 generic benchmark를 대체하려는 것이 아니라 **내 application의 실제 failure를 측정하기 위한 contract**다.

## 3. End-to-end worked example

### Step 1 · Production failure를 관찰한다

Trace:

```text
support-turn
├─ retrieve-policy
│  └─ output: "14일 이내 환불 가능"
└─ answer-generation
   └─ output: "환불 기간이 지났습니다."
```

Input fact:

```text
days_since_delivery = 10
```

여기서 중요한 것은 단순히 "답변이 나쁘다"가 아니다.

```text
retrieval evidence는 올바른 정책을 포함
generation output은 정책을 반대로 해석
```

이 설명이 있어야 다음 action을 고를 수 있다.

### Step 2 · Expectation을 구조화한다

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

문장 전체를 golden answer로 고정하지 않고 실제 domain property를 보존한다.

### Step 3 · Dataset case로 보존한다

```text
selected production failure
→ minimal reproducible case
→ source trace/observation provenance
```

### Step 4 · Candidate 하나를 바꾼다

예:

```text
baseline: prompt version 20
candidate: prompt version 21
```

가능하면 다음은 고정한다.

```text
same dataset version
same model
same retrieval condition
same evaluator definition
```

### Step 5 · Experiment를 실행한다

```text
same cases
same evaluator

v20
vs
v21
```

### Step 6 · 결과를 세 층으로 읽는다

```text
1. aggregate
2. item-level change
3. diagnostic trace
```

평균이 올랐다는 사실만으로 끝내지 않는다.

### Step 7 · Release policy로 판정한다

```text
critical cases must pass
overall correctness must not regress
p95 latency <= limit
evaluation coverage must be complete
```

### Step 8 · Production에서 다시 관찰한다

Offline pass는 끝이 아니다.

```text
new production traffic
→ new failure distribution
→ next trace review
```

Loop가 다시 시작된다.

## 4. Evaluator는 질문에 맞는 가장 단순한 도구부터 선택한다

모든 평가에 LLM judge를 쓸 필요는 없다.

### Deterministic evaluator

잘 맞는 질문:

```text
JSON schema valid?
field == expected?
required citation이 존재?
tool argument가 허용 range 안인가?
refund eligibility가 expected boolean과 같은가?
```

장점:

- 빠르다.
- 재현 가능하다.
- failure semantics가 읽기 쉽다.
- regression test로 사용하기 좋다.

### LLM-as-a-Judge

잘 맞을 수 있는 질문:

```text
설명이 핵심 의미를 보존하는가?
주어진 context에 grounded되어 있는가?
style guideline을 충족하는가?
두 답변 중 어느 쪽이 rubric을 더 잘 만족하는가?
```

하지만:

```text
judge output
≠ truth
```

Judge도 model이다. Prompt, model version, sampling, rubric ambiguity에 영향을 받는다.

### Human review

Human review가 특히 중요한 경우:

```text
새 failure mode discovery
ambiguous criterion
high-stakes judgment
LLM judge calibration
judge disagreement investigation
```

다만 human label도 자동으로 절대적인 ground truth가 되는 것은 아니다. 주관적인 task에서는 reviewer끼리 disagreement할 수 있다.

따라서 더 좋은 표현은 다음이다.

```text
human labels
= evaluator를 검증하기 위한 reference evidence
```

Reviewer disagreement가 크다면 judge를 더 복잡하게 만들기 전에 rubric 자체가 모호한지 먼저 본다.

## 5. LLM judge는 human reference와 calibration한다

`groundedness` judge를 만든다고 하자.

먼저 representative examples를 human이 판정한다.

```text
case A → pass
case B → fail
case C → borderline / disagreement
...
```

그 다음 judge가 같은 cases를 평가한다.

비교할 질문:

```text
judge와 human reference가 어디에서 일치하는가?
어디에서 체계적으로 틀리는가?
false positive / false negative 중 어느 쪽이 더 위험한가?
어떤 rubric 문장이 애매한가?
특정 segment에서만 disagreement가 커지는가?
```

좋은 calibration loop:

```text
human reference examples
→ judge prompt/rubric
→ disagreement analysis
→ rubric 또는 judge 수정
→ re-evaluate
→ production/experiment에 사용
→ 주기적으로 human sample 재검토
```

Judge score 하나만 보고 신뢰성을 가정하지 않는다.

## 6. Quality와 evaluation coverage를 분리한다

다음 run을 보자.

```text
100 items
90 items scored
10 evaluator errors

valid-score average = 0.94
```

`0.94`만 보면 매우 좋아 보인다.

하지만 10개를 평가하지 못했다.

그래서 최소한 두 축을 본다.

```text
quality among valid evaluations
evaluation coverage
```

가능하면 failure count도 분리한다.

```text
application_error_count
evaluator_error_count
score_missing_count
```

### 왜 evaluator error를 0으로 바꾸면 안 되는가?

```text
A. output을 정상적으로 평가
→ fail
→ score = 0

B. evaluator timeout
→ 판단하지 못함
→ evaluator_error
```

B를 0으로 바꾸면 application quality failure와 evaluation infrastructure failure를 구분할 수 없다.

반대로 error row를 평균에서 조용히 제외하면 coverage 감소가 숨을 수 있다.

따라서 quality와 coverage를 둘 다 report한다.

## 7. Release policy는 결과를 보기 전에 정의한다

Candidate 결과를 본 뒤 기준을 만들면 candidate에 유리하게 threshold를 조정하기 쉽다.

예:

```text
Release Policy

- critical case: 100% pass
- overall correctness: baseline보다 낮아지지 않음
- p95 latency: 1.6s 이하
- application/evaluator/missing-score gap: 0
```

이 숫자가 universal best practice라는 뜻은 아니다.

중요한 것은:

```text
result 보기 전
→ decision contract 정의
```

라는 순서다.

## 8. Code lab: score만 보지 않는 release gate

[`release_gate.py`](release_gate.py)는 evidence row를 다음 상태로 분리한다.

```text
scored
application_error
evaluator_error
score_missing
```

Score가 있는 row:

```python
EvidenceRow(
    case_id="critical-refund",
    critical=True,
    baseline_score=1.0,
    candidate_score=0.0,
)
```

Evaluator failure:

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

핵심 invariant:

```text
evaluator_error
→ candidate_score = 0으로 강제 변환하지 않음
```

## 9. 평균이 올라도 release가 막힐 수 있다

다음 결과를 보자.

```text
average correctness   0.88 → 0.91
p95 latency           1.2s → 1.5s
critical refund case  pass → fail
evaluator errors      0 → 2
```

평균만 보면 candidate가 좋아 보인다.

하지만 policy가:

```text
critical case must pass
evaluator errors = 0
```

이면 결론은:

```text
DO NOT RELEASE
```

이다.

다음 action은 평균을 더 계산하는 것이 아니다.

```text
critical regression trace 조사
evaluator errors 조사
```

## 10. 어떤 trace를 먼저 열 것인가?

모든 trace를 무작위로 읽지 않는다.

Information gain이 큰 순서를 사용할 수 있다.

1. critical regression
2. 새 application error
3. evaluator error / missing score
4. 큰 score delta가 난 item
5. aggregate trend의 대표 sample

Critical regression을 열면 다음을 확인한다.

```text
input은 같은가?
dataset expected output은 같은가?
dataset version은 같은가?
prompt/model/retrieval condition은 의도대로 고정됐는가?
실제 prompt-version linkage는 맞는가?
generation output은 어떻게 달라졌는가?
evaluator가 같은 evidence를 판정했는가?
```

Trace는 dashboard 장식이 아니라 **experiment result를 설명하는 diagnostic evidence**다.

## 11. Aggregate, segment, example을 왕복한다

좋은 evaluation review는 세 level을 오간다.

```text
aggregate
→ 전체 방향

segment
→ 특정 category/user journey/failure mode에서만 문제가 있는가?

example
→ 실제 item trace에서 mechanism이 무엇인가?
```

예:

```text
overall 0.91
refund 0.98
shipping 0.93
subscription 0.61
```

Overall만 보면 subscription regression이 숨는다.

따라서 dataset metadata와 failure taxonomy가 중요한 query dimension이 된다.

## 12. Evidence chain을 끊지 않는다

최종적으로 하나의 regression case가 다음 artifact를 연결할 수 있어야 한다.

```text
production trace
      ↓ source provenance
dataset item
      ↓ dataset version
experiment run
      ↓ condition identity
prompt/model/app revision
      ↓
item trace
      ↓
score + evaluator identity/status
      ↓
release decision
      ↓
new production trace
```

모든 화살표가 자동화될 필요는 없다.

하지만 사람이 "이 숫자가 어디서 왔지?"라고 물었을 때 역추적할 수 있어야 한다.

## 13. 이 deck의 최종 mental model

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

## 14. Final assessment

아래 과제는 이 deck의 주요 learning outcome을 한 번에 확인한다.

### Scenario

Production support assistant에서 다음 문제가 발견됐다.

```text
특정 boundary 질문에서 policy answer가 틀림
retrieval은 올바른 document를 가져옴
현재 production prompt는 version 20
```

### 과제 A · Diagnosis

설계한다.

```text
어떤 observation을 먼저 볼 것인가?
retrieval 문제가 아니라 generation 문제라고 판단하려면 어떤 evidence가 필요한가?
어떤 additional context가 trace에 있어야 하는가?
```

### 과제 B · Evaluator

정한다.

```text
평가 질문
trace-level인가 observation-level인가
code / LLM judge / human 중 어떤 방법을 쓸 것인가
score 0과 evaluator error를 어떻게 구분할 것인가
```

### 과제 C · Dataset promotion

정한다.

```text
최소 input
structured expected output
제거해야 할 production data
source trace/observation provenance
failure mode metadata
```

### 과제 D · Candidate experiment

Prompt version 21만 바꾼다고 가정한다.

```text
고정할 conditions
dataset version
evaluator identity
goal metric
guardrail
operational metric
release blocker
```

### 과제 E · Result interpretation

결과:

```text
overall correctness   0.86 → 0.91
critical boundary     pass → fail
p95 latency           1.0s → 1.3s
3 evaluator errors
```

답한다.

1. Release할 것인가?
2. 가장 먼저 조사할 item은 무엇인가?
3. Evaluator errors를 평균에 0으로 넣지 않는 이유는 무엇인가?
4. Candidate가 좋아졌다는 주장을 하려면 어떤 evidence gap을 먼저 닫아야 하는가?
5. Deploy 후 어떤 production observation으로 loop를 다시 시작할 것인가?

## 15. Self-review rubric

자신의 답을 다음 기준으로 검토한다.

### Evidence fidelity

- 관찰한 사실과 추론한 원인을 구분했는가?
- local contract와 live runtime evidence를 구분했는가?

### Evaluation quality

- evaluator가 실제 failure mode를 측정하는가?
- judge를 쓴다면 human reference와 calibration 계획이 있는가?
- quality와 evaluation coverage를 분리했는가?

### Experimental discipline

- baseline/candidate가 같은 cases를 사용하는가?
- material condition을 통제하거나 차이를 기록했는가?
- aggregate와 item-level evidence를 함께 봤는가?

### Decision quality

- release policy가 사전에 정의됐는가?
- critical regression을 평균으로 덮지 않았는가?
- offline pass를 production success로 과장하지 않았는가?

## References

- [Langfuse Evaluation Overview](https://langfuse.com/docs/evaluation/overview)
- [Langfuse Evaluation Core Concepts](https://langfuse.com/docs/evaluation/core-concepts)
- [Langfuse Academy · Evaluation](https://langfuse.com/academy/evaluation)
- [Langfuse Academy · Experiments](https://langfuse.com/academy/experiments)
- [Langfuse Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Langfuse Workshop](https://github.com/langfuse/langfuse-workshop)
- [Hamel Husain · Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)
- [Hamel Husain · Using LLM-as-a-Judge For Evaluation](https://hamel.dev/blog/posts/llm-judge/)
