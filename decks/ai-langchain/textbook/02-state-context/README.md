# 02. 상태가 남는 곳과 사라지는 곳: state, context, middleware

이 단원에서는 첫 교본에서 본 단일 `invoke`를 **두 번 호출**한다. 첫 호출의 메시지가 다음 호출에
남는지, 다른 대화의 기록과 섞이는지, 실행마다 전달하는 값이 어디에 나타나는지 실험한다.
[실행 파일](../../playground/02-state-context/state_context.py)과
[검증 파일](../../playground/02-state-context/test_state_context.py)을 함께 사용한다.

## 1. 입력에 메시지를 다시 넣었는데 왜 이전 대화를 기억하지 못할까?

첫 단원에서 `state["messages"]`는 실행을 마친 뒤 반환한 **그 실행의 결과**였다. 이것만으로 다음
호출을 기억하지 않는다. 호출 A의 리스트를 호출 B에 직접 다시 넘기거나, agent에 별도의
checkpointer를 제공해야 한다. 두 방식은 프로그램의 책임이 다르다.

`InMemorySaver`는 thread별 상태를 **현재 프로세스의 메모리**에 기록하는 checkpointer다. 교육용으로
쓰면 파일이나 데이터베이스 없이 여러 번의 `invoke`가 어떻게 이어지는지 관찰하기 쉽다. 다만 프로세스를
종료하면 내용이 사라지므로 영구 저장소가 아니며, 실제 서비스에서 내구성을 보장하는 저장 수단도 아니다.

이번 실험은 `thread-a`에 두 번, `thread-b`에 한 번 호출한다. 같은 thread에서는 메시지가 누적되고
다른 thread는 독립적이다. 여기서 `thread_id`는 사용자의 ID나 인증 정보가 아니라 checkpointer의
대화 구분 키다.

> **왜 코드에 `langgraph.*` import가 보일까?**
> LangChain v1의 `create_agent`는 내부적으로 LangGraph runtime 위에서 실행된다. 그래서
> `InMemorySaver`와 `Runtime` 타입은 `langgraph` 패키지에서 가져온다. 이는 `create_agent`의
> checkpointer·runtime 인터페이스를 사용하는 것이며, LangGraph `StateGraph`를 직접 설계하는 작업과는
> 별개다.

## 2. state와 runtime context는 무엇이 다른가?

LangChain의 `state`는 모델과 도구 실행이 진행되는 동안 저장·갱신되는 정보다. 기본적으로
`messages`가 대표적이며, checkpointer가 있으면 같은 thread의 다음 호출에서 읽어올 수 있다.
`messages` 필드는 단순 대입(덮어쓰기)이 아니라 기존 기록 뒤에 새 메시지를 이어 붙이는 **message
reducer**(병합 규칙)로 갱신된다. 그래서 두 번째 호출에 새 `HumanMessage` 하나만 넘겨도 이전
`HumanMessage`·`AIMessage` 뒤에 누적된다.

`context`는 **이번 `invoke`에만 주는 실행 설정/데이터**다. 예를 들면 테넌트 구분, 리소스 이름,
설정 플래그와 같은 값이다. `context_schema`로 구조를 선언한 뒤 호출자는 `context=RunContext(...)`
형태로 전달한다. middleware는 `runtime.context.label`로 읽는다. 이것은 메시지 history에 append되지
않으며, checkpointer에 저장되는 state와 동일시해서는 안 된다.

핵심 구성은 다음과 같다.

```python
@dataclass
class RunContext:
    label: str

@before_model
def observe_input(state: AgentState, runtime: Runtime[RunContext]) -> None:
    observations.append(("before", runtime.context.label, len(state["messages"])))

agent = create_agent(
    model=model,
    tools=[],
    checkpointer=InMemorySaver(),
    context_schema=RunContext,
    middleware=[observe_input, observe_output],
)
```

실행 순서와 예상되는 관찰 값은 다음과 같다.

| 호출 | thread | context.label | 모델 호출 전 메시지 수 | 모델 호출 후 수 |
| --- | --- | --- | --- | --- |
| 1 | thread-a | run-1 | 1 | 2 |
| 2 | thread-a | run-2 | 3 | 4 |
| 3 | thread-b | run-3 | 1 | 2 |

