# 6장 · Experiment: 같은 Cases에서 변경 전후를 비교하기

Dataset은 같은 문제를 다시 낼 수 있게 한다. 하지만 같은 문제를 가지고 있다는 것만으로는 변경이 좋아졌는지 알 수 없다.

Experiment가 답하려는 질문은 더 구체적이다.

> **같은 cases와 같은 evaluation contract 아래에서, 의도한 condition을 바꾸었을 때 어떤 behavior가 달라졌는가?**

이 장에서는 먼저 Langfuse 없이 comparison mechanics를 확인한 뒤, 같은 원리를 Langfuse Experiment Runner와
**고정된 hosted dataset snapshot**에 적용한다.

## 학습 목표

이 장을 마치면 다음을 할 수 있어야 한다.

- dataset, task, evaluator, experiment run의 역할을 구분한다.
- baseline과 candidate가 같은 case population을 사용해야 하는 이유를 설명한다.
- aggregate metric과 item-level regression을 함께 읽는다.
- 같은 aggregate score가 서로 다른 regression pattern을 숨길 수 있음을 설명한다.
- local data와 hosted dataset experiment의 차이를 설명한다.
- Langfuse dataset의 timestamp version을 baseline/candidate에 고정한다.
- application/task error, evaluator error, valid low score를 서로 다른 evidence로 취급한다.
- experiment evidence가 강하게 말할 수 있는 것과 causal claim의 한계를 구분한다.

## 1. Experiment의 네 책임

가장 작은 data flow는 다음과 같다.

```text
Dataset
   ↓ input + expected output
Task
   ↓ application output
Evaluator
   ↓ score / evaluation result
Experiment
   ↓ repeated comparison evidence
```

각 책임을 섞지 않는다.

```text
dataset
= 다시 시험할 cases와 reference

task
= 실제로 시험할 application behavior

evaluator
= output을 판정하는 rule

experiment
= cases × task × evaluator를 실행하고 비교할 evidence
```

특히 task가 `expected_output`을 그대로 읽어서 정답을 반환하면 experiment가 아니다.

```python
def bad_task(*, item, **kwargs):
    return item["expected_output"]
```

이 코드는 높은 score를 만들 수 있지만 production application이 문제를 해결했다는 evidence는 만들지 못한다.

## 2. 먼저 prediction한다

[`experiment_compare.py`](experiment_compare.py)의 local dataset에는 두 category가 있다.

```text
electronics: 14일까지 환불 가능
perishable:   7일까지 환불 가능
```

Teaching application은 일부러 category를 무시하고 하나의 global refund window만 사용한다.

Baseline:

```text
refund_window_days = 14
```

Candidate:

```text
refund_window_days = 7
```

실행하기 전에 예측한다.

1. baseline accuracy는 얼마일까?
2. candidate accuracy는 얼마일까?
3. candidate가 고치는 case는 무엇인가?
4. candidate가 새로 깨뜨리는 case는 무엇인가?
5. aggregate accuracy가 같다면 두 variant가 동등하다고 말할 수 있을까?

그 다음 실행한다.

```bash
cd decks/llmops-langfuse
uv run python textbook/06-experiments/experiment_compare.py
```

핵심 결과는 다음 관계다.

```text
baseline accuracy  = 0.75
candidate accuracy = 0.75

candidate fixes
perishable-day-10

candidate regression
electronics-day-14   critical
```

## 3. 평균이 같아도 behavior는 같지 않다

두 variant의 평균이 모두 75%여도 item transition은 다르다.

```text
case                  baseline   candidate
------------------------------------------------
electronics-day-14     PASS       FAIL   critical
perishable-day-10      FAIL       PASS
```

Aggregate는 전체 방향을 보는 데 유용하지만 어떤 case가 바뀌었는지는 알려 주지 않는다.

그래서 comparison은 최소한 다음 순서로 읽는다.

```text
aggregate
→ changed items
→ regressions
→ critical regressions
→ 해당 item의 execution evidence
```

[`test_experiment_compare.py`](test_experiment_compare.py)는 이 invariant를 deterministic contract로 고정한다.

## 4. 한 번에 무엇을 바꿨는지 말할 수 있어야 한다

