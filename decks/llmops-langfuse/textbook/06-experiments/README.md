# 6장 · Experiment로 변경 전후 비교하기

Dataset이 같은 문제를 반복해서 낼 수 있게 해 준다면, experiment는 **application variant가 그 문제를 어떻게 푸는지**를 비교한다.

```text
dataset
   ↓
task(application)
   ↓
output
   ↓
evaluator
   ↓
scores
```

## 학습 목표

- dataset, task, evaluator, experiment run의 역할을 구분한다.
- local data experiment와 hosted dataset experiment의 차이를 설명한다.
- baseline과 candidate를 같은 조건에서 비교해야 하는 이유를 설명한다.
- aggregate score만 보고 regression 판단을 끝내면 안 되는 이유를 설명한다.

## 1. 가장 작은 experiment

현재 Python SDK v4의 experiment runner는 local data에도 사용할 수 있다.

```python
from langfuse import get_client

langfuse = get_client()

local_data = [
    {"input": "2 + 2", "expected_output": "4"},
    {"input": "3 + 5", "expected_output": "8"},
]


def task(*, item, **kwargs):
    # 실제 tutorial에서는 application 함수를 호출한다.
    return item["expected_output"]


result = langfuse.run_experiment(
    name="calculator-baseline",
    data=local_data,
    task=task,
)

print(result.format())
```

Runner는 각 item 실행을 trace로 만들기 때문에 실패 case를 aggregate table에서 끝내지 않고 실제 execution으로 내려가 조사할 수 있다.

## 2. Evaluator 추가

```python
from langfuse import Evaluation


def exact_match(*, output, expected_output, **kwargs):
    return Evaluation(
        name="exact-match",
        value=1.0 if output == expected_output else 0.0,
    )
```

그리고:

```python
result = langfuse.run_experiment(
    name="calculator-with-eval",
    data=local_data,
    task=task,
    evaluators=[exact_match],
)
```

여기서 evaluator code는 **experiment process 안에서 실행되는 correctness logic**이다.
Langfuse는 결과를 score로 연결하고 run을 비교하기 쉽게 만든다.

## 3. Hosted dataset

Dataset을 Langfuse에 저장했다면:

```python
dataset = langfuse.get_dataset("support/refund-policy")

result = dataset.run_experiment(
    name="prompt-v2",
    task=my_support_application,
    evaluators=[policy_evaluator],
)
```

Hosted dataset은 팀이 같은 test cases와 historical versions를 공유하고 experiment들을 같은 dataset 기준으로 비교하기 좋다.

## 4. 한 번에 하나의 중요한 조건을 바꾼다

비교가 의미 있으려면 무엇이 달라졌는지 알아야 한다.

좋은 비교:

```text
baseline
prompt v1 + model A + code X

candidate
prompt v2 + model A + code X
```

해석이 어려운 비교:

```text
baseline
prompt v1 + model A + retriever X

candidate
prompt v2 + model B + retriever Y + new parser
```

후자의 결과가 좋아져도 무엇 때문인지 판단하기 어렵다.

## 5. 평균값만 보지 않는다

예를 들어 두 experiment가 모두 90% accuracy라고 하자.

```text
Baseline
중요한 refund case: pass
minor case: fail

Candidate
중요한 refund case: fail
minor case: pass
```

평균만 보면 동일하지만 release decision은 동일하지 않을 수 있다.

따라서:

```text
aggregate score 확인
→ regression case 찾기
→ item trace 열기
→ 원인 조사
```

순서가 중요하다.

## 6. 비교 조건을 기록한다

Experiment metadata에 application revision, prompt version, model/config 같은 비교 조건을 남기면 재현성과 해석이 좋아진다.

```python
result = langfuse.run_experiment(
    name="refund-prompt-v2",
    data=test_data,
    task=my_task,
    evaluators=[policy_evaluator],
    metadata={
        "app_revision": "abc123",
        "prompt_variant": "v2",
    },
)
```

## 7. 실패를 score 0으로 숨기지 않는다

Task execution failure, evaluator failure, 정상 output의 낮은 score는 서로 다른 상태다.

```text
execution error
≠ evaluator error
≠ valid output with low quality
```

Experiment를 운영할 때 이 셋을 하나의 숫자로 뭉개면 diagnosis가 어려워진다.

## 연습

두 candidate의 평균 score가 baseline보다 높다.
그런데 production에서 매우 중요한 3개 case 중 1개가 새로 실패했다.

1. 평균 향상만으로 deploy해도 되는가?
2. 어떤 trace를 열어 봐야 하는가?
3. evaluator 자체가 잘못됐을 가능성을 어떻게 구분할까?
4. release policy는 experiment 결과를 보기 전에 정의하는 것이 왜 좋은가?

## 다음 장

지금까지 prompt는 application code 안에 있다고 가정했다.
다음 장에서는 prompt를 versioned artifact로 관리하고 실행 trace와 연결한다.

## References

- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Experiments Data Model](https://langfuse.com/docs/evaluation/experiments/data-model)
- [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)
- [Langfuse Workshop](https://github.com/langfuse/langfuse-workshop)
