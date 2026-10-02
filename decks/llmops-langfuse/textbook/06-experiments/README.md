# 6장 · Experiment: 같은 Cases에서 변경 전후를 비교하기

Dataset은 같은 문제를 다시 낼 수 있게 한다. 그러나 dataset만으로는 변경이 좋아졌는지 알 수 없다.

Experiment는 다음 질문을 구조화한다.

> **같은 test cases와 같은 evaluation contract 아래에서 application condition 하나를 바꾸었을 때 무엇이 달라졌는가?**

Langfuse Academy가 강조하는 핵심도 cause/effect를 이해할 수 있도록 baseline을 고정하고 comparison condition을 통제하는
것이다.

## 학습 목표

- dataset, task, evaluator, experiment run의 역할을 구분한다.
- baseline과 candidate가 같은 dataset/evaluator를 사용해야 하는 이유를 설명한다.
- local data experiment와 hosted dataset experiment의 차이를 설명한다.
- aggregate metric과 item-level regression을 함께 읽는다.
- task error, evaluator error, valid low score를 구분한다.
- experiment가 보여 주는 evidence와 causal claim의 한계를 구분한다.

## 1. Experiment의 네 요소

가장 작은 모델은 다음과 같다.

```text
Dataset
   ↓
Task
   ↓
Output
   ↓
Evaluator
   ↓
Score
```

비교할 때는 여기에 condition이 추가된다.

```text
same dataset
same evaluator
same surrounding conditions

baseline application
        vs
candidate application
```

각 책임을 섞지 않는다.

```text
dataset expected_output
= 비교할 reference

task
= 시험할 application behavior

evaluator
= output과 reference를 판정하는 rule

experiment
= 같은 cases에서 condition을 반복 실행해 비교할 evidence
```

## 2. 가장 위험한 leakage: task가 정답을 읽는 것

다음 task는 test가 아니다.

```python
def bad_task(*, item, **kwargs):
    return item["expected_output"]
```

Application이 정답을 그대로 읽어 반환하기 때문이다.

```text
expected_output
→ evaluator가 참고해야 할 reference

task
→ expected_output을 모르는 production-like application
```

이 경계를 어기면 score가 높아도 application quality에 대한 evidence가 되지 않는다.

## 3. 먼저 Langfuse 없이 comparison mechanics를 본다

[`experiment_compare.py`](experiment_compare.py)는 API key 없이 실행할 수 있는 deterministic lab을 제공한다.

```bash
python textbook/06-experiments/experiment_compare.py
```

Dataset에는 두 product category가 있다.

```text
electronics policy: 14-day window
perishable policy: 7-day window
```

그런데 teaching application은 의도적으로 **global refund window 하나만** 사용한다.

Baseline:

```text
refund_window_days = 14
```

Candidate:

```text
refund_window_days = 7
```

이 candidate는 perishable case 하나를 고치지만 electronics의 critical boundary case를 깨뜨린다.

예상 출력의 핵심:

```text
baseline_accuracy=0.75
candidate_accuracy=0.75

regression
electronics-day-14
```

## 4. 평균이 같아도 system behavior는 같지 않다

Baseline과 candidate가 모두 75%라고 하자.

```text
baseline
electronics-day-14   PASS   critical
perishable-day-10    FAIL

candidate
electronics-day-14   FAIL   critical
perishable-day-10    PASS
```

Aggregate만 보면 동일하다.

하지만 regression 관점에서는 완전히 다르다.

```text
candidate가 고친 case
≠
candidate가 새로 깨뜨린 case
```

Release decision에는 다음 순서가 더 유용하다.

```text
aggregate trend 확인
→ changed items 찾기
→ critical regression 식별
→ 해당 item trace 조사
→ failure mechanism 설명
```

[`test_experiment_compare.py`](test_experiment_compare.py)는 **같은 aggregate가 critical regression을 숨길 수 있음**을
contract로 고정한다.

## 5. 이 lab은 causal claim의 한계도 보여 준다

Candidate에서 global window를 14 → 7로 바꿨다.

이 한 parameter change로 여러 dataset segment의 behavior가 바뀐다.

Experiment는 다음을 강하게 말할 수 있다.

```text
이 condition에서 이 case가 고쳐졌다.
이 condition에서 저 case가 회귀했다.
```

하지만 다음을 자동으로 증명하지는 않는다.

```text
production 전체에서도 반드시 개선된다.
관찰된 모든 변화의 내부 원인을 완전히 설명했다.
```

그래서 experiment는 controlled evidence이지 "원인에 대한 마법 같은 증명"이 아니다.

## 6. Langfuse Experiment Runner로 같은 구조를 실행한다

현재 Langfuse Python SDK v4의 Experiment Runner는 local data와 hosted dataset을 모두 지원한다. Runner는 item execution을
자동으로 trace하고 evaluator result를 연결하며, 개별 failure를 격리해 전체 run을 조사할 수 있게 한다.

`experiment_compare.py`에는 같은 deterministic task를 Langfuse runner로 실행하는 함수가 있다.

```python
return langfuse.run_experiment(
    name=name,
    data=LOCAL_DATA,
    task=task,
    evaluators=[correctness_evaluator],
    metadata={"refund_window_days": refund_window_days},
)
```

Evaluator:

```python
from langfuse import Evaluation

return Evaluation(
    name="correctness",
    value=1.0 if output == expected_output else 0.0,
)
```