해석하기 쉬운 comparison:

```text
baseline
prompt v20
model M
retriever R
code C

candidate
prompt v21
model M
retriever R
code C
```

해석하기 어려운 comparison:

```text
baseline
prompt v20
model M1
retriever R1

candidate
prompt v21
model M2
retriever R2
parser rewrite
```

두 번째 실험도 release package 전체의 결과를 비교하는 데는 의미가 있을 수 있다. 하지만 어느 change가 차이를 만들었는지
분리하기 어렵다.

따라서 먼저 질문한다.

```text
이 run은 product package comparison인가?
아니면 특정 change의 effect를 이해하려는 controlled experiment인가?
```

둘을 같은 causal claim으로 취급하지 않는다.

## 5. Langfuse local-data Experiment Runner

Credential을 설정하고 다음을 켜면 local data를 Langfuse runner에서도 실행할 수 있다.

```bash
export LANGFUSE_PUBLIC_KEY="..."
export LANGFUSE_SECRET_KEY="..."
export RUN_LANGFUSE_EXPERIMENT=1

uv run python textbook/06-experiments/experiment_compare.py
```

`LANGFUSE_DATASET_VERSION`을 설정하지 않으면 script는 `LOCAL_DATA`를 사용해 두 run을 만든다.

```text
refund-window-baseline
refund-window-candidate
```

Task는 production-like input만 읽는다.

```python
def task(*, item, **kwargs):
    return support_application(
        item=item,
        refund_window_days=refund_window_days,
    )
```

Evaluator는 output과 expected output을 비교한다.

```python
return Evaluation(
    name="correctness",
    value=1.0 if output == expected_output else 0.0,
)
```

여기서 중요한 것은 API 호출 성공이 아니라 역할 분리다.

```text
task
≠ evaluator

evaluator
≠ expected output owner

experiment runner
≠ correctness rule owner
```

## 6. Hosted dataset에서는 version도 condition이다

Production failure를 Unit 5에서 hosted dataset item으로 올렸다고 하자.

Dataset은 시간이 지나면서 변할 수 있다.

```text
09:00  cases A, B, C
10:00  case D 추가
11:00  case B 수정
```

Baseline은 09:30 snapshot을 쓰고 candidate는 11:30 snapshot을 쓰면 결과 차이가 application change 때문인지 dataset
change 때문인지 섞인다.

그래서 비교 contract에 dataset identity뿐 아니라 **dataset version**이 필요하다.

현재 Langfuse Python SDK v4에서는 다음처럼 timestamp를 전달할 수 있다.

```python
dataset = langfuse.get_dataset(
    "support/refund-policy",
    version=dataset_version,
)
```

`version`은 그 timestamp 기준의 dataset item state를 읽기 위한 condition이다.

이 deck에서는 schema migration 같은 별도 변화까지 이 한 값으로 설명한다고 가정하지 않는다. 여기서 version은
**experiment case population을 고정하는 snapshot boundary**로 사용한다.

## 7. Hands-on: snapshot timestamp를 하나 고정한다

Unit 5에서 필요한 dataset items를 만든 뒤, 그 상태를 이번 comparison에서 고정한다고 결정한다.

예를 들어 현재 UTC 시간을 snapshot boundary로 기록한다.

```bash
export LANGFUSE_DATASET="support/refund-policy"
export LANGFUSE_DATASET_VERSION="$(python - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).isoformat())
PY
)"
```

중요한 것은 timestamp 값 자체가 아니다.

> **baseline과 candidate가 정확히 같은 timestamp를 사용한다는 것**이 중요하다.

실행 전에 적는다.

```text
dataset name = ?
dataset version = ?
evaluator = ?

baseline condition = refund_window_days 14
candidate condition = refund_window_days 7
```

그 다음 실행한다.

```bash
export RUN_LANGFUSE_EXPERIMENT=1
uv run python textbook/06-experiments/experiment_compare.py
```

Script는 다음 형태를 stdout에 남긴다.

```text
hosted_dataset=support/refund-policy dataset_version=2026-...
```

그리고 내부에서는 **한 번 fetch한 동일 DatasetClient**를 baseline/candidate가 재사용한다.

