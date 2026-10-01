# 4장 · Score로 평가 Evidence 연결하기

Trace는 “무엇이 실행됐는가?”를 보여준다.
Score는 “그 실행을 어떤 기준으로 어떻게 평가했는가?”를 연결한다.

둘을 섞으면 안 된다.

## 학습 목표

- observation과 score의 역할을 구분한다.
- trace-level score와 observation-level score의 차이를 설명한다.
- deterministic evaluator의 결과를 Langfuse score로 기록한다.
- metadata/tag와 score의 용도를 구분한다.

## 1. Score는 evaluation result다

예를 들어 application code가 다음 rule을 가진다고 하자.

```python
def contains_expected_answer(output: str, expected: str) -> bool:
    return expected.lower() in output.lower()
```

이 함수가 correctness logic의 owner다.
Langfuse는 그 결과를 score로 기록할 수 있다.

```text
Python evaluator
      ↓
0 / 1
      ↓
Langfuse score
      ↓
trace와 연결해서 조회/비교
```

Langfuse에 score를 저장했다고 evaluator의 rule이 Langfuse의 책임으로 이동하는 것은 아니다.

## 2. 무엇에 점수를 붙일까

Score는 여러 level에 연결할 수 있다.

```text
trace
├─ retrieve-context   observation
└─ answer-generation observation
```

예:

- 최종 답변 correctness → trace score
- retrieval relevance → retrieval observation score
- generation style → generation observation score
- 전체 conversation 만족도 → session score

평가 대상과 score attachment target이 맞아야 한다.

## 3. Current context에서 score 만들기

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span",
    name="support-turn",
    input={"question": "환불 기간은?"},
) as root:
    answer = "구매 후 14일 이내입니다."
    root.update(output={"answer": answer})

    passed = "14일" in answer
    root.score_trace(
        name="policy-answer-correct",
        value=1.0 if passed else 0.0,
        data_type="BOOLEAN",
        comment="deterministic keyword check",
    )

langfuse.flush()
```

이 예제의 중요한 질문은 API 이름이 아니다.

> `policy-answer-correct`는 어떤 rule의 결과이며, 그 rule은 어디에 정의되어 있는가?

`BOOLEAN` score는 의미가 pass/fail이라는 뜻이다. 전송 값은 numeric 0/1 형태를 사용하더라도 evaluator의 semantic
contract가 Boolean이라는 점을 명시한다.

## 4. Score type을 선택한다

현재 Langfuse score는 Numeric, Categorical, Boolean, Text 같은 형태를 사용할 수 있다.

| 질문 | 후보 |
| --- | --- |
| pass/fail인가? | Boolean |
| 0~1 relevance인가? | Numeric |
| good / partial / bad인가? | Categorical |
| reviewer의 자유형 메모인가? | Text |

모든 판단을 0~1 숫자로 억지로 바꾸지 않는다.
Score가 무엇을 의미하는지 사람이 설명할 수 있어야 한다.

## 5. Tag와 Score를 구분한다

```text
tag
= 실행 전에 알고 있는 grouping에 적합

score
= 실행 결과를 평가한 evidence에 적합
```

예를 들어:

```text
channel:web          → tag
feature:support      → tag
correctness:true     → score
hallucination:0.2    → score
```

## 6. Evaluator failure와 application failure를 구분한다

Evaluator가 exception을 내면 application output이 잘못된 것과는 다른 상태다.

```text
application output exists
        ↓
evaluator failed
```

이 경우 score가 없다는 사실을 “0점”으로 바꾸면 안 된다.

```text
no score
≠ score 0
```

이 구분은 experiment 결과를 해석할 때 매우 중요하다.

## 7. 연습

다음 평가를 어디에 연결할지 정하고 이유를 설명한다.

1. retrieval top-3 문서 중 정답 문서가 포함됐는가
2. 최종 답변이 JSON schema를 만족했는가
3. 전체 10-turn conversation에 대한 사용자의 만족도
4. 특정 generation의 toxicity score
5. request가 `mobile` channel에서 왔는가

마지막 항목은 정말 score가 맞는지도 검토한다.

## 다음 장

한 번의 trace에 score를 붙이는 것만으로는 regression test가 되지 않는다.
다음 장에서는 중요한 사례를 **dataset**으로 보존한다.

## References

- [Scores via API/SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)
- [Scores Data Model](https://langfuse.com/docs/evaluation/scores/data-model)
- [Evaluation Core Concepts](https://langfuse.com/docs/evaluation/core-concepts)
