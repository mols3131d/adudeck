# 8장 · Evaluation Loop: Production Evidence에서 Release Decision까지

이제 각각의 Langfuse 기능을 따로 외우는 단계는 끝났다.

마지막 장의 목표는 trace, score, dataset version, experiment, prompt version을 하나의
**evidence-preserving improvement loop**로 연결하는 것이다.

```text
production observation
→ failure 발견
→ failure mechanism 설명
→ expectation 정의
→ dataset case로 보존
→ candidate 하나 변경
→ controlled experiment
→ evaluation
→ regression 조사
→ release decision
→ production에서 다시 관찰
```

좋은 loop의 기준은 feature 수가 아니다.

> **"왜 이 변경을 배포했는가?"라는 질문에 evidence chain으로 답할 수 있는가?**

## 학습 목표

이 장을 마치면 다음을 할 수 있어야 한다.

- online observation과 offline evaluation이 서로 다른 uncertainty를 줄인다는 것을 설명한다.
- production failure를 product-specific evaluator contract로 바꾸는 흐름을 설명한다.
- deterministic evaluator, LLM-as-a-Judge, human review의 역할과 한계를 구분한다.
- baseline과 candidate의 evaluation state를 독립적으로 추적한다.
- quality와 evaluation coverage를 분리하고 paired comparison population을 정의한다.
- critical failure와 newly introduced regression을 구분한다.
- release policy를 결과를 보기 전에 정의한다.
- evaluator error와 missing score를 quality score로 위장하지 않는다.
- production → dataset → experiment → prompt/model/app condition → score → release까지 provenance를 역추적한다.

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

강점:

```text
우리가 예상하지 못한 failure를 발견할 수 있음
```

한계:

```text
같은 input인가?
같은 prompt인가?
같은 model인가?
같은 retrieval state인가?
같은 external condition인가?
```

을 통제하기 어렵다.

### Offline evaluation

Dataset experiment는 같은 cases를 반복할 수 있게 한다.

```text
fixed dataset snapshot
fixed evaluator contract
controlled candidate
repeatable comparison
```

강점:

```text
known behavior를 재현하고 change를 비교할 수 있음
```

한계:

```text
dataset
≠ production distribution 전체
```

따라서 둘은 대체 관계가 아니다.

```text
production에서 discovery
→ offline에서 controlled comparison
→ release
→ production에서 다시 discovery
```

## 2. Metric 이름보다 failure를 먼저 본다

평가를 시작할 때 먼저 다음 단어를 고르는 것은 쉽다.

```text
accuracy
quality
helpfulness
relevance
groundedness
```

하지만 metric 이름만으로는 무엇을 실패라고 부르는지 모호하다.

더 좋은 순서는 다음이다.

```text
trace review
→ 반복되거나 중요한 failure 발견
→ failure mechanism 설명
→ 판정 가능한 질문으로 변환
→ 가장 단순한 신뢰 가능한 evaluator 선택
```

예:

```text
observed failure
"올바른 환불 정책 문서를 retrieval했지만 답변이 eligibility를 반대로 말함"

판정 질문
"최종 output의 eligible 값이 expected policy outcome과 같은가?"

evaluator
structured deterministic equality check
```

`quality=0.7`보다 무엇을 고쳐야 하는지가 훨씬 명확하다.

## 3. End-to-end worked example

### Step 1 · Production trace에서 failure를 찾는다

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

Evidence를 분리한다.

```text
observed
- retrieval output에 올바른 policy가 있음
- generation output은 eligibility를 반대로 표현

hypothesis
- generation/prompt reasoning path가 policy를 잘못 사용했을 가능성
```

관찰한 사실과 원인 추정을 같은 문장으로 만들지 않는다.

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

문장 전체를 golden answer로 고정하기보다 실제 domain property를 보존한다.

### Step 3 · Dataset case로 보존한다

```text
production evidence
→ 최소 재현 조건 추출
→ source trace/observation provenance 유지
→ hosted dataset item
```

### Step 4 · Dataset snapshot을 고정한다

Unit 6에서 배운 대로 baseline/candidate가 같은 timestamp version을 사용한다.

```text
dataset = support/refund-policy
version = T
```

### Step 5 · Candidate 하나를 바꾼다

```text
baseline prompt version = 20
candidate prompt version = 21
```

가능하면 다음은 고정한다.

```text
same dataset version
same model
same retrieval configuration
same evaluator definition
same application revision except intended change
```

