# 5. Function Calling: model proposal과 application execution

Function Calling에서 model이 만드는 것은 실행 결과가 아니라 **실행 요청**이다.

```text
function_call
- name
- arguments
- call_id
```

실제 Python function 실행은 application이 한다.

## 5.1 한 번의 tool loop를 그대로 읽는다

먼저 실행한다.

```bash
uv run textbook/05-function-calling/function_calling.py
```

이번 playground는 하나의 read-only tool만 사용한다.

```python
def lookup_order(order_id: str) -> dict:
    ...
```

그리고 model에게 이 function의 interface를 설명하는 schema를 보낸다.

```python
LOOKUP_ORDER_TOOL = {
    "type": "function",
    "name": "lookup_order",
    ...
}
```

Python function body가 API server로 upload되는 것은 아니다.

## 5.2 첫 Response는 proposal을 담는다

첫 request:

```python
response = client.responses.create(
    model=model,
    input="Look up order A-102 and tell me its current status.",
    tools=[LOOKUP_ORDER_TOOL],
    tool_choice={"type": "function", "name": "lookup_order"},
)
```

playground는 `response.output`에서 `function_call` item 하나를 찾는다.

```python
call = next(
    item for item in response.output
    if item.type == "function_call"
)
```

이 시점에 local `lookup_order()`는 아직 실행되지 않았다.

## 5.3 Arguments는 data다

```python
arguments = json.loads(call.arguments)
```

이 값은 model-generated input이다.

Lab은 read-only function 하나만 다루므로 code를 짧게 유지한다.
Production application에서는 function allowlist, authorization, business precondition 같은 boundary가 추가될 수 있다.

중요한 등식:

```text
schema-valid
!=
authorized
!=
safe to execute
```

## 5.4 Application이 직접 실행한다

```python
result = lookup_order(arguments["order_id"])
```

여기서 처음 local business data가 생긴다.

Playground output에서 다음 두 부분을 비교한다.

```text
model proposal
local execution result
```

`status="shipped"` 같은 order 상태는 model이 임의로 만든 값이 아니라
application-owned lookup result에서 나와야 한다.

## 5.5 Result를 다시 model에게 보낸다

Local Python value는 자동으로 model context가 되지 않는다.

Application이 `function_call_output`을 만든다.

```python
tool_output = {
    "type": "function_call_output",
    "call_id": call.call_id,
    "output": json.dumps(result),
}
```

그리고 next request에 넣는다.

```python
final = client.responses.create(
    model=model,
    previous_response_id=response.id,
    input=[tool_output],
    tools=[LOOKUP_ORDER_TOOL],
    tool_choice="none",
)
```

이 lab은 한 번의 tool proposal과 한 번의 local execution만 추적하려는 controlled experiment다. 두 번째 request의
`tool_choice="none"`은 추가 tool call을 막아 마지막 stage를 final text로 제한한다. 일반 application에서는 후속
turn에서도 tool을 허용할 수 있으며, 그 경우 또 다른 `function_call`을 처리하는 loop가 필요하다.

Control flow:

```text
request + tool schema
→ model function_call proposal
→ application argument parsing
→ local function execution
→ function_call_output
→ final text response
```

## 5.6 Identifier를 구분한다

```text
response.id
→ Response resource

response._request_id
→ HTTP/API request tracing

call.call_id
→ function proposal과 function output correlation
```

세 ID를 전부 "response ID"라고 부르지 않는다.

## 5.7 직접 수정: 존재하지 않는 order를 요청한다

Input을 다음처럼 바꾼다.

```python
input="Look up order A-999 and tell me its current status."
```

실행 전에 예측한다.

- model proposal의 `arguments`는 어떻게 달라질까?
- local `lookup_order()` result는 어떻게 달라질까?
- final response는 어떤 application-owned data를 근거로 답해야 할까?

다시 실행해 각 stage를 비교한다.

## 5.8 Lab이 일부러 하지 않는 것

이 playground는 function calling control flow를 선명하게 보이기 위해:

- tool 하나
- 한 번의 function call
- read-only local data
- serial execution

만 사용한다.

Production system에서 여러 tool, parallel call, write side effect, retry/recovery가 필요하면
그때 별도 abstraction과 policy를 추가한다. 처음부터 generic dispatcher framework를 만들지 않는다.

## Practice

다음 값을 `model-generated` 또는 `application-generated`로 분류한다.

```text
call.name
call.arguments
call.call_id
lookup_order() result
function_call_output JSON
final response text
```

## Checkpoint

`lookup_order` 대신 read-only `lookup_user_timezone(user_id)` tool을 설계한다.

다음을 설명한다.

1. model에게 보내는 schema
2. application이 검증할 최소 argument
3. local function이 만드는 result
4. result를 어떤 `call_id`와 연결해 돌려보내는지
