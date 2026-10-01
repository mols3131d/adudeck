# 5장 · Trace를 Dataset으로 바꾸기

Production에서 문제를 하나 발견하고 고쳤다고 하자.
그 사례를 기억에만 남겨 두면 다음 prompt/model 변경에서 같은 문제가 다시 생길 수 있다.

Dataset은 중요한 사례를 **반복 실행할 수 있는 test input**으로 바꾸는 장치다.

## 학습 목표

- dataset과 dataset item의 역할을 설명한다.
- input과 expected output을 평가 가능한 형태로 설계한다.
- production trace에서 가치 있는 실패 사례를 dataset으로 연결하는 이유를 설명한다.
- dataset version이 experiment 비교에 왜 중요한지 설명한다.

## 1. Dataset은 로그 창고가 아니다

나쁜 dataset 전략:

```text
production trace 10만 개
→ 전부 dataset에 복사
```

좋은 dataset은 질문이 있다.

```text
이 변경이 과거의 중요한 실패를 다시 만들지 않는가?
이 edge case를 처리하는가?
정상적인 대표 사례에서도 품질을 유지하는가?
```

따라서 dataset item은 **의도적으로 선택된 test case**여야 한다.

## 2. Dataset item

가장 단순한 형태:

```text
input
expected_output (optional)
metadata (optional)
```

예:

```json
{
  "input": {
    "question": "상품을 받은 지 10일 됐습니다. 환불 가능한가요?"
  },
  "expected_output": {
    "eligible": true,
    "policy_days": 14
  }
}
```

Expected output은 반드시 자연어 정답일 필요가 없다.
오히려 deterministic evaluator가 판단하기 좋은 structured expectation이 더 유용할 수 있다.

## 3. Dataset 만들기

```python
from langfuse import get_client

langfuse = get_client()

langfuse.create_dataset(
    name="support/refund-policy",
    description="환불 정책 회귀 테스트 사례",
)

langfuse.create_dataset_item(
    dataset_name="support/refund-policy",
    input={
        "question": "상품을 받은 지 10일 됐습니다. 환불 가능한가요?",
    },
    expected_output={
        "eligible": True,
        "policy_days": 14,
    },
)
```

## 4. Production trace에서 가져오기

실전에서 강력한 흐름은:

```text
production trace
→ 실패 발견
→ 원인 이해
→ expected behavior 정의
→ dataset item 생성
```

Langfuse dataset item은 source trace/observation과 연결할 수 있다.
그러면 “왜 이 test case가 존재하는가?”를 원래 production evidence까지 추적할 수 있다.

```python
langfuse.create_dataset_item(
    dataset_name="support/refund-policy",
    input={"question": "..."},
    expected_output={"eligible": True},
    source_trace_id="trace-id-from-production",
)
```

## 5. 무엇을 expected output으로 저장할까

나쁜 expected output:

```text
모범 답변 전체 문장을 한 글자도 다르지 않게 일치
```

LLM output은 표현이 달라질 수 있다.
정확히 같아야 하는 contract가 아니라면 strict string equality는 좋은 evaluator가 아닐 수 있다.

예를 들어 정책 assistant라면:

```json
{
  "policy_days": 14,
  "eligible": true
}
```

처럼 핵심 property를 기대값으로 두고 별도의 evaluator가 실제 answer를 판단할 수 있다.

## 6. Dataset version

현재 Langfuse는 dataset item의 add/update/delete/archive가 일어나면 dataset version을 추적한다.

왜 중요한가?

```text
Experiment A
dataset version X

Experiment B
다른 dataset version Y
```

이면 두 run의 평균 score 차이가 application change 때문인지 dataset change 때문인지 헷갈릴 수 있다.

Release decision을 비교할 때는 가능한 한 **같은 dataset version과 같은 evaluator definition**을 사용한다.

## 7. 좋은 dataset의 구성

처음부터 거대한 benchmark를 만들 필요는 없다.

작은 시작 예:

```text
normal case 2개
historical failure 2개
boundary case 2개
```

그리고 production에서 중요한 실패가 발견될 때 추가한다.

## 연습

다음 production 사례 중 dataset에 넣을 후보와 넣지 않을 후보를 나눈다.

1. 한 번 발생한 provider timeout
2. 반복적으로 틀리는 환불 기간 질문
3. 개인정보가 그대로 들어 있는 raw customer transcript
4. 새로운 prompt가 자주 틀리는 structured output boundary case
5. 이미 infrastructure monitoring이 소유하는 CPU spike

선택할 때 **재현할 학습 가치**, **평가 가능성**, **privacy**를 함께 설명한다.

## 다음 장

Dataset은 재사용 가능한 문제 모음이다.
다음 장에서는 같은 dataset을 여러 application variant에 실행해 **experiment**를 만든다.

## References

- [Langfuse Datasets](https://langfuse.com/docs/evaluation/experiments/datasets)
- [Evaluate with Datasets](https://langfuse.com/docs/evaluation/get-started/offline)
- [Compare Experiments](https://langfuse.com/docs/evaluation/experiments/compare-experiments)