### Step 6 · Experiment를 실행한다

```text
snapshot T
     ↓
baseline v20
candidate v21
     ↓
same evaluator
```

### Step 7 · 결과를 읽는다

세 층을 왕복한다.

```text
aggregate
→ item transition
→ diagnostic trace
```

### Step 8 · Release policy로 판정한다

```text
critical cases must pass
paired correctness must not regress
evaluation gaps must be zero
p95 latency <= agreed limit
```

### Step 9 · Production에서 다시 관찰한다

Offline pass는 끝이 아니다.

```text
new production traffic
→ new failure distribution
→ next trace review
```

Loop가 다시 시작된다.

## 4. Evaluator는 가장 단순한 신뢰 가능한 도구부터 선택한다

### Deterministic evaluator

잘 맞는 질문:

```text
JSON schema valid?
field == expected?
required citation id가 존재?
tool argument가 허용 range 안인가?
refund eligibility가 expected boolean과 같은가?
```

장점:

- 빠르다.
- 재현 가능하다.
- failure semantics를 읽기 쉽다.
- regression test로 사용하기 좋다.

### LLM-as-a-Judge

잘 맞을 수 있는 질문:

```text
설명이 핵심 의미를 보존하는가?
주어진 context에 grounded되어 있는가?
style rubric을 충족하는가?
두 답변 중 어느 쪽이 rubric을 더 잘 만족하는가?
```

하지만:

```text
judge output
≠ truth
```

Judge도 model이다. Prompt, model version, rubric ambiguity, sampling behavior에 영향을 받는다.

### Human review

특히 유용한 경우:

```text
새 failure mode discovery
ambiguous criterion
high-stakes judgment
LLM judge calibration
judge disagreement investigation
```

Human label도 자동으로 절대적인 ground truth가 되는 것은 아니다. 주관적 task에서는 reviewer disagreement가 생길 수 있다.

따라서 human labels는 다음 역할로 보는 편이 정확하다.

```text
reference evidence
→ rubric과 automated evaluator를 검증하는 기준
```

## 5. LLM judge는 calibration artifact가 필요하다

`groundedness` judge를 만든다고 하자.

먼저 representative examples를 human이 판정한다.

```text
case A → pass
case B → fail
case C → borderline / disagreement
```

그 다음 judge를 같은 cases에 적용한다.

조사한다.

```text
어디에서 일치하는가?
어디에서 체계적으로 틀리는가?
false positive / false negative 중 어느 쪽이 더 위험한가?
특정 segment에서만 disagreement가 커지는가?
rubric 문장이 모호한가?
```

좋은 loop:

```text
human reference
→ judge/rubric
→ disagreement analysis
→ rubric 또는 judge 수정
→ re-evaluate
→ production/experiment에 사용
→ periodic human re-check
```

## 6. `score=0`과 evaluation failure는 다른 사건이다

다음 두 row를 비교한다.

```text
A
application output 정상 생성
evaluator 정상 실행
result = fail
score = 0

B
application output 정상 생성
evaluator timeout
result = unknown
evaluator_error
```

B를 score 0으로 바꾸면 evaluation infrastructure failure가 quality failure처럼 보인다.

반대로 B를 평균에서 조용히 제외하면 coverage가 좋아 보일 수 있다.

그래서 최소한 다음을 분리한다.

```text
quality among valid comparable evaluations
baseline evaluation coverage
candidate evaluation coverage
paired comparison coverage
application error count
evaluator error count
score missing count
```

## 7. Baseline과 candidate 상태는 독립적이다

실제 comparison에서는 다음 상태가 가능하다.

```text
case A
baseline = scored 1.0
candidate = evaluator_error

case B
baseline = application_error
candidate = scored 1.0
```

따라서 row 하나에 shared `status` 하나만 두면 충분하지 않다.

이 장의 code lab은 variant evidence를 독립적으로 모델링한다.

```python
EvidenceRow(
    case_id="judge-timeout",
    critical=False,
    baseline=VariantEvidence.scored(0.8),
    candidate=VariantEvidence.gap("evaluator_error"),
)
```

각 variant의 invariant:

```text
status == scored
→ score가 반드시 존재

status != scored
→ score를 붙이지 않음
```

잘못된 state를 객체 생성 시점에 거부한다.

## 8. 평균은 같은 paired population에서 계산한다

다음 데이터가 있다고 하자.