이 evaluator는 experiment process 안에서 실행된다.

## 7. Live lab: baseline과 candidate를 별도 run으로 만든다

Langfuse credential을 설정한 뒤:

```bash
export RUN_LANGFUSE_EXPERIMENT=1

uv run python textbook/06-experiments/experiment_compare.py
```

두 experiment run을 비교한다.

```text
refund-window-baseline
refund_window_days=14

refund-window-candidate
refund_window_days=7
```

UI에서 다음 순서로 관찰한다.

1. aggregate correctness는 같은가?
2. candidate에서 score가 오른 item은 무엇인가?
3. candidate에서 새로 실패한 item은 무엇인가?
4. `electronics-day-14`가 critical이라는 metadata를 확인할 수 있는가?
5. 해당 experiment item의 trace로 내려가 실제 input/output을 확인할 수 있는가?

## 8. Hosted dataset으로 이동하면 무엇이 달라지는가?

Local data:

```python
langfuse.run_experiment(
    data=[...],
    ...
)
```

Hosted dataset:

```python
dataset = langfuse.get_dataset("support/refund-policy")

dataset.run_experiment(
    name="candidate",
    task=my_task,
    evaluators=[my_evaluator],
)
```

핵심 mechanism은 같다.

차이는 hosted dataset이 다음을 더 잘 지원한다는 점이다.

- 팀이 같은 cases를 공유한다.
- source trace linkage를 함께 관리할 수 있다.
- historical dataset version을 기준으로 run을 재현할 수 있다.
- 같은 dataset의 여러 experiment를 UI에서 비교하기 쉽다.

Hosted dataset을 쓴다고 evaluator/app contract가 자동으로 좋아지는 것은 아니다.

## 9. 비교 condition을 기록한다

Experiment 이름 하나만으로는 나중에 원인을 재현하기 어렵다.

가능하면 다음을 metadata나 명확한 run identity에 남긴다.

```text
application revision
prompt version
model/config
dataset version
retrieval configuration
feature flag
```

단, metadata를 많이 남기는 것이 목적은 아니다.

> 결과 차이를 해석하거나 재현하는 데 필요한 **material condition**을 남긴다.

## 10. 한 번에 하나의 중요한 variable을 바꾼다

좋은 비교:

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

해석하기 어려운 비교:

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

두 번째 comparison은 candidate package 전체가 좋았는지는 볼 수 있어도 **무엇이 효과를 만들었는지** 설명하기 어렵다.

Product release comparison과 causal experiment가 같은 목적이 아닐 수 있다는 점도 구분한다.

## 11. Failure state를 숫자 하나로 뭉개지 않는다

Experiment에는 최소한 다음 상태가 있다.

```text
task/application error
evaluator error
valid output + score 0
valid output + score 1
score missing
```

Runner가 item failure를 격리해 계속 실행할 수 있다고 해서 failure를 정상 score로 변환해야 한다는 뜻은 아니다.

진단에서는 **어디에서 실패했는가**가 중요하다.

## 12. Evaluator를 여러 개 둘 때

예를 들어 candidate를 다음 dimension으로 볼 수 있다.

```text
correctness      goal metric
safety           guardrail
latency          operational metric
cost             operational metric
```

Metric이 많을수록 좋다는 뜻은 아니다. Langfuse Academy와 일반적인 eval practice 모두 실제 failure mode와 product goal에서
metric을 선택할 것을 강조한다.

측정할 이유를 설명할 수 없는 metric은 noise가 된다.

## 13. 연습: 결과를 해석한다

다음 결과가 있다.

```text
baseline accuracy  0.86
candidate accuracy 0.90

critical case A    pass → fail
minor case B       fail → pass
minor case C       fail → pass

latency p95        1.1s → 1.4s
```

답한다.

1. candidate가 "더 좋다"고 한 문장으로 결론 내려도 되는가?
2. 가장 먼저 열어 볼 item trace는 무엇인가?
3. critical case의 evaluator가 틀렸을 가능성은 어떻게 확인할까?
4. latency 증가는 prompt change 때문이라고 바로 말할 수 있는가?
5. release criterion이 사전에 정의되어 있지 않다면 어떤 문제가 생기는가?

## 14. Assessment: 작은 experiment 설계

다음 중 하나를 선택한다.

```text
prompt version
model
retrieval top-k
parser rule
```

그리고 다음을 작성한다.

```text
baseline
candidate
고정할 conditions
dataset identity/version
item-level evaluator
guardrail
어떤 regression이 release를 막는가
어떤 trace evidence를 조사할 것인가
```

단순히 "두 번 실행해 평균을 비교한다"면 부족하다.

## 다음 장

지금까지 application variant를 metadata로만 표현했다. 다음 장에서는 prompt 자체를 versioned artifact로 관리하고,
**실제로 사용한 prompt version을 generation evidence에 연결**한다.

## References

- [Langfuse Academy · Experiments](https://langfuse.com/academy/experiments)
- [Experiments via SDK](https://langfuse.com/docs/evaluation/experiments/experiments-via-sdk)
- [Experiments Data Model](https://langfuse.com/docs/evaluation/experiments/data-model)
- [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)
- [Evaluate with Datasets](https://langfuse.com/docs/evaluation/get-started/offline)
- [Langfuse Workshop](https://github.com/langfuse/langfuse-workshop)
