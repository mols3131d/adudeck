# 5. Interrupt 이후 어디부터 다시 실행되는가?

[Checkpoint 교본](../checkpoints/README.md)에서는 완료된 thread에 새 입력을 보냈다.
이번에는 node 내부에서 **사용자 승인을 기다리는 동안 실제로 멈추고**, 같은 thread에
`Command(resume=...)`를 전달해 재개한다. 실습 파일은 [approval.py](approval.py)다.

목표는 `interrupt()` 문법보다 더 중요하다. **어떤 작업이 재실행되고 어떤 작업은
중복 실행되지 않는지**를 checkpoint와 연결해 설명해야 한다.

## 작은 승인 흐름

```text
START -> prepare -> request_approval -> finish -> END
                         │
                         └─ interrupt() : pause
                            │
                    Command(resume=True)
                            │
                       node의 시작부터 재실행
```

state는 `number`, `approved`, `finished`다.

- `prepare`가 `number`를 2에서 3으로 갱신한다.
- `request_approval`는 `{"question": "Proceed?", "number": 3}`을
  `interrupt()`에 전달한다. 여기서 **node가 완료되지 않고** 중단된다.
- 재개 시 `interrupt()`는 `Command(resume=True)`의 `True`를 돌려준다.
  node가 `{"approved": True}`를 반환한 뒤 `finish`가 `finished=True`를 기록한다.

`interrupt()`를 사용하려면 **checkpointer와 thread ID가 필요하다**. 여기서는
`InMemorySaver`를 쓰므로 같은 Python 프로세스 안에서만 재개할 수 있다.

## 실행 전 trace 예측

예제에는 `trace`라는 list에 node 이름을 기록하는 **관찰 도구**가 들어 있다.
이것은 graph state도 아니고 checkpoint에 보존되는 데이터도 아니다. 외부 서비스나
운영 로그를 흉내 내는 대신, 같은 프로세스에서 함수 본문이 몇 번 실행되는지 보려는 장치다.

실행 전에 다음 세 시점의 trace를 예측하라.

| 시점 | 최신 state | 다음 node |
| --- | --- | --- |
| `prepare` 완료 | `number=3, approved=None` | `request_approval` |
| `interrupt()`로 중단 | `number=3, approved=None` | `request_approval` 대기 |
| `Command(resume=True)` 후 | `number=3, approved=True, finished=True` | 없음 |

이때 `trace`는 다음처럼 변한다.

```text
첫 호출:  ["prepare", "request_approval"]
재개 후:  ["prepare", "request_approval", "request_approval", "finish"]
```

**왜 `prepare`는 한 번인데 `request_approval`는 두 번일까?**
Checkpoint는 `prepare`가 완료된 super-step을 보존한다. 그러나
`request_approval`의 `interrupt()`는 **node 내부**에서 발생했다. LangGraph는
중단된 node의 Python 코드 중간 줄에서 계속하지 않고 **node의 시작부터 다시 실행**한다.

따라서 `interrupt()` 앞에 놓인 작업은 두 번 실행될 수 있다.
반대로 완료된 이전 node인 `prepare`의 작업은 이 재개 경로에서 반복되지 않는다.

## 직접 실행하고 비교하기

```bash
cd decks/ai-langgraph
uv run python textbook/interrupts/approval.py
```

출력에서 다음을 개별적으로 확인한다.

1. `interrupt:`의 payload가 `number=3`을 포함하는가?
2. `saved:`의 `approved`가 아직 `None`인가?
3. `next:`에 `request_approval`가 남아 있는가?
4. `node visits:`에서 `request_approval`가 두 번 나타나는가?
5. 재개 뒤 최종 `approved=True`, `finished=True`인가?

`paused["__interrupt__"]`는 이 실습의 `graph.invoke` API가 제공하는
중단 payload다. 다른 이벤트 스트리밍 API는 interrupt 정보를 다른 구조로 전달한다.
중단 응답의 `__interrupt__` 필드를 최종 state 값이라고 오인하지 않는다.

## 승인 거절과 side effect 경계

이제 `Command(resume=True)`를 `Command(resume=False)`로 바꾸기 전에
어떤 항목이 달라질지 예측하라. `number=3`과 재실행 횟수는 같지만
`approved=False`, `finished=False`가 되어야 한다.

추가 변형은 **실제 외부 부작용 없이** 수행한다.
`trace.append("request_approval")`를 `interrupt(...)` 아래로 옮기면
이름을 기록하는 횟수는 어떻게 바뀔까? 이것은 `interrupt` 앞부분이 다시 실행되는
현상을 관찰 도구로 보여 준다.

외부 결제·메일·DB 쓰기를 `interrupt()` 앞에 두면 재개 시 중복 실행될 위험이 있다.
이를 **checkpoint가 exactly-once를 보장한다**고 생각해서는 안 된다.
실제 부작용에는 idempotency key, 중복 검증, durable task 같은 별도 경계가 필요하다.
이번 실습은 그런 외부 작업을 호출하지 않는다.

## 이해 확인

1. `prepare`에서 외부 API를 호출한 뒤 `request_approval`에서 interrupt하면,
   이번 재개에서 어느 node가 재실행되는가? 단, 오류·재시도는 없다고 가정한다.
2. `request_approval`에서 `interrupt()` 전에 DB insert를 한 경우
   승인 재개로 중복될 수 있는 부분은 어디인가?
3. 같은 thread ID를 가진 `Command(resume=True)`와
   `graph.invoke({"number": 9, ...}, config)`를 비교한다.
   중단 재개와 새 입력의 의미가 어떻게 다른가?

**통과 기준:** checkpoint에 남는 state, 대기 중 node, 실제 재실행한 함수와
side effect 위험을 하나의 trace로 설명한다.

## 참고

- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- [Graph API의 재실행과 멱등성](https://docs.langchain.com/oss/python/langgraph/graph-api)
