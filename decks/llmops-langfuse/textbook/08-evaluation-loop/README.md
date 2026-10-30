# 8장 · Evaluation Loop: Production Evidence에서 Release Decision까지

마지막 장에서는 trace, score, dataset version, experiment, prompt version을 연결해 **실제 release 결정을 내리는 근거**를 만든다.

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

목표는 기능을 많이 사용하는 것이 아니라 **“왜 이 변경을 배포했는가?”에 evidence chain으로 답하는 것**이다.

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

| 구분 | Online observation | Offline evaluation |
| --- | --- | --- |
| 무엇을 보는가 | 실제 사용자 입력, orchestration path, provider 동작, latency/cost, 예상 밖의 실패 | 고정된 dataset snapshot과 evaluator로 동일한 case를 반복 실행한 결과 |
| 강점 | 미처 예상하지 못한 failure 발견 | Known failure 재현과 candidate 변경 효과 비교 |
| 한계 | Input, prompt, model, retrieval, 외부 조건을 통제하기 어려움 | Dataset이 production의 모든 입력 분포를 대표하지는 않음 |

둘은 대체재가 아니다. **Production에서 실패를 발견하고 → offline에서 통제해 비교하고 → release 후 다시 production을 관찰한다.**

## 2. Metric 이름보다 failure를 먼저 본다

처음부터 `accuracy`, `quality`, `helpfulness`, `relevance`, `groundedness` 같은 metric 이름을 고르면 **무엇이 실패인지** 모호해지기 쉽다.

Trace를 검토해 중요한 failure를 찾고, mechanism을 설명한 다음, **판정 가능한 질문**과 가장 단순한 evaluator를 정한다.

| 단계 | 환불 정책 예시 |
| --- | --- |
| 관찰된 실패 | 올바른 정책 문서를 retrieval했지만 답변에서 eligibility를 반대로 설명함 |
| 판정 질문 | 최종 output의 `eligible` 값이 expected policy outcome과 같은가? |
| Evaluator | Structured deterministic equality check |

이렇게 정의해야 `quality=0.7`이라는 숫자보다 무엇을 고쳐야 하는지 분명해진다.

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

| Case | Application | Evaluator | 결과 |
| --- | --- | --- | --- |
| A | 정상 실행 | 정상 실행, 판정은 실패 | `score=0` (평가 완료) |
| B | 정상 실행 | Timeout | `evaluator_error` (평가 미완료) |

B를 `0`점으로 바꾸면 infrastructure failure가 품질 실패로 보이고, 평균에서 조용히 제외하면 coverage 문제가 가려진다.

따라서 **유효한 paired case의 quality**, baseline/candidate 각각의 evaluation coverage, paired coverage, application error·evaluator error·missing score 건수를 분리해 보고한다.

## 7. Baseline과 candidate 상태는 독립적이다

같은 case에서도 baseline과 candidate의 평가 상태가 다를 수 있다.

| Case | Baseline | Candidate |
| --- | --- | --- |
| A | `scored 1.0` | `evaluator_error` |
| B | `application_error` | `scored 1.0` |

따라서 row 하나에 shared `status`만 두면 한쪽의 실패를 표현할 수 없다.

이 장의 code lab은 variant evidence를 독립적으로 모델링한다.

```python
EvidenceRow(
    case_id="judge-timeout",
    critical=False,
    baseline=VariantEvidence.scored(0.8),
    candidate=VariantEvidence.gap("evaluator_error"),
)
```

각 variant는 **`scored`일 때만 score가 있어야 하며**, 그 correctness 값은 유한한 `[0, 1]` 범위여야 한다. 그 외 status에는 score를 붙이지 않는다.

Code는 생성 시점에 `NaN`, `Inf`, 범위 밖 점수를 거부한다. Release decision도 음수·비유한 p95 latency를 거부한다. 잘못된 값을 `0`점으로 치환하거나 평균에서 조용히 제외하지 않는다.

## 8. 평균은 같은 paired population에서 계산한다

| Case | Baseline | Candidate |
| --- | --- | --- |
| A | `1.0` | missing |
| B | missing | `1.0` |

각각의 평가된 값만 평균내면 둘 다 `1.0`처럼 보인다. 하지만 **양쪽에서 모두 평가된 case는 0개**이므로 품질 차이를 계산할 근거가 없다.

