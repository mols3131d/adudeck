# 5. Function Calling: model의 제안과 application 실행을 분리한다

Function Calling에서 model이 만드는 것은 **실행 결과가 아니라 실행 요청**이다.

```text
function_call
- name
- arguments
- call_id
```

> **model은 무엇을 호출할지 제안한다. 실제 function 실행과 authority는 application이 소유한다.**

이 한 문장을 유지하면 Function Calling의 control flow, validation, side effect를 훨씬 쉽게 설명할 수 있다.

## 5.1 Tool schema와 executable function은 다른 object다

Application code:

```python
def lookup_order(order_id: str) -> dict:
    ...
```

Model에게 보내는 tool definition:

```python
tool = {
    "type": "function",
    "name": "lookup_order",
    "description": "Look up one order.",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {"type": "string"},
        },
        "required": ["order_id"],
        "additionalProperties": False,
    },
    "strict": True,
}
```

역할은 다르다.

```text
tool schema
→ model이 사용할 callable interface를 설명

Python function
→ application process에서 실제 business logic을 실행
```

Schema를 API에 보냈다고 local function이 remote server에 upload되거나 자동 실행되는 것은 아니다.

## 5.2 Function loop 전체를 먼저 본다

```text
request + tools
      ↓
model
      ↓
function_call(name, arguments, call_id)
      ↓
application
  - allowlist / authorization
  - arguments validation
  - local function execution
      ↓
function_call_output(call_id, output)
      ↓
next Responses request
      ↓
final text or another function_call
```

Ownership은 간단하다.

```text
model owns proposal
application owns execution
```

첫 Response에 final text가 없고 `function_call`만 있어도 정상적인 intermediate state일 수 있다.

## 5.3 `arguments`는 실행 명령이 아니라 untrusted input이다

Function-call arguments는 JSON-encoded data로 온다.

```python
args = json.loads(call.arguments)
```

`strict=True` schema가 argument shape를 강화해도 application은 최소한 다음을 판단해야 한다.

```text
이 function name을 허용하는가?
현재 caller가 이 operation을 실행할 권한이 있는가?
business precondition이 맞는가?
```

즉:

```text
schema-valid
!=
authorized
!=
safe to execute
```

Read-only lookup과 payment cancellation을 같은 dispatcher policy로 다루면 안 된다.

## 5.4 `call_id`는 proposal과 result를 연결한다

실행 결과를 다음 request에 돌려줄 때:

```python
{
    "type": "function_call_output",
    "call_id": call.call_id,
    "output": json.dumps(result),
}
```

`call_id`는 어느 function request의 결과인지 연결하는 correlation key다.

```text
response.id
→ Response resource

response._request_id
→ HTTP/API request tracing

call_id
→ function proposal ↔ function result
```

Identifier 역할을 분리하면 multi-call debugging이 쉬워진다.

## 5.5 Local return value는 자동으로 model context가 되지 않는다

```python
result = lookup_order(args["order_id"])
```

이 Python value는 아직 application memory에만 있다. Application이 serialize해 다음 Responses request에 넣어야 한다.

```python
second = client.responses.create(
    model=model,
    previous_response_id=first.id,
    input=[
        {
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": json.dumps(result),
        }
    ],
    tools=[tool],
)
```

여기서 Unit 2의 conversation-state concept가 다시 등장한다.

```text
first response identity
+
function_call_output
→ next model turn
```

Function Calling은 독립 기능 하나가 아니라 **state ownership + structured arguments + application execution**을
결합한다.

## 5.6 Worked trace: order A-102 조회

```text
user
"Look up order A-102."

Round 1 model output
function_call
  name      = lookup_order
  arguments = {"order_id":"A-102"}
  call_id   = call_1

application
  parse arguments
  validate allowed tool
  execute lookup_order("A-102")

application result
{"order_id":"A-102","status":"shipped","found":true}

next input
function_call_output
  call_id = call_1
  output  = serialized result

Round 2
model interprets returned business data
```

`status="shipped"`는 첫 model response가 아니라 **application-owned lookup result**에서 처음 등장해야 한다. 이 위치를
찾는 것이 control-flow 이해의 핵심이다.

## 5.7 한 Response에 function call 하나만 있다고 가정하지 않는다

Brittle:

```python
call = response.output[0]
```

더 안전한 mental model:

