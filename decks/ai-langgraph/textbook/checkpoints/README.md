# 3. Checkpoint는 실행 중인 graph의 상태를 thread별로 보존한다

[이전 단위](../reducers/README.md)까지 graph는 모든 실행을 현재 메모리에만 두었다.
이제 하나의 graph object에서 **thread별 최신 state**를 저장하고 다음 입력이 이를
어떻게 쓰는지 관찰한다. 사용 파일은 [checkpoints.py](checkpoints.py)다.

이 단위는 아직 interrupt를 사용하지 않는다. checkpoint 저장과 **새 입력**을 먼저
구분해야 다음 단위의 resume를 정확히 이해할 수 있다.

## 왜 checkpoint가 필요한가?

하나의 함수 호출 결과만 있으면 이후 다른 요청에서 이전 state를 읽기 어렵다.
LangGraph는 checkpointer를 연결하면 graph를 실행하면서 **super-step 경계**마다
thread에 대한 state snapshot을 저장한다.

- **thread ID**: 어떤 연속된 graph 실행의 state를 읽고 갱신할지 가리키는 식별자.
- **checkpoint**: 한 super-step 이후의 state, 다음에 실행할 node, 실행 메타데이터를 포함하는 snapshot.
- **`get_state(config)`**: 해당 thread의 최신 checkpoint를 읽는다.
- **`next`**: checkpoint에서 실행 대기 중인 node 목록. 빈 tuple `()`은 이 graph 실행의 완료를 뜻한다.

`InMemorySaver`는 로컬 학습용이다. 이 스크립트 프로세스가 끝나면 저장된 checkpoint도
사라진다. 실무에서 말하는 durable persistence나 서버 재시작 복구가 가능한 저장소로
오인하지 않는다.

## 실행 구조와 state 계산

```text
START -> add -> END
```

state는 `total`과 `delta`로 구성된다. `add` node는 입력 state의
`total + delta`를 계산하고 `{"total": new_total}`만 반환한다. `delta`는
갱신하지 않으므로 기존 값이 보존된다.

```python
graph = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "study-a"}}
result = graph.invoke({"total": 10, "delta": 2}, config=config)
```

첫 결과는 `{"total": 12, "delta": 2}`다. 이후 같은 thread에
`{"delta": 5}`라는 **새 입력**을 주면 이전의 `total=12`가 유지되고
`delta`만 5로 바뀐 뒤 `add`가 다시 실행되어 `total=17`이 된다.

이것은 실패하거나 중단된 node를 재개하는 동작과 **다르다**.
이전 실행은 `END`까지 완료되었고, 다음 `invoke`는 현재 저장된 state에 새 입력을
반영해 처음 entry node에서 다시 시작한다.

## 별도 thread는 별도 state다

같은 compiled graph object라도 다른 `thread_id`를 사용하면 state가 분리된다.

| 순서 | thread | 호출에 넘긴 input | 호출 완료 state |
| --- | --- | --- | --- |
| 1 | `study-a` | `total=10, delta=2` | `total=12, delta=2` |
| 2 | `study-a` | `delta=5` | `total=17, delta=5` |
| 3 | `study-b` | `total=1, delta=2` | `total=3, delta=2` |

이 실습은 `study-b`가 `study-a`의 `total=17`을 읽지 않는다는 것을 보여 준다.
서로 다른 graph object 각각에 새 `InMemorySaver`를 만들면 같은 `thread_id`라고 해도
기존 프로세스의 상태를 공유하지 않는다는 점도 기억한다.

## 실행하여 snapshot 관찰하기

```bash
cd decks/ai-langgraph
uv run python textbook/checkpoints/checkpoints.py
```

출력에서 `A checkpoint:` 행의 `values`와 `next`를 구분한다.
`next=()`는 첫 실행이 완료됐다는 뜻이다. 여기서 다시 `invoke({"delta": 5})`를
하는 것은 **완료된 thread에 새 입력을 적용**하는 것이지 중단 지점의 강제 재개가 아니다.

추가로 코드에 다음 줄을 넣어 보고 각 checkpoint의 `values`와 `next`를 조사한다.

```python
for snapshot in graph.get_state_history(first):
    print(snapshot.values, snapshot.next)
```

반환 순서는 **최근 checkpoint가 먼저**다. 역사에 보이는 기록의 개수는 런타임과
체크포인트 세부 구현에 따라 달라질 수 있으므로, 개수 대신 어떤 `total` 상태가
보존되는지를 설명한다.

## 실패하기 쉬운 해석

- **"thread_id는 자동으로 새 실행을 만든다."** 아니다. 같은 ID는 이전 state를 참조할 수 있다.
- **"새 입력은 언제나 상태 전체를 교체한다."** 아니다. 이전 state key는 update되지 않았다면 남는다.
- **"checkpoint = 외부 API 요청도 정확히 한 번."** 아니다. checkpoint는 graph state를 보존한다.
  외부 side effect의 멱등성·재시도 경계는 별도로 설계해야 한다.
- **"InMemorySaver를 쓰면 프로세스 재시작 후에도 복원된다."** 아니다. 메모리는 휘발성이다.

## 직접 판단하기

1. A의 첫 입력을 `{"total": 10, "delta": -3}`으로 바꾸면
   A의 두 번째 실행에서 결과는 어떻게 달라지는가?
2. B 입력을 `{"delta": 2}`만 전달하면 왜 첫 호출이 성공하지 못할 수 있는가?
   B에는 이전 `total`이 없다는 조건을 반영해 설명한다.
3. 완료된 A에서 `next=()`인데, 같은 thread로 또 invoke하면 왜 `add`가 실행되는가?
   새 입력과 미완료 실행의 resume를 비교하라.

**통과 기준:** thread마다 첫/다음 호출의 state를 예측하고,
`values`, `next`, 체크포인터 보존 범위를 각각 설명한다.

## 참고

- [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- [Persistence와 store 차이](https://docs.langchain.com/oss/python/langgraph/persistence)
