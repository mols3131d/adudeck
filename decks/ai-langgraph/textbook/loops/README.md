# 2. 조건 분기에서 반복과 종료까지: graph의 loop 추적

앞 단위는 홀짝에 따라 한 갈래를 고른 뒤 `END`로 향했다. 실제 workflow에서는
조건을 충족할 때까지 같은 작업을 여러 번 수행할 수 있다. 핵심은 Python의 `while`
문을 graph로 바꾸어 외우는 것이 아니라 **한 번 실행한 node가 state를 갱신하고,
그 결과로 다음 node를 선택한다**는 순서를 이해하는 것이다.

실습은 [counter_loop.py](counter_loop.py) 한 파일로 실행한다. 입력 숫자를 2씩 늘려
목표값 이상이 되면 종료한다. API 호출이나 외부 파일 기록은 없다.

## 1. 상태와 제어 흐름은 다른 역할이다

`value=1`, `target=6`에서 시작한다. state에는 실제 수와 목표 외에도
`checks`와 `advances`라는 관찰용 정수가 있다.

```text
START → check ──(value >= target)──→ END
          │
          └──(value < target)──→ advance
                                    │
                                    └──→ check
```

- `check` node는 `checks`만 1 증가시켜 **몇 번 검사했는지** 기록한다.
- 조건부 edge의 `choose_next`는 `value >= target`일 때 `done`,
  그렇지 않으면 `again`을 반환한다. 이 함수는 state를 변경하지 않는다.
- `advance` node는 `value`에 2를 더하고 `advances`를 1 늘린다.
- `advance → check`라는 일반 edge가 **같은 node로 되돌아가는 경로**다.

`builder.add_conditional_edges("check", choose_next, {"again": "advance", "done": END})`를
사용한다. `choose_next`의 `again`·`done`은 애플리케이션이 정한 경로 label이며,
이를 실제 node인 `advance` 및 종료점 `END`에 매핑한다.
`END`는 오류가 아니라 모든 작업을 마치고 정상 종료하는 지점이다.

## 2. 왜 1부터 시작하면 결과가 7인가?

이번 문제의 종료 조건은 **같다(`==`)**가 아니라 **이상이다(`>=`)**.
따라서 1, 3, 5, 7의 순서로 값이 변한다. 6에 정확히 닿을 필요가 없다.

| Super-step의 node | 반환 update | 적용 후 값 | 다음 경로 |
| --- | --- | --- | --- |
| `check` | `checks=1` | `value=1` | `advance` |
| `advance` | `value=3, advances=1` | `value=3` | `check` |
| `check` | `checks=2` | `value=3` | `advance` |
| `advance` | `value=5, advances=2` | `value=5` | `check` |
| `check` | `checks=3` | `value=5` | `advance` |
| `advance` | `value=7, advances=3` | `value=7` | `check` |
| `check` | `checks=4` | `value=7` | `END` |

최종 state는 `value=7, target=6, checks=4, advances=3`이다.
**완료된 실행**에서 `checks = advances + 1`이다.
이는 목표를 이미 넘었더라도 마지막 `check`는 실행되고 `advance`는 선택되지
않기 때문이다. 실행 중간에는 아직 종료 확인이 없을 수 있으므로 모든 시점에
이 수식이 성립한다고 주장하면 안 된다.

노드가 반환하지 않은 `target`은 보존된다. Graph가 반복한다고 해서
파이썬 함수를 재귀적으로 직접 호출하거나 node 함수가 전체 state를
다시 만들어야 하는 것도 아니다. 다음 실행은 edge가 예약한다.

## 3. 실행 전에 예측하고 중간 update 관찰하기

```bash
cd decks/ai-langgraph
uv run --locked python textbook/loops/counter_loop.py
```

`update:` 행은 `stream_mode="updates"`의 **node별 partial update**다.
`check`와 `advance`가 몇 번 나타나는지, `target`이 update에
없는지 먼저 예측하고 비교한다. 예제는 이어서 `invoke`로 같은 초기 입력을
**다시 실행**해 최종 state를 출력한다. 현재 node는 메모리상의 순수 계산이라
재실행이 안전하지만, 실제 외부 쓰기 node라면 이 호출도 부작용을 반복한다.

조건을 바꾼 두 가지 경우를 따로 생각한다.

- **이미 도달한 값:** `initial_state(8, 6)`은 `check`를 한 번 실행하지만
  `advance`는 실행하지 않는다. 최종 `checks=1, advances=0`.
- **정확히 목표값:** `initial_state(6, 6)`도 마찬가지다.
  검사 node가 `END`를 선택한 결과와 node 실행을 생략한 결과는 같지 않다.

## 4. 종료가 잘못되었을 때의 방어선

`choose_next`에서 `>=`를 `==`로 바꿔 `initial_state(1, 6)`을
실행하면 어떻게 될까? 1에서 2씩 증가한 값은 계속 홀수이므로
6에 도달하지 않는다. **끝없이 이어지는 경로가 생겼다**는 것이 문제다.

LangGraph의 `recursion_limit`은 한 실행이 허용하는 **super-step 수**를 제한한다.
파이썬 함수의 재귀 깊이나 `advance` 호출 횟수만 세는 것이 아니다.
예제는 정상 종료하기에 너무 작은 limit를 지정한 또 다른 실행을 수행해
`GraphRecursionError`를 고의로 관찰한다.

```python
graph.invoke(initial_state(1, 100), config={"recursion_limit": 4})
```

한계를 넘으면 **정상적인 완료 state가 반환되지 않고 예외가 발생**한다.
limit을 늘리는 것으로 잘못된 종료 조건을 해결했다고 주장해서는 안 된다.
먼저 종료를 가능하게 하는 단조로운 변화(`value += 2`)와 판정 조건(`>= target`)을
서로 비교해야 한다.

이 실습의 예외 처리 범위는 `GraphRecursionError`뿐이다. 다른 실패를
정상 종료처럼 숨기지 않는다.

## 5. 학습자 과제

1. `initial_state(0, 5)`의 node 호출 순서, 최종 `checks`, `advances`,
   `value`를 직접 계산한 다음 실행으로 확인한다.
2. `advance`를 `value -= 2`로 바꾸고 `initial_state(1, 6)`을
   실행한다. 어떤 상태 불변식이 깨지고 왜 종료되지 않는가? 임시로 작은
   `recursion_limit`을 전달해 실행을 통제한다.
3. `advance`가 `advances`를 기록하지 않도록 고치면 결과값의
   최종값은 유지될 수 있지만 **어떤 관찰 증거**가 사라지는가?
4. 이전 단위의 한 번뿐인 홀짝 조건 분기와 이번 `check → advance → check`
   경로를 비교한다. 둘 다 조건부 edge를 사용하지만 언제 loop가 되는가?

**이해 확인:** 실행하기 전 각 super-step의 state update와 다음 경로를
설명하고, 잘못된 종료 조건의 최소 반례를 구성하며,
`GraphRecursionError`가 어떤 상태에서 발생하는지 재현하면 이 단위를 통과한다.

## 공식 자료

- [조건부 edge와 loop](https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow)
- [Graph API: super-step과 recursion limit](https://docs.langchain.com/oss/python/langgraph/graph-api)