```text
case A
baseline = 1.0
candidate = missing

case B
baseline = missing
candidate = 1.0
```

각 side에서 존재하는 값만 따로 평균내면:

```text
baseline average = 1.0
candidate average = 1.0
```

처럼 보인다.

하지만 실제로 두 variant가 **같이 평가된 case는 0개**다.

이 비교는 품질 delta를 말할 근거가 없다.

그래서 `release_gate.py`는 평균을 다음 population에서만 계산한다.

```text
paired-scored population
= baseline.status == scored
AND candidate.status == scored
```

그리고 coverage는 별도로 남긴다.

```text
baseline_coverage
candidate_coverage
paired_coverage
```

Quality와 coverage를 섞지 않는다.

## 9. Regression은 before/after transition이다

다음을 구분한다.

```text
baseline PASS
candidate FAIL
→ regression

baseline FAIL
candidate FAIL
→ existing/continuing candidate failure

baseline FAIL
candidate PASS
→ fix / improvement
```

따라서 critical case가 candidate에서 fail했다는 사실만으로 항상 "critical regression"이라고 부르면 안 된다.

Code lab은:

```text
baseline 1.0 → candidate 0.0
= critical regression

baseline 0.0 → candidate 0.0
= critical candidate failure
```

로 구분한다.

이 용어 구분은 incident diagnosis에서 중요하다.

```text
새 변경이 문제를 만들었는가?
아니면 이미 존재하던 failure를 아직 못 고쳤는가?
```

는 다른 질문이다.

## 10. Release policy는 결과를 보기 전에 정의한다

Candidate 결과를 본 뒤 threshold를 고르면 결과에 맞춰 기준을 움직이기 쉽다.

예:

```text
Release Policy

- critical candidate cases: 100% pass
- paired correctness: baseline보다 낮아지지 않음
- required evaluation gaps: 0
- p95 latency: 1.6s 이하
```

`1.6s`가 universal best practice라는 뜻은 아니다.

핵심은:

```text
result 보기 전
→ decision contract 정의
```

라는 순서다.

## 11. Code lab: evidence-preserving release gate

실행:

```bash
cd decks/llmops-langfuse
uv run python textbook/08-evaluation-loop/release_gate.py
```

핵심 타입:

```python
VariantEvidence.scored(1.0)
VariantEvidence.gap("evaluator_error")
VariantEvidence.gap("application_error")
VariantEvidence.gap("score_missing")
```

Row:

```python
EvidenceRow(
    case_id="critical-refund",
    critical=True,
    baseline=VariantEvidence.scored(1.0),
    candidate=VariantEvidence.scored(0.0),
)
```

Release decision은 다음을 함께 반환한다.

```text
approved
reasons
baseline_average
candidate_average
baseline_coverage
candidate_coverage
paired_coverage
```

실행 전에 예측한다.

1. critical refund row는 regression인가?
2. candidate evaluator error 두 건은 score 0이 되는가?
3. evaluator error row는 paired average에 들어가는가?
4. candidate coverage는 baseline coverage보다 낮아지는가?
5. 평균이 좋아도 release가 막힐 수 있는가?

## 12. Contract tests가 고정하는 failure semantics

[`test_release_gate.py`](test_release_gate.py)는 다음을 검사한다.

```text
baseline scored / candidate evaluator error
baseline evaluator error / candidate scored
baseline scored / candidate score missing
baseline score missing / candidate scored
critical pass → fail
critical fail → fail
critical fail → pass
policy-satisfied pass case
invalid status/score combination
```

이 테스트가 중요한 이유는 release code가 바로 이 장의 conceptual model이기 때문이다.

```text
prose에서는 failure를 구분
code에서는 하나의 None으로 뭉갬
```

같은 불일치를 허용하지 않는다.

## 13. 평균이 올라도 release가 막힐 수 있다

예:

```text
paired correctness    0.88 → 0.91
p95 latency           1.2s → 1.5s
critical refund case  pass → fail
candidate evaluator errors = 2
paired coverage       0.98
```

평균만 보면 좋아 보인다.

하지만 policy가:

```text
critical case must pass
evaluation gaps = 0
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
coverage gap 원인 조사
```

## 14. 어떤 trace를 먼저 열 것인가?

모든 trace를 무작위로 읽지 않는다.

Information gain이 큰 순서를 사용할 수 있다.

1. critical pass → fail regression
2. 새 application error
3. evaluator error / missing score
4. 큰 score delta가 난 paired item
5. segment regression representative example

