# 8장 · Production Trace에서 Regression Gate까지

마지막 장에서는 개별 기능을 하나의 loop로 연결한다.

```text
observe
→ find failure
→ define expectation
→ dataset
→ change one thing
→ experiment
→ evaluate
→ inspect regression
→ release decision
→ observe again
```

Langfuse를 잘 쓴다는 것은 기능을 많이 켜는 것이 아니라 이 loop에서 **evidence의 연결이 끊기지 않는 것**이다.

## 학습 목표

- online observation과 offline evaluation의 역할을 구분한다.
- production failure를 reusable regression case로 바꾸는 전체 data flow를 설명한다.
- deterministic evaluator와 LLM-as-a-Judge의 역할과 신뢰 경계를 구분한다.
- aggregate score, item trace, evaluator evidence를 함께 사용해 release decision을 설명한다.

## 1. Online과 Offline

Online evaluation:

```text
real production trace
→ score / feedback
→ trend와 failure pattern 발견
```

Offline evaluation:

```text
fixed dataset
→ candidate application 실행
→ scores
→ baseline과 비교
```

둘 중 하나로 다른 하나를 대체하지 않는다.

Production은 예상하지 못한 입력을 보여 주고, offline dataset은 같은 사례를 반복해서 비교하게 해 준다.

## 2. End-to-end example

### Step 1 · Production에서 실패 발견

```text
question: "10일 전에 받은 상품 환불 가능?"
answer: "환불 기간이 지났습니다."
```

Trace를 열어 보니 retrieval은 `14일 이내 가능`을 가져왔지만 generation이 잘못 해석했다.

### Step 2 · Dataset으로 보존

```json
{
  "input": {"days_since_delivery": 10},
  "expected_output": {"eligible": true}
}
```

### Step 3 · Candidate 변경

Prompt instruction을 더 명확히 한다.

### Step 4 · Experiment

같은 dataset version에 baseline과 candidate를 실행한다.

### Step 5 · Evaluate

Deterministic evaluator가 `eligible` property를 확인한다.

### Step 6 · Compare

평균 score뿐 아니라 과거에 통과하던 case가 새로 실패하지 않았는지 본다.

### Step 7 · Deploy 후 다시 관찰

Offline dataset이 production distribution 전체를 대표한다는 보장은 없다.
배포 후 실제 trace와 online score를 다시 본다.

## 3. Deterministic evaluator를 먼저 신뢰할 수 있으면 사용한다

가능한 경우:

```text
JSON schema valid?
expected field equals?
required citation exists?
tool call argument range valid?
```

이런 검사는 code evaluator가 명확하고 재현 가능하다.

LLM-as-a-Judge가 필요한 질문도 있다.

```text
답변이 친절한가?
요약이 핵심을 보존하는가?
설명이 충분히 grounded되어 있는가?
```

하지만 judge도 model이다.
Human label과 calibration 없이 “LLM judge score가 곧 진실”이라고 가정하면 안 된다.

## 4. Score가 없는 것과 실패를 구분한다

Release table을 볼 때 다음 상태를 분리한다.

```text
application error
output produced + score 0
output produced + evaluator error
output produced + score missing
```

모두 “fail” 한 칸으로 합치면 원인을 잃는다.

## 5. Release policy는 결과를 보기 전에 정한다

예:

```text
- critical policy cases: 모두 pass해야 함
- overall correctness: baseline보다 낮아지면 안 됨
- p95 latency: 허용 범위 안
- evaluator error: 0건
```

결과를 본 다음 기준을 바꾸면 candidate에 유리하게 해석하기 쉽다.

## 6. Final diagnosis exercise

새 prompt candidate의 experiment 결과가 다음과 같다.

```text
average correctness: 0.88 → 0.91
latency: 1.2s → 1.5s
critical refund case: pass → fail
evaluator errors: 0 → 2
```

질문:

1. candidate가 더 좋다고 말할 수 있는가?
2. 어떤 item trace를 먼저 조사할까?
3. evaluator error 두 건을 score 0으로 처리하면 왜 문제가 생길까?
4. prompt 변경의 효과와 latency 변화가 같은 원인인지 어떻게 확인할까?
5. release policy가 `critical case must pass`라면 결론은 무엇인가?

## 7. 이 deck의 최종 mental model

Langfuse 기능을 각각 외우지 않는다.

```text
Trace
= 실행 evidence

Score
= 평가 evidence

Dataset
= 반복할 사례

Experiment
= 같은 사례에서 change를 비교하는 실행

Prompt version
= change identity의 한 종류
```

그리고 전체 loop는:

```text
관찰
→ 판단
→ 사례화
→ 비교
→ 결정
→ 다시 관찰
```

이다.

## 이후 확장할 수 있는 주제

Core를 이해한 뒤 다음을 별도로 깊게 다룰 수 있다.

- LLM-as-a-Judge 설계와 human calibration
- Annotation Queues
- experiment CI/CD gate
- direct OpenTelemetry ingestion
- LangChain/LlamaIndex/Agents SDK integration
- self-hosted Langfuse 운영
- custom dashboards / metrics API

## References

- [Langfuse Academy](https://langfuse.com/academy)
- [Evaluation Overview](https://langfuse.com/docs/evaluation/overview)
- [Evaluation Core Concepts](https://langfuse.com/docs/evaluation/core-concepts)
- [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)
- [Langfuse Workshop](https://github.com/langfuse/langfuse-workshop)
