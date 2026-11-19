# 3. 왜 병렬 node에는 reducer가 필요한가?

[첫 단위](../state_flow/README.md)에서는 한 번에 한 계산 node만 실행되어
state key `number`를 갱신했다. 이제 두 node가 **같은 super-step에** `events`라는
key를 업데이트하게 만든다. 이 단위의 학습 결과는 reducer를 암기하는 것이 아니라,
**동시에 반환된 update들이 왜 단순 덮어쓰기로 합쳐지지 않는지** 설명하는 것이다.

실습 파일은 [parallel_updates.py](parallel_updates.py)다.

## 실행 모델: node 병렬 실행과 super-step

LangGraph는 여러 node가 같은 단계에 실행되도록 할 수 있다. 동일 super-step의
`left`, `right`는 각자 **이전 super-step까지의 동일한 state**를 읽고 독립적인
update를 반환한다. 한쪽 node가 반환한 새 `events`를 다른 node가 바로 읽는 모델이 아니다.

```text
START -> seed ─┬─> left  ─┐
               └─> right ─┴─> join -> END
                        (동일 super-step)
```

시작 state가 `{"events": [], "summary": ""}`일 때 `seed`가 `["seed"]`를 쓴다.
다음 super-step에서 `left`와 `right`는 각각 `["left"]`, `["right"]`를 반환한다.

**질문:** 한 state key에 두 update가 동시에 들어오는데, 덮어쓰기로 하나를 택하면
다른 결과를 잃게 된다. 그래서 이 예제는 key별 병합 규칙을 선언한다.

## reducer는 state의 key별 계산식이다

```python
from typing import Annotated
import operator

class State(TypedDict):
    events: Annotated[list[str], operator.add]
    summary: str
```

`Annotated[list[str], operator.add]`에서 `operator.add`는 현재 list와 update list를
연결하는 reducer다. 예를 들어:

```text
current: ["seed"]
update:  ["left"]
result:  ["seed", "left"]

다른 병렬 update ["right"]를 병합
result: ["seed", "left", "right"]  (순서 보장 아님)
```

중요한 것은 list에 항목을 **추가하는 갱신 의미**다. 새 `events` 값을 반환한 node가
전체 history를 다시 구성할 필요는 없다. 반면 `summary: str`에는 reducer가 없으므로
`join`의 반환값이 기존 값을 덮어쓴다.

**주의:** 동일 super-step의 병렬 update 순서에 의존하지 않는다. 예제의 `join`은
`sorted(state["events"])`로 summary를 만들어 결과 비교를 쉽게 한다.
순서가 업무 의미를 가진다면 각 update에 명시적 정렬 key를 포함하는 등 별도 설계가 필요하다.
`operator.add`만으로 의미 있는 실행 순서를 보장하지 않는다.

## node 입력 스키마에 대한 주의

이번 파일은 동일 node 함수를 `State`와 `PlainState` 두 그래프에 재사용한다.
LangGraph는 node의 첫 인자 타입 annotation을 입력 스키마로 읽을 수 있다.
node 인자에 `State`를 고정하면 `PlainState` 그래프의 같은 key `events`가
서로 다른 채널 타입으로 충돌할 수 있다. 그래서 두 상태를 비교하는 **이 실습의 재사용 함수**에는
입력 annotation을 생략하고 `StateGraph(...)`에서 상태 스키마를 명시한다.
이는 전체 앱에서 타입 annotation을 생략하라는 권장이 아니다.

## fan-in의 의미

`builder.add_edge(["left", "right"], "join")`은 **양쪽 node가 완료된 뒤**
`join`을 한 번 실행하도록 한다. 각 node에서 따로 `add_edge("left", "join")`와
`add_edge("right", "join")`를 호출하는 것과 일반적으로 같은 계약이 아니다.
분기 길이가 달라지면 별개의 edge는 `join`을 여러 번 예약할 수 있다.

`join`의 입력에는 `["seed"]`와 양쪽 update가 모두 포함되어야 한다.
`summary`는 `"left, right, seed"`가 된다. 최종 `events`는 세 항목을 포함하며
`summary` 문자열의 정렬과 같은 순서라고 가정하면 안 된다.

## 예측 → 실행 → 관찰

저장소 root에서:

```bash
cd decks/ai-langgraph
uv run python textbook/reducers/parallel_updates.py
```

`updates` stream에서 `seed`, `left`, `right`, `join` node의
**key별 update**를 관찰한다. `summary`는 `join`의 output이며,
`join`이 실행되기 전까지는 변경되지 않는다.

그 다음 코드는 같은 graph topology를 `PlainState`로 다시 만들고,
`events`에 reducer가 없을 때 발생하는 `InvalidUpdateError`를 보여 준다.
이 실패는 고의적인 학습 반례다. `try`는 이 특정 예외만 받으며, 예상하지 못한
다른 예외를 성공처럼 숨기지 않는다.

`stream`과 `invoke`는 **별도 실행**이다. 이 단위에서는 외부 side effect가
없어 비교해도 안전하지만, 실제 I/O를 가진 node의 재실행은 별도 문제다.

## 원인 분석 연습

1. `seed`가 `["start"]`를 반환하도록 수정한다. `events`와 `summary`의
   어느 부분이 바뀔지 예측하고 다시 실행한다.
2. `right`가 `{"summary": "right"}`만 반환한다면 병렬 갱신 충돌은 발생하는가?
   `events`의 항목 수와 `summary`의 최종값을 설명한다.
3. `join`을 `left`에서만 연결하고 `right`의 결과도 기다린다고 주장하는
   코드 리뷰를 받았다. 어떤 super-step 경계가 빠졌는지 설명하고 올바르게 고친다.
4. `operator.add` 대신 `set` 기반 병합을 사용하고 싶다면 어떤 순서 정보가
   사라질 수 있는가? 요구사항이 단순 중복 제거인지 순서 보존인지 먼저 정한다.

## 이해 확인

아래의 두 구현 중 어떤 것이 요구사항을 보장하는지 근거와 함께 판단한다.

- A: `events: list[str]` + 서로 다른 두 node의 동시 `{"events": [...]}` 반환.
- B: `events: Annotated[list[str], operator.add]` + 같은 두 update.

각 구현에 대해 실제로 일어나는 결과(병합 또는 오류), 그 이유, `join`에서
관찰 가능한 값, 순서에 대한 보장 수준을 말할 수 있어야 한다.

**통과 기준:** 코드 없이 super-step별 읽기 state와 반환 update를 구분하고,
`InvalidUpdateError`가 나는 조건과 reducer가 필요한 이유를 예측한다.
오답이라면 [첫 단위](../state_flow/README.md)의 partial update부터 다시 추적한다.

## 참고

- [State와 reducer 공식 문서](https://docs.langchain.com/oss/python/langgraph/graph-api-state)
- [병렬 edge와 fan-in 공식 문서](https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow)
