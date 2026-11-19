# 01. 메시지에서 도구 호출까지: Agent는 무엇을 실행하는가?

**학습 목표:** 모델의 요청, 실제 함수 실행, 실행 결과, 최종 응답을 서로 다른 사건으로 설명하고
`create_agent`가 이 사건들을 어떻게 연결하는지 실행 기록으로 검증한다.

선행 지식은 Python 함수와 `dict`, JSON, LLM 요청·응답의 기본 개념이다. LangGraph를 직접 구성하거나
유료 모델 API를 사용할 필요는 없다. 이 교본에서는 [실습 코드](../../playground/01-agent-loop/first_agent.py)를
읽고 실행하며, 결과보다 **그 결과가 만들어지는 순서**를 먼저 공부한다.

## 1. 왜 모델에 함수를 넘기는 것만으로 충분하지 않을까?

LLM은 텍스트를 예측한다. 도구를 지원하는 모델도 Python 함수를 직접 실행하지 않는다. 대신 도구의
이름과 입력 형식을 보고 **어떤 도구를 어떤 인자로 호출해 달라는 요청**을 응답으로 만든다. 요청을 받은
프로그램이 실제 함수를 실행하고, 그 결과를 다시 모델에 전달해야 한다.

단독 모델 호출과 Agent 실행을 구분하면 책임이 명확해진다.

| 주체 | 하는 일 | 하지 않는 일 |
| --- | --- | --- |
| Chat model | 메시지를 읽고 응답을 생성한다. 응답에 tool call이 들어갈 수 있다 | Python 함수를 직접 실행하지 않는다 |
| Tool | 정해진 인자를 받아 Python 코드를 실행하고 결과·예외를 만든다 | 다음 모델 호출을 스스로 결정하지 않는다 |
| `create_agent` | 모델 응답을 해석하고 필요하면 도구를 호출해 결과를 메시지로 전달한다 | 모델이 만든 모든 문장이 사실이라고 검증하지 않는다 |

예를 들어 사용자가 "7의 두 배"를 묻고 모델이 `double(value=7)`을 요청했다고 하자. 이 순간 계산값
`14`는 아직 없다. 프로그램이 `double(7)`을 실행해야만 결과가 생긴다. 모델이 결과를 읽고 "14"라고
답하는 것은 그보다 **나중** 사건이다.

## 2. 메시지가 실행 기록이 되는 방식

이번 실습에 필요한 세 메시지 타입은 다음과 같다.

- `HumanMessage`: 사용자가 보낸 입력.
- `AIMessage`: 모델이 생성한 내용. `content`뿐 아니라 `tool_calls`를 가질 수 있다.
- `ToolMessage`: 프로그램이 도구를 실행한 결과. `tool_call_id`로 원래 요청과 연결된다.

도구 호출 경로는 개념적으로 다음 순서를 따른다.

```text
HumanMessage("Double 7")
    → AIMessage(content="", tool_calls=[{name:"double", args:{value:7}, id:"call_double_1"}])
    → ToolMessage(content="14", tool_call_id="call_double_1")
    → AIMessage(content="The doubled value is 14.")
```

중요한 불변식은 **실행된 도구의 결과가 어떤 요청에 대한 응답인지 식별 가능해야 한다**는 것이다.
`ToolMessage.tool_call_id`와 대응되는 `AIMessage.tool_calls[*].id`를 비교한다. 실제 환경에서는
모델이 여러 tool call을 요청할 수도 있으므로 단순히 "직전 메시지가 결과"라고 가정하지 않는다.

또한 위 기록은 **한 번의 `agent.invoke`가 반환한 메시지 목록**이다. 다음 `invoke` 호출에서도 기록이
자동으로 유지된다는 뜻은 아니다. 여러 호출을 이어 기억하려면 별도의 persistence 구성이 필요하다.

## 3. 도구 계약: 이름과 schema가 왜 필요한가?

[실습 파일](../../playground/01-agent-loop/first_agent.py)의 `double`은 `@tool`로 노출된 Python 함수다.
그 함수의 docstring과 `value: int` 인자 타입은 모델에 전달할 도구 설명·인자 schema의 출발점이다.
모델이 반환하는 `ToolCall`은 실행 가능한 Python 코드를 제공하는 것이 아니라, 이름·인자·ID로 구성된
**데이터**다. 프로그램은 요청을 해석해 등록된 도구를 선택하고 입력을 검증한다.

`model-only` 시나리오는 모델이 tool call을 생성하는데도 실제 실행 횟수가 0임을 보여준다.
같은 scripted 응답을 `create_agent`에 전달한 `tool` 시나리오에서는 `double`이 1회 실행된다.

## 4. `create_agent`는 언제 멈추는가?

`create_agent(model, tools=[...])`는 모델과 도구의 실행을 연결한다. 핵심은 다음 두 분기다.

1. 모델이 일반 응답을 반환하면 도구를 실행하지 않고 종료한다. (`no-tool`)
2. 모델이 tool call을 반환하면 도구를 실행하고 결과를 모델에 전달한다. 이후 모델이 일반 응답을
   반환하면 종료한다. (`tool`)

