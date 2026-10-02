# 4장 · Score: 실행 Evidence와 평가 Evidence를 분리하기

Trace를 보면 **무엇이 실행되었는지** 알 수 있다. 그러나 trace가 있다고 해서 그 실행이 좋은지 나쁜지 자동으로 알 수
있는 것은 아니다.

이번 장에서는 이 두 종류의 evidence를 분리한다.

```text
observation
= execution evidence

score
= evaluation evidence
```

핵심은 "Langfuse에 점수를 저장한다"가 아니다.

> **먼저 평가 질문과 evaluator의 의미를 정의하고, 그 결과를 올바른 execution target에 연결한다.**

## 학습 목표

- trace/observation과 score의 책임을 구분한다.
- trace-level, observation-level, session-level score가 각각 어떤 질문에 적합한지 설명한다.
- Boolean/Numeric/Categorical/Text score를 의미에 맞게 선택한다.
- deterministic evaluator가 계산한 결과를 score로 연결한다.
- `score=0`, `score missing`, `evaluator error`, `application error`를 구분한다.
- tag/metadata와 score를 혼동하지 않는다.

## 1. 먼저 "평가 질문"을 쓴다

나쁜 시작:

```text
score 하나 만들자
```

좋은 시작:

```text
질문:
"최종 답변이 환불 기간 14일이라는 정책을 보존했는가?"

판정 주체:
deterministic Python evaluator

평가 대상:
전체 support-turn의 최종 결과

결과 의미:
true = 정책 조건을 보존
false = 정책 조건을 보존하지 못함
```

이제서야 score 이름과 target이 의미를 가진다.

```text
policy-answer-correct
→ trace-level Boolean score
```

Score의 API shape보다 **semantic contract**가 먼저다.

## 2. Score target은 evaluator가 판단한 범위와 맞춘다

다음 trace를 보자.

```text
support-turn
├─ retrieve-policy
└─ answer-generation
```

서로 다른 evaluator가 있다.

```text
"최종 답변이 정책상 맞는가?"
→ whole request 결과를 평가
→ trace-level score

"retrieve-policy가 관련 문서를 가져왔는가?"
→ retrieval operation을 평가
→ observation-level score

"이 generation의 문체가 규칙을 따르는가?"
→ generation observation을 평가
→ observation-level score

"10-turn 대화 전체 만족도는 어떤가?"
→ session-level score
```

Langfuse의 score data model은 trace, observation, session, dataset run 같은 서로 다른 target에 score를 연결할 수 있다.
Target을 선택할 때 "API가 무엇을 허용하는가?"보다 "evaluator가 **어느 범위의 evidence를 보고 판단했는가?**"를 먼저
묻는다.

## 3. Worked example: 평가한 뒤 기록한다

[`score_evidence.py`](score_evidence.py)는 두 deterministic evaluator를 사용한다.

```python
def answer_mentions_policy_days(answer: str) -> bool:
    return "14일" in answer


def retrieval_contains_policy(document: str) -> bool:
    return "14일" in document and "환불" in document
```

이 evaluator는 교육용으로 매우 단순하다. 실제 semantic correctness를 완전히 보장하지 않는다.

그 다음 **평가를 먼저 완료하고** score를 기록한다.

```python
answer_passed = answer_evaluator(answer)
retrieval_passed = retrieval_evaluator(document)

root_observation.score_trace(
    name="policy-answer-correct",
    value=1.0 if answer_passed else 0.0,
    data_type="BOOLEAN",
)

retrieval_observation.score(
    name="retrieval-relevant",
    value=1.0 if retrieval_passed else 0.0,
    data_type="BOOLEAN",
)
```

여기에는 중요한 invariant가 있다.

```text
평가 성공
→ score가 존재

평가 결과가 나쁨
→ score = 0

평가 자체가 실패
→ score를 만들지 않음
```

## 4. `0`과 `없음`은 다른 상태다

가장 위험한 실수 중 하나는 evaluator exception을 잡아서 자동으로 `0`으로 바꾸는 것이다.

```text
A. output을 정상 평가함
result = false
→ score 0

B. evaluator timeout
판정 자체를 못함
→ no score / evaluator error
```

A와 B를 같은 값으로 만들면 experiment에서 다음 질문에 답할 수 없게 된다.

- candidate가 정말 품질이 낮았나?
- evaluator infrastructure가 깨졌나?
- score ingestion이 누락됐나?

[`test_score_evidence.py`](test_score_evidence.py)는 이 distinction을 직접 검증한다.

```bash
python textbook/04-scores/test_score_evidence.py
```

특히 evaluator가 exception을 내는 test에서는 score recorder가 비어 있어야 한다.

## 5. Score type은 측정 의미에 맞춘다

현재 Langfuse score에는 Numeric, Boolean, Categorical, Text 같은 형태가 있다. SDK에는 correction과 같은 추가
score type도 존재하지만, 이 deck의 core에서는 아래 네 가지로 reasoning을 연습한다.

| 평가 질문 | 적합한 형태 | 이유 |
| --- | --- | --- |
| schema validation에 통과했는가? | Boolean | pass/fail contract |
| retrieval relevance가 0~1 중 어느 정도인가? | Numeric | 연속적인 정도 |
| `good / partial / bad` 중 어디인가? | Categorical | 순수 숫자보다 category 의미가 중요 |
| reviewer가 근거를 자유롭게 기록하는가? | Text | 자유형 설명 |

