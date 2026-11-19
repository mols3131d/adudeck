# 03. Structured output: 텍스트가 유효한 데이터가 되는 조건

첫 단원의 agent는 `"The doubled value is 14."`라는 문자열을 돌려줬다. 사람이 읽기에는 충분해도,
프로그램은 그 문장에서 값과 오류를 안정적으로 구분하기 어렵다. 이 단원에서는 모델이 구조화된 값을
요청하게 하고, LangChain이 **schema를 검증한 결과**와 실패 시 **재시도 경로**를 직접 관찰한다.

[실행 코드](../../playground/03-structured-output/structured_response.py)와
[테스트](../../playground/03-structured-output/test_structured_response.py)는 모두 고정된 fake model
응답을 사용한다. 실제 provider 계정이나 API key는 필요 없다.

## 1. 구조가 맞는 것과 의미가 맞는 것은 다른 문제다

`Rating`은 `score: int`와 `reason: str`을 정의하는 Pydantic 모델이다. `score`에 `ge=1`,
`le=5`라는 제약을 추가했으므로 `score=9`는 거부된다. 이는 단순히 JSON 형태가 유효한지만
보는 것보다 강한 검증이다. 반면 `score=4`가 실제 제품을 올바르게 평가한 값인지는 **schema로
검증할 수 없다**. 데이터 형태와 사실·품질을 따로 평가해야 한다.

`create_agent(..., response_format=ToolStrategy(Rating))`는 모델의 응답을 schema에 맞춰
구조화하도록 요청한다. 유효한 값은 `state["structured_response"]`에서 Pydantic 객체로 얻는다.
`ToolStrategy`는 provider-native JSON 모드와 다른 도구 호출 기반 전략이다. 이 실습에서는
실제 모델의 provider 지원과 무관하게 검증 메커니즘을 관찰하기 위해 `ToolStrategy`를 명시한다.

## 2. 예측할 세 가지 경로

| 실행 | 첫 모델 요청 | 처리 | 관찰 대상 |
| --- | --- | --- | --- |
| `valid` | `Rating(score=4)` | schema를 통과 | `structured_response.score == 4` |
| `repair` | `Rating(score=9)` | 오류 피드백을 모델에 돌려줌 | 두 번째 요청에서 `score=4`로 수정 |
| `reject` | `Rating(score=9)` | 재시도하지 않음 | 예외가 호출자에게 전파 |

**주의:** `repair`의 두 번째 응답은 테스트가 미리 준비한 값이다. LangChain이 피드백 메시지를
되돌려주는 것은 실습으로 확인할 수 있지만, 실제 모델이 언제나 피드백을 이해해 올바른 값을
반환한다고 보장할 수는 없다.

정상 응답에서도 tool call은 실제 비즈니스 함수의 실행 요청과 다르다. 이 실습의 `Rating`은
구조화된 값을 만들기 위한 **형식 도구**다. 첫 단원의 `double`처럼 숫자를 계산하는 함수가 아니며,
그것을 실행한 효과가 있다고 설명하면 안 된다.

## 3. 실패를 숨기지 않고 읽는 법

`ToolStrategy(..., handle_errors=True)`에서는 출력 schema가 맞지 않을 때 검증 오류를
피드백 `ToolMessage`로 전달하고 모델에 다시 시도할 기회를 준다. 이를 기본적인 **복구 경로**로
부를 수 있지만, 비용·호출 횟수·실패 횟수 제한을 직접 검토하지 않고 무조건 재시도 정책으로
쓰면 안 된다.

`handle_errors=False`이면 같은 잘못된 출력에서 `StructuredOutputValidationError`가 전파된다.
이렇게 실패를 표면으로 드러내면 호출자가 기록하거나 중단 조건을 선택할 수 있다. 실패를
`{"score": 0}` 같은 성공 모양의 값으로 바꾸면 어떤 문제가 있었는지 잃어버리기 쉽다.

개념적으로 정상 값과 오류의 흐름은 다음과 같다.

```text
HumanMessage
  → AIMessage(tool_calls=[Rating(score=9), id=rating_invalid])
  → ToolMessage(tool_call_id=rating_invalid, validation feedback)
  → AIMessage(tool_calls=[Rating(score=4), id=rating_repaired])
  → ToolMessage(tool_call_id=rating_repaired, accepted)
  → state["structured_response"] = Rating(score=4, ...)
```

ID를 확인하면 어떤 요청이 검증 오류를 냈고 어떤 요청이 최종 값으로 받아들여졌는지 연결할 수 있다.

## 4. 실제 실행과 재검증

실행 전에 각 시나리오의 **모델 응답 횟수**, **검증 피드백 개수**, **최종 구조화된 값 또는 예외**
세 가지를 먼저 예측한다.

```bash
uv run --no-project --with langchain==1.5.2 python decks/ai-langchain/playground/03-structured-output/structured_response.py --scenario valid
uv run --no-project --with langchain==1.5.2 python decks/ai-langchain/playground/03-structured-output/structured_response.py --scenario repair
uv run --no-project --with langchain==1.5.2 python decks/ai-langchain/playground/03-structured-output/structured_response.py --scenario reject
uv run --no-project --with langchain==1.5.2 python decks/ai-langchain/playground/03-structured-output/test_structured_response.py
```

테스트는 Pydantic 경계 검증뿐 아니라 실제 `create_agent` 실행 결과에서
`structured_response`, 요청 ID, 검증 메시지 순서, 예외 전파를 확인한다.
문법 검사나 Pydantic만 직접 호출하는 테스트는 agent가 올바르게 이어졌다는 증거가 될 수 없다.

## 5. 학습자가 직접 해결할 과제

1. `score`의 범위를 `0..10`으로 변경한다면 기존의 `repair` 테스트가 왜 다른 결과를
   내야 하는가? schema와 재시도 조건을 연결해 설명하라.
2. `reason`을 빈 문자열로 바꿔 테스트하라. 값의 타입은 맞는데도 왜 거부되는가?
3. `repair`의 두 번째 모델 응답까지 잘못된 값으로 바꾸면 어떤 위험이 생기는가? 단순히
   무한히 재시도하게 두는 것보다 어떤 종료 정책이 필요한지 제안하라.
4. `ProviderStrategy`로 바꾸려면 무엇을 확인해야 하는가? 실제 모델과 제공자가 native
   structured output을 지원하는지, 도구와 동시에 사용 가능한지 구분하라.
5. JSON schema 통과가 잘못된 계산이나 환각을 막는다는 주장에 반례를 하나 제시하라.

**평가 기준:** 구조 검증과 의미 검증을 구분하며, 실패 경로에서 어떤 메시지가 어떤 요청에 연결되는지
추적하고, 재시도/예외 전파를 호출자의 신뢰성 요구에 맞춰 선택할 수 있어야 한다.

## 공식 근거

- [Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [Unit testing](https://docs.langchain.com/oss/python/langchain/test/unit-testing)