단, 도구 실행이 실패하면 항상 정상적인 `ToolMessage`가 만들어지고 자동으로 재시도되는 것은 아니다.
이번 실습의 `double(-1)`은 의도적으로 `ValueError`를 발생시킨다. 처리하지 않은 예외는 호출자에게
전달되며, 실행 흔적의 마지막 정상 응답과 구분해야 한다. 운영상 재시도·오류 복구 정책은 별도로 설계한다.
모델이 계속 도구를 요청하는 경우에는 실행 단계 제한 같은 별도 종료 제어도 필요하다.

## 5. 실습: 예측하고 실행 기록으로 확인하기

처음 한 번만 다음 명령으로 LangChain 의존성을 설치하면서 실행한다. 설치된 Python 3.11 이상과 `uv`가
필요하며, 외부 API key는 필요 없다. 프로젝트 의존성의 직접 버전은 `pyproject.toml`에 고정되어 있다.

```bash
uv run --project decks/ai-langchain --no-lock python \
  decks/ai-langchain/playground/01-agent-loop/first_agent.py --scenario model-only
uv run --project decks/ai-langchain --no-lock python \
  decks/ai-langchain/playground/01-agent-loop/first_agent.py --scenario no-tool
uv run --project decks/ai-langchain --no-lock python \
  decks/ai-langchain/playground/01-agent-loop/first_agent.py --scenario tool
uv run --project decks/ai-langchain --no-lock python \
  decks/ai-langchain/playground/01-agent-loop/first_agent.py --scenario error
```

실행 **전**에 다음을 기록한다: `AIMessage`/`ToolMessage` 등장 순서, `tool_executions` 값,
`call_double_1`의 등장 위치, 오류 상황에서 최종 `AIMessage`를 얻을 수 있는지.

실행 후 `tool`의 기록에서 `AIMessage.tool_calls[0].id`와 `ToolMessage.tool_call_id`가 같은지 확인한다.
`model-only`는 동일한 도구 요청이 **실행되지 않는** 대조군이다. `no-tool`은 도구가 등록되어도 호출
요청이 없으면 실행되지 않는 반례다. `error`는 호출 횟수가 1인데도 정상 최종 응답은 없는 사례다.

아래 명령은 도구 실행 횟수, 메시지 순서, ID 대응, 예외의 전파를 실제 LangChain 실행으로 검사한다.

```bash
uv run --project decks/ai-langchain --no-lock python \
  decks/ai-langchain/playground/01-agent-loop/test_first_agent.py
```

**검증의 한계:** `ScriptedToolModel`은 실제 LLM이 아니다. 테스트용 응답 두 개를 사전에 정했고, 마지막
문장의 "14"는 도구 결과를 읽어서 추론한 것이 아니라 미리 적힌 텍스트다. 따라서 테스트 통과는
**Agent의 연결·제어 흐름이 동작한다**는 증거이지, 실제 모델이 올바른 결정을 내린다는 증거는 아니다.
실제 provider는 별도 인증·요금·비결정성과 실행 정책을 수반하므로 이번 무키(no-key) 실습에 섞지 않는다.

## 6. 이해도를 확인하는 연습

코드를 바로 바꾸기 전에 답을 예측하고 근거를 말한다.

1. `tool` 시나리오에서 첫 `AIMessage`를 이미 받았다고 하자. 여기에서 `double`을 제거하고 모델만
   직접 호출하면 `14`라는 도구 결과가 만들어질까? `AIMessage`와 `ToolMessage`의 차이로 설명하라.
2. `tool` 시나리오의 call ID를 `call_second`로 바꾸되 **요청 ID만** 변경한다면 어떤 메시지도 함께
   바뀌어야 하는가? 실제 코드를 수정하고 실행 기록으로 확인하라.
3. `double(-1)`의 오류를 `try/except`로 처리해 문자열을 반환하도록 바꾸면, 오류가 전달되는 방식과
   학습자가 관찰하는 증거가 어떻게 달라지는가? 오류를 문자열로 숨기는 설계의 단점을 설명하라.
4. 새로운 함수 `triple(value: int)`를 추가할 경우 모델이 `triple`을 요청하더라도 실제 실행이
   가능하려면 어떤 등록 작업과 검증이 필요한가? 두 분기의 메시지 흐름을 비교하라.

**힌트:** (2)는 `ToolMessage`를 직접 만들기보다 agent가 생성하게 두고 출력 ID를 비교한다.
(3)은 도구가 `"error"`라는 정상 문자열을 반환한 상태와 실제 Python 예외가 발생한 상태의 의미를
분리한다. (4)는 도구 함수의 존재와 agent에 등록된 도구 목록이 다른 개념이라는 점에서 출발한다.

**체크포인트:** 다른 숫자와 새 call ID를 사용해도 도구 실행 1회, 요청↔결과 ID 일치, 도구 없는 경로
실행 0회, 처리하지 않은 예외의 전파라는 특성을 스스로 설명하고 확인할 수 있어야 한다. 실행 결과를
단순히 복사하는 것은 충분하지 않다.

## 근거

- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Messages](https://docs.langchain.com/oss/python/langchain/messages)
- [LangChain Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [LangChain Unit testing](https://docs.langchain.com/oss/python/langchain/test/unit-testing)