```python
calls = [
    item for item in response.output
    if item.type == "function_call"
]
```

여러 call이 있으면 각각 matching `call_id`의 output이 필요하다.

Parallel execution 여부는 별도 application decision이다. Side effect, ordering, resource limits가 중요하면 무조건
parallelize하지 않는다.

## 5.8 Tool execution은 side-effect boundary다

Read-only tool:

```text
lookup_order
```

Write tool:

```text
send_email
cancel_payment
update_database
delete_file
```

Write tool에서는 다음 application responsibility가 중요해진다.

```text
explicit allowlist
authorization
business precondition
idempotence / duplicate handling
timeout / error mapping
audit evidence
```

`call_id`는 API correlation key이지 external side effect를 자동 idempotent하게 만드는 key가 아니다.

Unit 3의 SDK retry도 구분한다.

```text
Responses API HTTP retry
!=
local tool execution retry
```

Whole tool loop를 다시 실행하면 local side effect가 반복될 수 있으므로 business-level recovery policy가 필요할 수 있다.

## 5.9 Playground: proposal과 execution 사이의 경계를 관찰한다

먼저 preview:

```bash
python playground/function_calling.py --preview
```

확인할 것:

1. API에 보내는 것은 tool schema이지 Python dataset/function body가 아니다.
2. model이 만들 것으로 기대하는 `function_call` shape.
3. application이 validation/dispatch를 소유한다.
4. result는 `function_call_output`으로 다시 보낸다.

Live access가 있다면:

```bash
uv run playground/function_calling.py
```

다음 순서만 추적한다.

```text
first Response IDs
→ function_call name / arguments / call_id
→ local execution result
→ function_call_output
→ second Response
```

Output text의 문장 품질보다 **어느 state가 model-generated이고 어느 state가 application-generated인지** 먼저 설명한다.

### Variation

Dispatcher를 다음처럼 만들자는 제안을 검토한다.

```python
globals()[call.name](**args)
```

왜 explicit allowlist보다 위험한지 설명한다. Lab에는 function 하나뿐이므로 거대한 registry abstraction을 추가할 필요는
없다.

## 5.10 Validation boundary

| Evidence | 검증하는 것 | 검증하지 않는 것 |
| --- | --- | --- |
| preview | application control-flow plan | 실제 model tool choice |
| live first Response | model이 function call item을 반환함 | local function이 안전함 |
| local execution result | application function behavior | model final interpretation correctness |
| final Response | tool output을 model이 후속 turn에 사용함 | business action authorization 전체 |

## 5.11 흔한 오해

### "model이 Python function을 실행한다"

Model은 function-call proposal을 만든다. Execution은 application이 한다.

### "tool schema가 authorization이다"

Schema는 argument contract다. Authority는 application policy다.

### "`call_id`가 Response ID다"

서로 다른 identity다.

### "function return value는 SDK가 자동으로 model에게 보낸다"

Application이 `function_call_output`을 만들어 next request에 넣는다.

### "`response.output[0]`은 항상 function_call이다"

Output item은 type으로 판단한다.

## 5.12 Practice

### A. Ownership trace

다음 값을 `model-generated` / `application-generated`로 분류한다.

```text
call.name
call.arguments
call.call_id
lookup_order() result
function_call_output JSON
final response text
```

### B. Safe dispatcher

다음 요구만 만족하는 최소 dispatcher를 설계한다.

```text
허용 tool: lookup_order
argument: order_id string 하나
unknown tool은 실행하지 않음
```

추상화를 늘리는 것이 아니라 **authority boundary가 code에 보이게** 만든다.

### C. Side-effect review

`cancel_payment` tool을 추가한다고 가정한다. 다음을 구분해 설계한다.

```text
argument schema
caller authorization
duplicate execution protection
API call retry
tool execution retry/recovery
audit evidence
```

## Assessment checkpoint

다음을 독립적으로 설명할 수 있으면 통과한다.

1. Function Calling loop를 `proposal → validation → execution → correlated output → next response`로 추적한다.
2. `response.id`, request ID, `call_id`의 역할을 구분한다.
3. Schema-valid tool call이 application authority를 자동으로 갖지 않는 이유를 설명한다.
4. Retry나 workflow restart가 tool side effect를 반복할 수 있는 지점을 찾아 안전한 boundary를 제안한다.