`release_gate.py`는 **`baseline.status == scored`이면서 `candidate.status == scored`인 paired population**에서만 평균을 계산한다. `baseline_coverage`, `candidate_coverage`, `paired_coverage`는 별도 필드로 보고한다. **Quality와 coverage는 다른 정보다.**

## 9. Regression은 before/after transition이다

| Baseline → Candidate | 해석 | Code lab의 critical case |
| --- | --- | --- |
| PASS → FAIL | 새 regression | `1.0 → 0.0`: `critical regression` |
| FAIL → FAIL | 기존 실패가 남아 있음 | `0.0 → 0.0`: `critical candidate failure` |
| FAIL → PASS | 수정으로 개선됨 | `0.0 → 1.0`: improvement |

Critical case가 candidate에서 실패했다는 사실만으로 regression이라고 부르면 안 된다. **새 변경이 실패를 만들었는지, 기존 실패를 아직 해결하지 못했는지** 구분해야 진단 방향이 달라진다.

## 10. Release policy는 결과를 보기 전에 정의한다

결과를 본 뒤 threshold를 정하면 관측값에 맞춰 기준을 바꾸기 쉽다. 예를 들어 실험 **전에** 다음 정책을 합의한다.

- Critical candidate case: 100% pass
- Paired correctness: baseline보다 낮아지지 않을 것
- 필수 evaluation gap: 0건
- p95 latency: 1.6초 이하

`1.6s`는 보편적 권장값이 아니라 **이 예제에서 미리 정한 기준**이다.

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
non-finite/out-of-range correctness와 non-finite/negative latency
```

이 테스트가 중요한 이유는 release code가 바로 이 장의 conceptual model이기 때문이다.

```text
prose에서는 failure를 구분
code에서는 하나의 None으로 뭉갬
```

같은 불일치를 허용하지 않는다.

## 13. 평균이 올라도 release가 막힐 수 있다

| 지표 | 관찰 결과 |
| --- | --- |
| Paired correctness | `0.88 → 0.91` |
| p95 latency | `1.2s → 1.5s` |
| Critical refund case | PASS → FAIL |
| Candidate evaluator error | 2건 |
| Paired coverage | `0.98` |

평균은 개선됐지만 **critical case 100% pass**, **evaluation gap 0건**이라는 정책에는 실패한다. 결론은 **DO NOT RELEASE**다.

이때는 평균을 다시 계산하기보다 critical regression trace, evaluator error, coverage gap의 원인을 조사한다.

## 14. 어떤 trace를 먼저 열 것인가?

모든 trace를 무작위로 읽지 않는다.

Information gain이 큰 순서를 사용할 수 있다.

1. critical pass → fail regression
2. 새 application error
3. evaluator error / missing score
4. 큰 score delta가 난 paired item
5. segment regression representative example

Critical regression trace를 열어 **input·expected output·dataset version**이 같은지, **prompt/model/retrieval 조건**이 의도대로 통제됐는지 확인한다. 실제 prompt version linkage와 generation output의 차이, evaluator definition의 일치 여부도 추적한다.

## 15. Aggregate, segment, example을 왕복한다

Evaluation review는 **aggregate → segment → example**을 왕복한다. Aggregate는 전체 방향, segment는 category·failure mode별 편차, example은 실제 item trace의 실패 mechanism을 보여 준다.

| Segment | Score |
| --- | ---: |
| Overall | 0.91 |
| Refund | 0.98 |
| Shipping | 0.93 |
| Subscription | 0.61 |

Overall만 보면 subscription의 낮은 성능이 가려진다. 그래서 dataset metadata와 failure taxonomy가 분석 축이 된다.

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

## 17. 전체 loop에서 무엇이 남아야 하는가?

각 도구의 evidence 역할은 [교본 안내의 핵심 invariants](../README.md#핵심-invariants)에 정리되어 있다. 마지막으로 확인할 것은 **연결 관계**다. Execution은 trace/observation과 generation에, 평가는 score와 variant별 상태에, 재현 조건은 dataset version과 prompt/model/application identity에, 행동 기준은 release policy에 남아야 한다.

**Observe → Explain → Preserve → Change → Compare → Evaluate → Decide → Observe again.** 이 순환에서 근거가 끊긴 지점이 없는지 마지막 assessment로 점검한다.

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
