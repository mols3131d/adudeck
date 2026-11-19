# 5. 종합 실습: 승인형 stateful workflow를 추적하고 복구한다

앞선 네 단위에서는 state·조건 분기, 병렬 reducer, checkpoint, interrupt를 서로 분리해서 보았다.
이제 하나의 작은 graph에 결합한다. [workflow.py](workflow.py)를 실행하고 **정상 승인,
승인 거절, 입력 조건 위반, 작업 실패 후 재시도**를 구별한다.

이 실습은 외부 API를 호출하지 않는다. 숫자 변경이라는 작은 가상 작업을 사용하므로
실패를 만들어도 돈이나 실제 데이터에 영향을 주지 않는다.

## 어떤 문제를 풀 것인가?

숫자를 입력받아 짝수면 2배, 홀수면 1을 더하는 계산을 실행하려 한다. 다만 계산 전에
범위 검증과 parity 확인을 **병렬로** 실행하고, 사람이 승인한 후에만 적용한다.
`number`가 0~20 밖이면 승인해도 적용하지 않는다.

```text
START → classify ─┬→ check_range  ─┐
                   └→ check_parity ─┴→ ask_approval
                                        │ interrupt()로 대기
                                     [resume]
                                        │
                                 조건부 route
                                 ├→ apply  → END
                                 └→ cancel → END
```

이 구조는 각 학습 개념의 소유 범위를 분리한다. `classify`가 `route`를
만들고, 두 check node는 같은 `checks` key에 각각 항목 하나를 추가한다.
`ask_approval`은 완료된 검사 결과를 본 다음 `interrupt()`로 멈춘다.
승인 후 `choose_action`은 `approved=True`와 `range-ok` 두 조건이 **모두**
성립해야 `apply`를 선택한다.

## state와 super-step 계산

```python
class State(TypedDict):
    number: int
    route: str
    checks: Annotated[list[str], operator.add]
    approved: bool | None
    outcome: str
```

`checks`에만 reducer `operator.add`가 있다. 동일 super-step의
`check_range`와 `check_parity`가 각각 `{"checks": ["range-ok"]}`와
`{"checks": ["odd"]}`를 반환해도 서로 덮어쓰지 않는다. 두 update의 상대 순서는
불변식이 아니다. `ask_approval`에서 `sorted(checks)`를 사용하는 것은 **표시와
비교를 안정화하기 위한 것**이지 LangGraph가 check node의 실행 순서를 보장해서가 아니다.

입력 `number=3`의 실행을 먼저 추적한다.

| 경계 | 변경된 값 | 보존된 값 / 다음 node |
| --- | --- | --- |
| 처음 | `number=3` | `checks=[]` |
| `classify` 이후 | `route="odd"` | `number=3` |
| 두 check node 이후 | `checks`에 `range-ok`, `odd` 포함 | `ask_approval` |
| `interrupt()` | 아직 `approved=None` | `next=("ask_approval",)` |
| `Command(resume=True)` | `approved=True` | `apply` 선택 |
| `apply` 이후 | `number=4, outcome="applied"` | `next=()` |

Checkpoint가 저장한 중간 상태는 `graph.get_state(config).values`로,
다음에 실행할 node는 `.next`로 확인한다. 이 실습에서 `InMemorySaver`는
현재 프로세스에서만 유지되는 학습용 저장소다.

## 실행 전에 네 가지 경로 예측하기

`initial_state(number)`는 입력의 빈 필드를 모두 명시한다. `number`만 바꿔
동일한 실험을 재현할 수 있다.

1. **3, 승인:** 범위 유효, 홀수, 적용되어 4가 된다.
2. **4, 승인 거절:** 유효한 짝수여도 `approved=False`면 `cancelled`이고 숫자는 4다.
3. **21, 승인:** 범위가 벗어나 `range-invalid`가 추가된다. 승인했어도 `cancelled`이고
   숫자는 21로 유지된다.
4. **3, 승인 후 적용 단계에서 오류:** 승인 이전 node들은 완료됐고 `apply`가 실패한다.
   같은 thread에서 `graph.invoke(None, config=config)`로 **실패 지점부터 재실행**한다.

여기서 3번은 **승인과 검증이 서로 독립 조건**임을 보여 준다. 승인이라고 해서
필수 범위 검사를 건너뛸 수 없도록 분기 조건을 구성했다.

## 실제 실행과 관찰

저장소 root에서:

```bash
cd decks/ai-langgraph
uv sync --locked
uv run python textbook/integration/workflow.py
uv run python -m unittest discover -s tests -v
```

`pause:`에서 승인 요청에 전달된 숫자와 검사 결과를 보고,
`snapshot:`과 `next:`에서 중단 시점을 확인한다.
`approved:`와 `rejected:`의 최종 state를 비교한다.
`approval visits: 2`인 이유는 `interrupt()`가 포함된 node가 처음 시작할 때와
resume 시 각각 한 번 실행되기 때문이다.

이것은 `ask_approval` 이전에 끝난 `classify`나 check node도 두 번 실행된다는 뜻이 아니다.
상태가 어떻게 저장되는지 확인한 뒤 함수 재실행 범위를 설명하라.

## 고의적 오류 후 복구

`build_graph(trace, fail_first_apply=True)`로 graph를 만들면 `apply`가 **첫 실행에서만**
`RuntimeError("simulated apply failure")`를 발생시킨다. 이 동작은 코드에 넣은
fault injection으로, LangGraph의 내장 오류 주입 기능이 아니다.

[검증 코드](../../tests/test_integration.py)는 승인으로 `apply`에 도달한 후
예외가 발생하는지 확인하고, 그 시점의 checkpoint에서 `next=("apply",)`인지를 본다.
그다음 **같은 graph와 thread**에 `None`을 전달해 완료된 앞 단계 없이 `apply`만
다시 실행되는지 검증한다.

이때 관찰용 `trace`에는 `apply`가 **두 번** 남는다. 운영 환경의 실제
side effect가 같은 방식으로 중복될 수 있으므로 안전한 재실행에는 idempotency key나
중복 조정 절차가 필요하다. 현재 예제는 메모리에 문자열을 추가하고 숫자만 바꿀 뿐,
외부 DB·메일·결제는 수행하지 않는다.

오류 후 `invoke(None, ...)`와 승인 중단 후 `Command(resume=...)`는 서로
다른 복구 경로라는 점도 설명하라.

## 학습자 독립 평가

교본을 보지 않고 다음 중 한 가지 변경을 선택한다.

- `check_range` 조건을 `5 <= number <= 15`로 바꾸고, 입력 3·8·21의
  승인 후 결과를 예측하고 관찰한다.
- `choose_action`의 승인 조건을 제거하면 어떤 안전 조건이 깨지는지
  가장 작은 반례를 설계한다. 테스트를 고쳐 통과시키는 것이 아니라 **안전 조건을 복원**한다.
- `ask_approval` 앞에 관찰용 기록을 추가하고 재개 시 중복되는지 검증한다.
  어느 위치에 놓아야 재실행이 일어나지 않는지 이유와 함께 설명한다.

**평가 기준:** state key의 읽기·쓰기, 병렬 update와 reducer, checkpoint의 저장
경계, 중단 node 재실행, 승인·검증 분기, 실패 복구 경로를 코드 및 관찰 결과로
구분할 수 있어야 한다. 테스트 실행 성공만으로 이해했다고 판단하지 않는다.

## 참고

- [Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [State와 reducer](https://docs.langchain.com/oss/python/langgraph/graph-api-state)
- [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
