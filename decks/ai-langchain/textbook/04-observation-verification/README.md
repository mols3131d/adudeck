# 04. 실행을 증명하는 방법: stream, failure, test

앞선 단원은 `agent.invoke`가 반환한 최종 메시지를 살펴봤다. 하지만 최종 메시지 하나로는
**도구가 정말 실행됐는지**, **어느 단계에서 실패했는지**, **오류가 복구됐는지**를 충분히
알기 어렵다. 이번 단원에서는 같은 `create_agent`를 `stream_mode="updates"`로 실행하고
단계별 산출물을 검증한다.

[관찰 실습](../../playground/04-observation-verification/trace_and_recovery.py)과
[실행 테스트](../../playground/04-observation-verification/test_trace_and_recovery.py)를 사용한다.

## 1. 최종 응답과 실행 증거는 무엇이 다른가?

정상적인 `agent.invoke`는 결과 `state`를 반환한다. 반면 `agent.stream(..., stream_mode="updates")`
는 **모델 노드와 도구 노드에서 상태가 갱신될 때마다** 업데이트를 전달한다. 모델이 tool call을
생성한 시점과 실제 도구가 값을 반환한 시점의 차이를 조사할 수 있다.

```python
events = list(
    agent.stream(
        {"messages": [HumanMessage(content="Double 7.")]},
        stream_mode="updates",
    )
)
```

이번 실습의 정상 실행에서 흐름은 다음과 같다.

```text
model → AIMessage(tool_calls=[{id: "call_double_1", ...}])
tools → ToolMessage(tool_call_id="call_double_1", content="14")
model → AIMessage(content="The doubled value is 14.")
```

이것은 한 번의 실행을 기록한 **실습용 local observation**이다. 네트워크 전체를 포괄하는
distributed trace나 실제 provider 토큰 사용량은 아니다. 서로 다른 증거 수준을 구분해야 한다.

최종 문장이 `"14"`여도 그 값이 도구로부터 만들어졌다는 보장은 없다. 따라서 최종 응답만
비교하는 테스트는 통과하면서도 도구 호출이 전혀 안 되는 버그를 놓칠 수 있다. 도구 실행 횟수,
요청 ID와 결과 ID의 일치, 노드 순서까지 검사하는 이유다.

## 2. 오류를 전파할지 메시지로 바꿀지

첫 교본의 `double(-1)`은 `ValueError`를 던진다. 별도 처리하지 않으면
`agent.invoke` 호출자에게 오류가 전파된다. 이는 분명한 **실패 상태**이며, 최종 답변을
성공처럼 포장하지 않는다.

이번 단원의 두 번째 경로는 `@wrap_tool_call` middleware를 적용한다.
middleware는 `handler(request)`를 실행하고, 특정 `ValueError`가 발생한 경우에만
`ToolMessage(status="error", tool_call_id=...)`를 반환한다. 따라서 도구 실행 실패라는 사실은
남고, 모델은 그 오류를 보고 **정상 계산을 할 수 없다는 내용**으로 응답할 수 있다. 반환 타입
주석에 보이는 `Command`는 `create_agent`가 LangGraph runtime 위에서 동작하기 때문에
`langgraph.types`에서 가져온 타입이다.

```python
@wrap_tool_call
def report_failure(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    try:
        return handler(request)
    except ValueError as exc:
        return ToolMessage(
            content=f"tool failed: {exc}",
            tool_call_id=request.tool_call["id"],
            status="error",
        )
```

중요한 차이는 다음과 같다.

| 구분 | middleware 없음 | middleware 있음 |
| --- | --- | --- |
| 도구 함수 호출 | 1회 | 1회 |
| 함수에서 발생한 오류 | `ValueError` | `ValueError` |
| 호출자에게 보이는 형태 | Python 예외 전파 | `status="error"`인 `ToolMessage` |
| 이후 모델 호출 | 이루어지지 않음 | 이루어짐 |
| 결과 의미 | 실행 실패 | 실패가 복구된 것이 아니라 **오류를 보고한 응답** |

예외를 평범한 `"success"` 문자열로 바꾸면 호출자는 실패를 감지하기 어렵다. 이번 예시는
`ToolMessage.status`를 명시적으로 `error`로 두어 실패를 성공으로 오인하지 않게 한다.
다만 어떤 예외를 보고하거나 재시도할지는 시스템의 정책과 부작용에 따라 달라진다. 외부 결제나
쓰기 작업을 동일하게 다시 실행하는 식의 재시도는 별도 idempotency 검토 없이 적용하면 안 된다.

## 3. 예측, 실행, 재검증

실행 전에는 `stream`이 어느 순서로 어떤 노드 이름을 보여줄지, 실패 후 정상 응답을
받는 것과 도구 호출이 성공한 것이 왜 다른지 예상한다.

```bash
uv run --project decks/ai-langchain --locked python decks/ai-langchain/playground/04-observation-verification/trace_and_recovery.py
uv run --project decks/ai-langchain --locked python decks/ai-langchain/playground/04-observation-verification/test_trace_and_recovery.py
```

