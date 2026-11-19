# 1. State는 값이고, node는 변경분을 반환한다

첫 실습의 목표는 그래프를 화면에 그리는 것이 아니다. **각 node가 읽은 값과 쓰는 값, 그리고 다음 실행 node를
구별해** 입력에서 최종 상태까지 추적하는 것이다. 사용 파일은 [flow.py](flow.py)다.

## 왜 Python 함수만 연결하지 않는가?

일반 함수 호출에서는 호출자가 반환값을 받고 다음 함수를 직접 선택한다. LangGraph는 이 일을
**state / node / edge**로 분리한다.

- **State**: 실행 과정에서 공유되는 key-value 스냅샷. 이 실습은 `number`와 `branch` 두 key를 쓴다.
- **Node**: 현재 state를 읽어 일부 key의 **update**를 반환하는 Python 함수.
- **Edge**: 어떤 node를 다음에 실행할지 정하는 연결. 조건부 edge는 완료된 node가 갱신한 state를 읽어 선택한다.
- **START / END**: 처음과 종료를 표현하는 가상 node. 애플리케이션 로직 자체를 실행하지 않는다.

Node가 전체 state를 새로 만들 필요는 없다. 예를 들어 입력이
`{"number": 3, "branch": ""}`일 때 `classify`는 `{"branch": "odd"}`만 반환한다.
LangGraph는 **갱신하지 않은 `number`를 보존**한다. 따라서 다음 state는
`{"number": 3, "branch": "odd"}`이다.

이것이 `return state`로 모든 값을 반복해서 쓰는 Python 함수와 중요한 차이다. 이 단계에서는
같은 key를 두 node가 동시에 수정하지 않으므로 기본 규칙인 **덮어쓰기**만 생각하면 된다.
Reducer에 의한 병합은 반복과 종료 조건을 익힌 후에 다룬다.

## 그래프 구성과 제어 흐름

```text
START
  │
  ▼
classify  -- branch=odd  --> increment ─┐
  └────── -- branch=even --> double ────┴──> END
```

`classify(state)`는 `number % 2`로 홀짝을 판단해 `branch`를 설정한다. 조건부 edge의
`choose_branch(state)`는 **이 갱신이 적용된 state**를 받아 `increment` 또는 `double`의
이름을 반환한다. `increment`는 `number+1`, `double`은 `number*2`를 update한다.
하나의 입력에서 두 계산 node가 동시에 실행되는 것이 **아니다**.

[flow.py](flow.py)에서 `StateGraph(State)`로 빌더를 만들고, `add_node`로 node 이름을 등록한
다음 `add_edge` / `add_conditional_edges`로 실행 경로를 연결한다. `compile()` 뒤에
`graph.invoke(initial)`로 최종 state를 받거나 `graph.stream(..., stream_mode="updates")`로
node별 변경분을 관찰한다.

## 실행 전에 값 추적하기

입력 A는 `{"number": 3, "branch": ""}`이다.

| 시점 | node가 돌려준 update | 적용 후 state |
| --- | --- | --- |
| 입력 | 없음 | `number=3, branch=""` |
| `classify` | `branch="odd"` | `number=3, branch="odd"` |
| 조건부 edge | 다음 node `increment` | state 변경 없음 |
| `increment` | `number=4` | `number=4, branch="odd"` |

입력 B는 `{"number": 4, "branch": ""}`이다. `classify`는 `branch="even"`만 쓰고,
조건부 edge는 `double`을 선택한다. 마지막 update가 `number=8`이므로 결과는
`{"number": 8, "branch": "even"}`이다.

여기서 중요한 불변식은 **선택되지 않은 계산 node는 실행되지 않고, 갱신하지 않은 state key는 남는다**는 것이다.

## 직접 실행해 증거 읽기

저장소 root에서:

```bash
cd decks/ai-langgraph
uv sync
uv run python textbook/state_flow/flow.py
```

출력의 `update:`는 `{node_name: {key: updated_value}}` 형태다. 첫 입력에서
`classify`와 `increment` event가 보이고, 두 번째 입력에서는 `classify`와 `double`이
보여야 한다. `final`은 전체 state다.

**주의:** 예제는 update stream을 관찰한 뒤 `invoke`를 **새로 호출**해서 최종 state를 출력한다.
현재 node는 모두 순수 계산이므로 결과가 같지만, 외부 API나 DB를 쓰는 node라면 두 번의 실행이
side effect를 두 번 만들 수 있다. 한 실행의 중간 변화를 보는 것과 다시 실행하는 일을 혼동하지 않는다.

## 한 조건만 바꿔 보기

1. 실행 전 `number=5`를 추가했을 때 어떤 update 두 개와 최종 state가 나올지 적는다.
2. `choose_branch`에서 odd/even의 선택을 서로 바꾼다. **`classify`가 반환하는 값은
   그대로인데** 어떤 node가 달라지는지 예측하고 실행한다.
3. 원래 코드로 복원한 뒤 `increment`가 `{"number": state["number"] + 2}`를 반환하도록
   변경한다. `branch`가 바뀌지 않는 이유를 설명한다.

이때 변수와 print를 늘리기보다 `stream_mode="updates"`의 두 event와 `invoke` 결과만
비교한다. 변경 후 테스트가 실패하면 원래 코드를 복원한다.

## 흔한 오해와 반례

- **"node는 전체 state를 반환한다."** 아니다. `classify`가 `number`를 반환하지 않아도
  `number=3`은 보존된다.
- **"조건부 edge는 node 실행 전에 판단한다."** 아니다. `classify`가 돌려준
  `branch` update가 반영된 뒤 `choose_branch`가 호출된다.
- **"조건 분기는 두 node를 병렬 실행한다."** 아니다. `choose_branch`는 둘 중 하나의 이름만
  반환한다. 두 경로를 함께 실행하는 구조는 병렬 edge를 별도로 연결해야 한다.
- **"stream과 invoke가 같은 실행이다."** 아니다. 위 실습 코드는 두 번 호출한다.

## 이해 확인

`number=7`일 때 입력부터 종료까지 `state → update → 다음 node`를
표로 작성한다. 그 뒤 다음 질문에 답한다.

1. `classify`가 `{"number": 99}`를 반환하고 `branch`를 갱신하지 않는다면,
   기존 입력의 `branch=""`일 때 어떤 경로로 실행되는가? 판단 근거는 무엇인가?
2. `double`이 `{"branch": "done"}`만 반환하면 `number`의 최종값은 얼마인가?
3. graph가 분기를 선택하는 이유를 `node`의 반환과 `edge`의 역할로 나눠 설명하라.

**자기 점검 기준:** 호출한 node, 반환 update, 변경되지 않은 key와 종료 경로를 모두 근거와 함께
설명할 수 있어야 한다. 답을 암기하지 말고 [flow.py](flow.py)의 함수 본문을 한 줄씩 따라가며 검증한다.

## 참고

- [Graph API 개요](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [조건 분기와 제어 흐름](https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow)