두 번째 호출에 `run-2`라는 context를 주더라도 첫 번째 호출의 `run-1`이 두 번째 호출의
runtime context로 남지 않는다. 반대로 메시지는 두 번의 호출에서 누적되어 4개가 된다. 서로 다른
수명(lifetime)을 가진 값이므로 저장 위치와 소유 책임을 함께 생각해야 한다.

## 3. middleware는 데이터를 어디에서 관찰하는가?

`create_agent`는 model과 tools를 반복 호출한다. middleware는 그 과정의 특정 지점에 실행 로직을
추가한다. 이 실습에서는 두 개의 **node-style hook**만 사용한다.

- `@before_model`: 모델을 호출하기 전 현재 state와 runtime context를 관찰한다.
- `@after_model`: 모델 응답이 state에 반영된 뒤 같은 thread의 메시지 수를 관찰한다.

두 hook은 `None`을 반환하므로 상태를 바꾸지 않는다. 여기서는 `observations`라는 로컬 리스트에
작은 이벤트만 수집한다. 실제 시스템의 로그/trace 연동이나 예외 복구와 달리, 이는 작동 순서를
가르치기 위한 관찰 장치다. 모델 호출이 실패하면 `after_model`까지 실행된다고 가정하면 안 된다.

node-style hook은 state update dict(예: `{"messages": [...]}`)를 반환해 상태를 갱신할 수도 있다.
이때 반환한 dict는 해당 필드의 reducer(예: `messages`의 append 규칙)를 거쳐 state에 병합된다.
반면 `wrap_model_call`은 호출을 감싸며 처리/재시도/모델 교체에 개입한다. 단순 상태 관찰, state
갱신, 재시도 같은 **부작용**을 같은 동작으로 혼동하지 말아야 한다.

## 4. 예측 → 실행 → 해석

다음 명령은 단일 프로세스에서 committed lockfile로 실습한다. 외부 모델을 호출하지 않는다.

```bash
uv run --project decks/ai-langchain --locked python decks/ai-langchain/playground/02-state-context/state_context.py
uv run --project decks/ai-langchain --locked python decks/ai-langchain/playground/02-state-context/test_state_context.py
```

실행 전에 **(a) 세 호출의 메시지 개수, (b) 앞/뒤 hook의 개수, (c) 세 번째 호출에 첫 thread의
메시지가 남아 있는지**를 직접 적는다. 실행 후 이벤트의 `label`과 `history_length`를
함께 본다. 단순히 최종 응답이 출력되는지만 확인하지 않는다.

이 실습의 `GenericFakeChatModel`은 `response-1`, `response-2`, `response-3`을 순서대로
반환한다. 따라서 응답 내용의 정확성을 시험하는 것이 아니다. checkpointer가 어떤 메시지를
되살렸는지와 hook이 실제로 어느 시점에 호출됐는지를 확인한다.

## 5. 연습과 평가

1. 세 번째 호출에서 `thread-b`를 `thread-a`로 바꾸고 실행하라. 변경 전후의 메시지 개수를
   예상하고, 왜 세 번째 호출만 변해야 하는지 설명하라.
2. 호출 순서를 바꾸되 `thread_id` 관계는 유지해라. `run-2`가 첫 번째로 들어가도 label이
   저장된 state처럼 남는가? **모델의 fake 응답 순서**와 thread의 **메시지 누적**을 구분하라.
3. `@before_model`이 `None` 대신 잘못된 state update를 반환하도록 바꾼다면, 지금처럼
   관찰만 하는 것과 어떤 위험이 달라지는가? 특히 메시지 reducer를 모르고 임의로 바꿀 때의
   결과를 설명하라.
4. 이 코드를 프로세스 두 개로 나누어 각각 실행한다면 왜 in-memory checkpointer로는 공유 대화를
   보장할 수 없는가? 어떤 저장 보장이 필요한지 제안하라.

**평가 기준:** state와 context의 소유자·수명·식별자를 구분하고, 각 호출에서 모델이 실제로 읽는
history를 예측하며, 다른 thread로 정보가 섞이지 않는 이유를 설명할 수 있어야 한다.
답이 맞아도 단순히 출력 숫자를 외웠다면 통과로 보지 않는다.

## 공식 근거

- [Agents — runtime context](https://docs.langchain.com/oss/python/langchain/agents)
- [Short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory)
- [Custom middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom)