관찰 결과가 예측과 다르면 단순히 테스트를 완화하지 말고 **어느 단계의 상태를 잘못 이해했는지**
판단한다. 모델 출력이 미리 고정된 fake라는 점도 함께 고려한다. 테스트는 LangChain의 제어 흐름과
우리가 정의한 오류 정책을 검증하지만, 실제 LLM이 도구를 선택하는 판단이나 생성된 답의 사실성을
평가하지 않는다.

### 검증 경계

- **Unit/runtime:** API key 없는 fake model과 실제 `create_agent`의 제어 흐름을 검증한다.
- **Integration:** 실제 provider와 도구 시스템을 연결했다면 네트워크 요청·인증·비용·timeout과
  비결정적인 모델 응답을 별도로 측정해야 한다.
- **Evaluation:** 모델 답변이 질문에 맞는지와 도구를 쓸 필요가 있었는지 자체를 평가하려면
  별도의 평가 데이터·기대 속성·실패 분류가 필요하다. 단순 unit test를 평가 점수로 간주하지 않는다.

실제 모델과 연결할 때는 데이터에 비밀정보가 섞이지 않도록 trace와 message 기록을 제한하고,
외부 호출이 있는 테스트와 무키(unit) 테스트를 분리한다.

## 4. 독립 연습

1. `stream_success`의 도구 실행을 두 번 일으키도록 fake 응답을 수정한다. 한 `AIMessage`에
   두 `tool_calls`를 넣는 경우와 두 턴에 나누어 호출하는 경우의 모델/도구 노드 순서를
   **실행 전에 예상**하고, 각 tool call ID와 결과 ID가 일치하는지 검사하라.
2. `report_failure`에서 `ValueError` 대신 모든 `Exception`을 가로채게 하면 어떤 문제가
   생기는가? 설정 오류나 프로그래밍 오류가 **정상 실행인 것처럼** 처리될 위험을 설명하라.
3. `ToolMessage`를 만들면서 `tool_call_id`를 잘못 기록하면 어떻게 진단할 수 있는가?
   요청-결과 매칭 invariant를 기준으로 검사를 작성하라.
4. 기존 테스트가 전부 통과해도 fake 모델의 최종 응답에 잘못된 값을 적으면 왜 의미 검증은
   실패할 수 있는가? 검증 범위별로 어느 assertion을 추가해야 하는지 분리하라.
5. API key를 사용해 실습을 확장한다면 어떤 테스트는 반복 가능하고 어떤 테스트는 그렇지
   않은가? 실패 복구 과정의 비용과 부작용까지 고려해 경계를 작성하라.

**평가 기준:** 결과만 보고 결론을 추측하지 않고, node update·메시지·함수 호출 횟수를
같은 실행 사건으로 연결한다. 실패를 숨기지 않으면서 복구 경로를 설명하며, 테스트의
검증 수준과 아직 검증되지 않은 범위를 구분할 수 있어야 한다.

## 5. 누적 통합 점검 (01~04장 종합)

01~04장을 모두 마친 뒤, 다음 가상 실행 기록만으로 원인과 책임 계층을 진단한다.

> `InMemorySaver` checkpointer, `RunContext(label=...)`, `double` 도구, `@wrap_tool_call` 오류
> 변환 middleware, `ToolStrategy(Rating, handle_errors=True)`를 함께 연결한 agent를 같은
> `thread-a`에 두 번 호출했다. 두 번째 호출에서 최종 `state["structured_response"]`는
> `Rating(score=5, reason="ok")`로 반환되었지만, 스트림 기록에는 `double(-1)`에 대한
> `ToolMessage(status="error")`가 남아 있다.

코드를 보지 않고 아래 네 질문에 근거와 함께 답한다.

1. **도구 실행 vs 구조화 검증:** `structured_response`가 유효한 `Rating` 객체라는 사실이
   `double` 도구 실행 성공을 증명하는가? `ToolMessage.status`와 `structured_response`의
   책임 차이를 설명하라.
2. **상태 수명:** 두 번째 호출의 `state["messages"]`에 첫 호출 메시지와 두 번째 호출의 오류
   `ToolMessage`가 함께 남아 있을 때, `RunContext.label`도 첫 호출 값이 유지되는가?
3. **오류 정책 선택:** 만약 `double(-1)` 실패 시 구조화된 최종 응답 자체를 만들지 않고
   호출자에게 실패를 알려야 한다면, `@wrap_tool_call`과 `handle_errors` 중 어느 경계를
   어떻게 바꿔야 하는가?
4. **테스트 설계:** 이 회귀를 막는 무키(unit) 테스트에 넣어야 할 최소 assertion 3가지를
   적고, 그 테스트가 여전히 검증하지 못하는 항목 1가지를 명시하라.

**통과 기준:** (1) schema 통과와 도구 실행 성공·사실성을 분리하고, (2) thread state와
per-invocation context의 수명을 구별하며, (3) 오류 전파/변환 경계를 정책에 맞게 선택하고,
(4) fake 단위 테스트의 검증 한계를 함께 서술해야 한다.

## 공식 근거

- [Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [Custom middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom)
- [Unit testing](https://docs.langchain.com/oss/python/langchain/test/unit-testing)