Critical regression trace에서 확인한다.

```text
input은 같은가?
dataset expected output은 같은가?
dataset version은 같은가?
prompt/model/retrieval condition은 의도대로 고정됐는가?
실제 prompt version linkage는 맞는가?
generation output은 어떻게 달라졌는가?
evaluator definition은 같은가?
```

## 15. Aggregate, segment, example을 왕복한다

좋은 evaluation review는 세 level을 오간다.

```text
aggregate
→ 전체 방향

segment
→ 특정 category/failure mode에서만 문제가 있는가?

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

Dataset metadata와 failure taxonomy가 query dimension이 되는 이유다.

## 16. Evidence chain을 끊지 않는다

하나의 important case를 역추적할 수 있어야 한다.

```text
production trace
      ↓ source provenance
dataset item
      ↓ fixed dataset version
experiment run
      ↓ condition identity
prompt/model/app revision
      ↓
item trace
      ↓
variant evaluation state + score
      ↓
release policy
      ↓
release decision
      ↓
new production trace
```

각 화살표가 반드시 완전히 자동화되어야 하는 것은 아니다.

하지만 사람이:

> 이 release decision의 숫자는 어디서 왔는가?

라고 물었을 때 chain을 거슬러 올라갈 수 있어야 한다.

## 17. 이 deck의 최종 mental model

기능 이름보다 evidence role로 기억한다.

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

## 18. Final assessment

### Scenario

Production support assistant에서 다음 문제가 발견됐다.

```text
특정 refund boundary 질문에서 answer가 틀림
retrieval은 올바른 document를 가져옴
production prompt = version 20
```

Candidate는 prompt version 21이다.

### 과제

다음을 설계하고 설명한다.

1. **Trace diagnosis**
   - 어느 observation을 먼저 볼 것인가?
   - observed fact와 hypothesis를 어떻게 구분할 것인가?

2. **Evaluator**
   - deterministic / LLM judge / human 중 무엇을 선택할 것인가?
   - trace-level인가 observation-level인가?
   - evaluator failure는 어떻게 표현할 것인가?

3. **Dataset case**
   - 최소 input은 무엇인가?
   - expected output은 어떤 domain property인가?
   - raw production data 중 무엇을 제거할 것인가?
   - source provenance를 어떻게 유지할 것인가?

4. **Dataset version**
   - baseline/candidate가 같은 snapshot을 사용한다는 것을 어떻게 보장할 것인가?

5. **Candidate condition**
   - prompt 20 → 21 외에 무엇을 고정할 것인가?

6. **Prompt evidence**
   - generation이 실제 version 21을 사용했다는 것을 어떻게 확인할 것인가?

7. **Comparison**
   - aggregate, item transition, trace를 어떤 순서로 볼 것인가?
   - paired population은 무엇인가?

8. **Failure semantics**
   - baseline scored / candidate evaluator error case는 평균과 coverage에 어떻게 반영할 것인가?
   - baseline fail / candidate fail을 regression이라고 부를 것인가?

9. **Release policy**
   - goal metric, guardrail, operational metric을 정의한다.
   - 결과를 보기 전에 pass/fail contract를 쓴다.

10. **Production closure**
    - offline pass 뒤 어떤 production evidence를 다시 관찰할 것인가?

### Self-review rubric

좋은 답은 다음을 만족한다.

```text
Evidence fidelity
- 관찰과 추정을 구분
- score 0과 evaluation failure를 구분
- baseline/candidate state를 독립적으로 표현

Experimental discipline
- same dataset version
- same evaluator
- material conditions controlled
- paired population 명시

Ownership clarity
- domain truth owner 명확
- provider/application/evaluator 책임 구분
- prompt/dataset identity 추적 가능

Decision quality
- release policy 사전 정의
- critical regression 별도 확인
- coverage gap 별도 확인
- production re-observation 포함
```

## References

- [Langfuse Evaluation Overview](https://langfuse.com/docs/evaluation/overview)
- [Evaluate with Datasets](https://langfuse.com/docs/evaluation/get-started/offline)
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)
- [Langfuse Academy](https://langfuse.com/academy)
- [Hamel Husain · Your AI Product Needs Evals](https://hamel.dev/blog/posts/evals/)
- [Hamel Husain · Using LLM-as-a-Judge For Evaluation](https://hamel.dev/blog/posts/llm-judge/)