모든 것을 `0.83` 같은 숫자로 바꾸면 정밀해 보일 수 있지만, 숫자가 무엇을 의미하는지 설명할 수 없다면 좋은 metric이
아니다.

## 6. Boolean score의 numeric wire value와 semantic type을 구분한다

예제에서는 다음처럼 기록한다.

```python
value=1.0 if passed else 0.0
data_type="BOOLEAN"
```

`0.0/1.0`을 전송하더라도 의미는 continuous quality가 아니라 Boolean 판정이다.

```text
0.0
= "조금 덜 정확함"이 아니라 false

1.0
= true
```

Score의 data type은 dashboard formatting만을 위한 정보가 아니라 evaluator contract를 읽는 사람에게 의미를 전달한다.

## 7. Tag / metadata / score를 구분한다

`channel=web`을 score로 만들면 안 되는 이유를 생각해 보자.

```text
tag / metadata
= 실행의 context 또는 grouping

score
= 실행을 평가한 결과
```

예:

```text
channel:web                     metadata/tag
feature:support                 tag
model_variant:candidate         metadata
policy-answer-correct:true      score
retrieval-relevance:0.82        score
```

"나중에 filter하고 싶다"는 이유만으로 모든 값을 score로 만들지 않는다.

## 8. Live lab

Langfuse credential을 설정한 뒤 실행한다.

```bash
uv run python textbook/04-scores/score_evidence.py
```

UI에서 같은 trace를 열고 다음을 확인한다.

1. `policy-answer-correct`는 trace 전체에 붙어 있는가?
2. `retrieval-relevant`는 `retrieve-policy` observation에 붙어 있는가?
3. score 이름만 보고 evaluator 질문을 대략 추론할 수 있는가?
4. comment가 score의 의미를 보조하는가?
5. 같은 실행에 metadata와 score가 역할별로 분리되어 있는가?

### Variation

`score_evidence.py`의 answer를 다음처럼 바꿔 본다.

```text
"환불할 수 없습니다."
```

예측:

```text
application execution은 성공
score는 존재
policy-answer-correct = false
```

그 다음 evaluator를 의도적으로 exception 나게 바꾼다.

예측:

```text
application output은 존재
evaluator는 실패
score는 생성되지 않음
```

두 상태를 UI/로그에서 같은 것으로 보지 않는 것이 핵심이다.

## 9. Evaluator는 누구의 책임인가?

Langfuse에 score를 저장했다고 correctness rule의 owner가 Langfuse로 이동하는 것은 아니다.

```text
domain/application evaluator
→ 무엇이 맞는지 정의하고 계산

Langfuse
→ 그 evaluation evidence를 execution과 연결하고 조회/비교
```

Langfuse 자체에서 code evaluator나 LLM-as-a-Judge를 실행할 수도 있다. 그래도 **평가 기준의 의미와 신뢰 경계**는
사용자가 설계해야 한다.

8장에서 evaluator 종류를 다시 비교한다.

## 10. 좋은 evaluator의 첫 기준: 질문이 좁고 판정 가능해야 한다

다음 두 score 이름을 비교한다.

```text
quality
```

```text
refund-policy-correct
```

두 번째가 완벽하다는 뜻은 아니다. 그러나 무엇을 평가하는지 훨씬 쉽게 검토할 수 있다.

좋은 evaluator를 설계할 때 묻는다.

- 어떤 failure mode를 잡으려는가?
- input/output 중 어떤 evidence가 필요한가?
- deterministic code로 판정 가능한가?
- human label이 필요한 주관적 기준인가?
- false positive / false negative의 비용은 무엇인가?
- evaluator version이 달라지면 비교가 깨지는가?

Score는 숫자 하나가 아니라 **평가 contract의 결과**다.

## 11. 연습: target과 type을 설계한다

각 항목에 대해 다음을 정한다.

```text
target
score name
data type
판정 owner
```

항목:

1. retrieval top-3에 정답 문서가 포함됐는가?
2. final JSON이 schema를 만족했는가?
3. 전체 10-turn conversation에 대한 사용자 만족도
4. 특정 generation의 toxicity category
5. request가 mobile channel에서 왔는가?
6. evaluator API가 timeout 됐는가?

5번과 6번은 **score로 만들지 않는 선택**도 검토한다.

## 12. Cumulative checkpoint

다음 상태를 정확히 구분해 설명할 수 있어야 한다.

```text
application error
output produced + score 0
output produced + score 1
output produced + evaluator error
output produced + score missing
```

이 구분이 흐려지면 이후 dataset/experiment의 aggregate 결과도 신뢰하기 어려워진다.

## 다음 장

Score는 한 실행의 평가 evidence다. 하지만 같은 failure를 다음 변경에서도 다시 확인하려면 **사례 자체를 보존**해야 한다.
다음 장에서는 production evidence를 dataset item으로 승격한다.

## References

- [Scores via API/SDK](https://langfuse.com/docs/evaluation/evaluation-methods/scores-via-sdk)
- [Scores Data Model](https://langfuse.com/docs/evaluation/scores/data-model)
- [Evaluation Core Concepts](https://langfuse.com/docs/evaluation/core-concepts)
- [Langfuse Academy · Evaluation](https://langfuse.com/academy/evaluation)