```text
get_dataset(name, version=T)
        ↓
    snapshot T
     ↙      ↘
baseline   candidate
```

이 구조가 중요한 이유는 두 run 사이에 label이나 current dataset이 바뀌더라도 이번 comparison의 case population은 이미
고정되어 있기 때문이다.

## 8. UI에서는 세 level을 왕복한다

Hosted experiment를 실행한 뒤 다음 순서로 본다.

### Level 1 · Aggregate

```text
baseline correctness
candidate correctness
```

방향을 빠르게 확인한다.

### Level 2 · Item transition

```text
pass → fail
fail → pass
unchanged fail
unchanged pass
```

특히 critical metadata가 붙은 `pass → fail`을 먼저 본다.

### Level 3 · Trace

Regression item을 열고 묻는다.

```text
input이 같은가?
expected output이 같은가?
실제 application output은 어떻게 달라졌는가?
어느 condition만 바뀌었는가?
evaluator가 같은 rule을 사용했는가?
```

이때 trace는 dashboard 장식이 아니라 comparison 결과를 설명하는 diagnostic evidence가 된다.

## 9. Failure state를 숫자 하나로 뭉개지 않는다

Experiment에는 최소한 다음 상태가 있다.

```text
application/task error
evaluator error
score missing
valid output + low score
valid output + high score
```

다음 두 사건은 다르다.

```text
output을 평가했고 틀림
→ valid score 0

evaluator가 timeout
→ evaluator error
```

Evaluator error를 0으로 바꾸면 quality failure처럼 보인다. 반대로 실패 row를 평균에서 조용히 제외하면 coverage가 좋아
보일 수 있다.

Unit 8에서는 baseline/candidate의 이런 상태를 독립적으로 보존한 release gate를 만든다.

## 10. Experiment가 증명하지 않는 것

Controlled experiment는 다음을 강하게 말할 수 있다.

```text
이 고정된 case population과 evaluator에서
candidate가 case X를 고쳤다.

같은 조건에서
candidate가 case Y를 새로 깨뜨렸다.
```

하지만 다음까지 자동으로 증명하지 않는다.

```text
production 전체 distribution에서도 반드시 개선됨
관찰된 모든 차이의 내부 원인을 완전히 증명함
future traffic에서도 같은 metric 유지
```

Offline experiment는 production uncertainty의 일부를 줄이는 도구다. Production observation을 대체하지 않는다.

## 11. Checkpoint

코드를 보지 않고 답한다.

1. Task가 `expected_output`을 읽으면 왜 leakage인가?
2. Baseline/candidate 평균이 같아도 release decision이 달라질 수 있는 이유는 무엇인가?
3. Dataset name이 같아도 version을 고정해야 할 수 있는 이유는 무엇인가?
4. Hosted dataset snapshot을 한 번 fetch해서 두 variant가 재사용하면 어떤 confounder를 제거하는가?
5. `score=0`과 evaluator error는 왜 다른 evidence인가?
6. Product package comparison과 single-variable experiment의 목적은 어떻게 다른가?

## 12. Assessment: 작은 controlled comparison을 설계한다

다음 change 중 하나를 고른다.

```text
prompt version
model
retrieval top-k
parser rule
```

다음을 작성한다.

```text
baseline condition
candidate condition
고정할 dataset name + version
고정할 evaluator contract
고정할 model/retrieval/app condition
critical cases
release를 막는 regression
먼저 열 trace와 그 이유
```

좋은 답은 단순히 "두 번 실행해서 평균을 비교한다"로 끝나지 않는다.

## 다음 장

지금까지 application condition은 metadata로 표현할 수 있었다. 다음 장에서는 prompt 자체를 versioned artifact로 다루고,
**실제 generation이 어느 immutable prompt version을 사용했는지** 연결한다.

## References

- [Langfuse Academy · Experiments](https://langfuse.com/academy/experiments)
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Experiments Data Model](https://langfuse.com/docs/evaluation/experiments/data-model)
- [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)
- [Evaluate with Datasets](https://langfuse.com/docs/evaluation/get-started/offline)
- [Langfuse Python SDK v4.16.0 · DatasetClient](https://github.com/langfuse/langfuse-python/blob/v4.16.0/langfuse/_client/datasets.py)
