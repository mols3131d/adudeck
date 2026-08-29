# 5. Function Calling: model의 제안과 application 실행을 분리한다

Structured Outputs에서는 model output을 typed data contract로 받았다.

Function Calling에서는 경계가 한 단계 더 확장된다.

model은 application이 제공한 function schema를 보고 다음과 같은 output item을 만들 수 있다.

```text
function_call
- name
- arguments
- call_id
```

여기서 가장 중요한 문장은 이것이다.

> **model은 Python 함수를 실행하지 않는다. application이 function call을 읽고, 허용 여부와 arguments를 검증하고, 실제
> code를 실행한 뒤 결과를 다시 API input으로 보낸다.**

이번 chapter는 function calling을 "LLM에게 tool을 주면 알아서 실행한다"고 배우지 않는다.
**proposal → validation → application execution → correlated tool output → next response**라는 control flow로 배운다.

## 5.1 tool schema는 executable function 자체가 아니다

application에 다음 함수가 있다고 하자.

```python
def lookup_order(order_id: str) -> dict:
    ...
```

Responses API에 보내는 것은 이 Python function object 자체가 아니다.

model에게는 function tool definition을 제공한다.

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

이 schema가 하는 일과 하지 않는 일을 분리한다.

```text
tool schema
→ model에게 callable interface의 이름/의미/argument shape를 설명

Python function
→ application process 안에서 실제 business logic 수행
```

schema를 API에 전달했다고 local function이 remote server에 upload되는 것도 아니다.

## 5.2 첫 response의 목적이 최종 text가 아닐 수 있다

일반 text call에서는 다음 흐름을 기대했다.

```text
user input
→ Response
→ output_text
```

Function Calling에서는 첫 response가 다음처럼 끝날 수 있다.

```text
user input
→ Response
→ function_call item
```

예:

```text
name      = lookup_order
arguments = {"order_id":"A-102"}
call_id   = call_...
```

이것은 "주문 상태를 조회했다"는 뜻이 아니다.

정확한 의미는 다음이다.

> model이 현재 context와 tool contract를 바탕으로 `lookup_order` 호출을 application에 요청했다.

실제 data lookup은 아직 application code에서 일어나지 않았다.

## 5.3 Function call loop 전체를 먼저 본다

Responses API의 기본 custom function loop를 단순화하면 다음과 같다.

```text
application
  |
  | request + tools
  v
Responses API / model
  |
  | function_call(name, arguments, call_id)
  v
application
  |
  | validate name / arguments / authorization
  | execute local function
  | serialize result
  v
function_call_output(call_id, output)
  |
  | next Responses request
  v
Responses API / model
  |
  | final text or another function_call
  v
application
```

loop의 가운데를 누가 소유하는지 강조한다.

```text
model owns proposal
application owns execution
```

이 ownership이 Function Calling의 핵심이다.

## 5.4 `arguments`는 JSON string이다

function call output item에서 arguments는 model이 생성한 JSON-encoded string이다.

```python
arguments = json.loads(call.arguments)
```

`strict=True` schema는 argument shape contract를 강화하지만 application은 여전히
**어떤 function name을 실제 dispatcher가 허용하는지** 확인해야 한다.

```python
if call.name != "lookup_order":
    raise ValueError(...)
```

그리고 parsed arguments가 local function contract와 맞는지 확인한다.

```python
if set(arguments) != {"order_id"}:
    raise ValueError(...)
```

여기서 schema validation과 application authorization을 하나로 만들지 않는다.

```text
schema-valid arguments
!=
application이 실행을 허용해야 함
```

예를 들어 `delete_user(user_id=...)`의 argument shape가 완벽하더라도 현재 caller가 해당 deletion 권한을 가지는지는 별도
business/security 판단이다.

## 5.5 `call_id`는 request와 result를 연결하는 correlation key다

application이 function을 실행한 뒤 API에 결과를 돌려줄 때 다음 input item을 만든다.

```python
{
    "type": "function_call_output",
    "call_id": call.call_id,
    "output": json.dumps(result),
}
```

여기서 `call_id`가 중요하다.

```text
function_call A
call_id = call_A

function_call_output
call_id = call_A
```

같은 ID를 사용해 **어느 requested call의 결과인지** 연결한다.

`response.id`, output item의 optional `id`, `call_id`를 하나의 identifier로 뭉개지 않는다.

```text
response.id
→ 전체 Response resource identity

response._request_id
→ HTTP/API request debugging identity

call_id
→ function call proposal과 application result의 correlation identity
```

각 ID는 다른 관계를 추적한다.

## 5.6 result는 model에 직접 return하는 것이 아니라 다음 input item이 된다

local function:

```python
result = lookup_order("A-102")
```

Python return value가 자동으로 model context에 들어가지 않는다.

application이 serialize하고 다음 Responses request에 넣는다.

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

두 번째 request가 첫 response와 이어지는 state mechanism은 Unit 2의 `previous_response_id`다.

따라서 Function Calling은 새 독립 개념만이 아니라 이전 unit을 결합한다.

```text
conversation state ownership
+
structured arguments
+
application execution
+
correlation identity
```

## 5.7 worked trace: order A-102를 조회한다

user input:

```text
Look up order A-102 and tell me its current status.
```

lab은 첫 response에서 `lookup_order`를 호출하도록 tool choice를 고정한다. 이것은 control flow를 안정적으로 관찰하기 위한
**teaching instrumentation**이다. 일반 application이 모든 turn에서 tool call을 강제해야 한다는 설계 원칙이 아니다.

### Round 1 — model proposal

```text
response.id = resp_1
response.output
  → function_call
      name = lookup_order
      arguments = {"order_id":"A-102"}
      call_id = call_1
```

아직 local order dictionary를 읽지 않았다.

### Application execution

```python
args = json.loads(call.arguments)
result = lookup_order(args["order_id"])
```

lab data:

```json
{
  "order_id": "A-102",
  "status": "shipped",
  "eta": "2026-08-31",
  "found": true
}
```

이 state는 OpenAI API가 만든 것이 아니라 **application-owned tool execution result**다.

### Correlated output

```text
function_call_output
call_id = call_1
output = serialized application result
```

### Round 2 — model interpretation

```text
previous_response_id = resp_1
input = function_call_output(call_1, ...)
```

그 다음 model은 final text를 만들 수도 있고 필요하면 또 다른 function call을 요청할 수도 있다.

## 5.8 한 response에 function call이 하나라고 가정하지 않는다

Responses output array의 길이와 item order는 model response에 따라 달라질 수 있다.

다음 코드는 brittle하다.

```python
call = response.output[0]
```

대신 output item을 type으로 검사한다.

```python
calls = [item for item in response.output if item.type == "function_call"]
```

한 response에 여러 function call이 있을 수 있으므로 각 call에 matching output을 만들어야 한다.

```text
call_A → output_A with call_id A
call_B → output_B with call_id B
```

parallel execution을 실제로 사용할지는 application responsibility와 side-effect safety에 따라 판단한다.

이번 lab은 작은 deterministic lookup 하나를 사용하지만 mental model은 multiple-call case까지 확장된다.

## 5.9 tool execution은 side effect boundary다

`lookup_order`는 read-only라 안전한 학습 도구다.

하지만 실제 function은 다음을 할 수 있다.

```text
email 발송
결제 취소
database update
workflow trigger
file 삭제
```

model의 call proposal을 곧바로 실행하면 안 되는 이유가 여기 있다.

application은 최소한 다음을 소유한다.

```text
allowed tool registry
argument validation
caller authorization
business precondition
idempotence / duplicate handling
execution timeout / error mapping
audit / observability
```

Function Calling은 model에게 application authority를 넘기는 기능이 아니다.

> model은 **무엇을 호출하면 좋을지 제안**할 수 있고, actual authority는 application execution layer에 남는다.

## 5.10 Unit 3의 retry와 local tool retry를 섞지 않는다

SDK automatic retry는 API HTTP attempt에 관한 policy였다.

local tool execution은 application code다.

```text
Responses API request retry
!=
lookup_order()를 다시 실행
```

하지만 application이 whole tool loop를 바깥에서 재시도한다면 local side effect가 반복될 수 있다.

예를 들어:

```text
1. model function_call 생성
2. application이 payment 취소 성공
3. function_call_output를 보내기 전에 process crash
4. whole workflow를 처음부터 재시작
5. payment 취소 function을 다시 실행할 가능성
```

그래서 destructive tool에는 business-level idempotency key나 existing-state check가 필요할 수 있다.

`call_id`는 API correlation에 중요하지만 **모든 external system이 자동으로 idempotent해지는 마법의 key는 아니다.**

## 5.11 Observable Lab A: API 없이 execution ownership을 표시한다

```bash
python playground/function_calling.py --preview
```

preview에서 다음을 찾는다.

```text
tool schema
first request tool choice
model-proposed function_call
application validation + dispatch
function_call_output
previous_response_id continuation
```

다음을 답한다.

1. preview에서 `lookup_order()`가 실제 실행되었는가?
2. model에게 전달되는 것은 Python dict dataset인가, function schema인가?
3. local result를 누가 JSON string으로 serialize하는가?
4. `call_id`를 누가 생성하고 누가 다시 사용해야 하는가?

## 5.12 Observable Lab B: live tool loop를 단계별로 본다

valid credential과 model access가 있으면 실행한다.

```bash
uv run playground/function_calling.py
```

playground는 round별로 다음을 출력한다.

```text
Response status / IDs
output item types
function name
call_id
raw arguments JSON
application execution result
next Response
final output text
```

실행 뒤 다음 경계를 실제 값으로 설명한다.

```text
model-generated state
vs.
application-generated state
```

특히 `status="shipped"`라는 business data가 **어느 순간 처음 등장했는지** 찾는다.

첫 model response가 아니라 local `lookup_order()` execution에서 등장해야 한다.

## 5.13 dispatcher를 깨뜨려 failure boundary를 본다

local working copy에서 다음 variation을 생각한다.

```python
if name != "lookup_order":
    ...
```

검사를 제거하고 arbitrary name을 `globals()[name](...)` 같은 방식으로 실행하면 어떤 문제가 생기는가?

model-generated string이 application execution authority를 직접 선택하게 된다.

좋은 dispatcher는 explicit allowlist를 가진다.

```python
TOOLS = {
    "lookup_order": lookup_order,
}
```

그리고 각 tool마다 argument/business validation을 적용한다.

이번 lab은 function 하나라 `if`로 충분하다. 미래 tool registry를 예상해 abstraction을 과도하게 만들지 않는다.

## 5.14 tool result도 application contract다

tool output은 string으로 API에 전달된다.

structured data라면 JSON encoding이 자연스럽다.

```python
output=json.dumps(result)
```

하지만 다음을 구분한다.

```text
tool input schema
→ model이 요청할 arguments contract

tool output contract
→ application이 model에게 되돌리는 result semantics
```

input schema가 strict하다고 output data가 자동으로 올바른 것은 아니다.

application function이 stale/inconsistent data를 반환하면 model은 그 result를 바탕으로 잘못된 final answer를 만들 수
있다.

## 5.15 흔한 잘못된 mental model

### "model이 `lookup_order` 함수를 실행한다"

model은 function call output item을 생성한다. 실제 Python execution은 application이 한다.

### "tool schema가 있으니 authorization도 끝났다"

schema validation과 caller/business authorization은 다르다.

### "`call_id`는 Response ID다"

function request/result correlation을 위한 별도 identity다.

### "function result를 return하면 SDK가 알아서 model에게 전달한다"

application이 `function_call_output` input item을 만들어 다음 request에 보내야 한다.

### "response.output[0]은 항상 function_call이다"

output array는 item type을 검사해야 한다.

### "tool calling helper를 쓰면 application function도 자동 실행된다"

Responses API의 parsing helper는 argument parsing을 도울 수 있지만 application-owned execution loop 자체를 없애지
않는다.

### "read-only lookup이 안전하니 write tool도 같은 pattern으로 바로 실행하면 된다"

side effect, authorization, idempotence, audit responsibility가 추가된다.

## 5.16 Practice

### A. State owner trace

아래 값을 owner별로 분류한다.

```text
tool JSON schema
function_call.arguments
function_call.call_id
ORDERS dictionary
lookup_order return value
function_call_output JSON
final response.output_text
```

후보:

```text
application-authored contract
model/API-derived proposal
application business state/execution
correlation state
final API-derived output
```

### B. Correlation repair

두 function call이 한 response에 들어왔다.

```text
call_A: lookup_order(A-101)
call_B: lookup_order(A-102)
```

application이 output 두 개 모두 `call_id=call_A`로 보냈다.

무엇이 깨졌는지 설명하고 correct mapping을 그린다.

### C. Authorization design

다음 tool을 추가한다고 하자.

```text
cancel_order(order_id)
```

schema validation 외에 application이 확인해야 할 precondition을 최소 네 가지 설계한다.

### D. Retry reasoning

`cancel_order()` side effect는 성공했지만 process가 function output을 API에 보내기 전에 종료됐다.

whole workflow를 재시작할 때 duplicate cancellation을 막기 위한 application/external-system invariant를 설계한다.

## Assessment checkpoint

이번 chapter는 다음 두 과제를 독립적으로 수행할 수 있을 때 통과한다.

### 1. Function-call execution map

실제 또는 주어진 trace에서 다음을 표시한다.

```text
request + tool schema
→ function_call output
→ argument/name validation
→ local function execution
→ function_call_output with matching call_id
→ next Response
→ final text or next call
```

각 단계의 state owner와 identifier를 설명한다.

### 2. Safe dispatcher modification

`lookup_order` 외에 read-only function 하나를 추가한다.

learner는:

1. strict input schema를 정의한다.
2. dispatcher allowlist를 확장한다.
3. multiple function call을 type-based iteration으로 처리한다.
4. 각 result를 matching `call_id`로 돌려준다.
5. 예상치 못한 tool name/invalid arguments를 application failure로 분류한다.
6. write-side effect tool로 확장할 때 추가될 authorization/idempotence boundary를 설명한다.

평가 기준:

- model proposal과 Python execution을 분리했는가?
- schema validation과 execution authorization을 구분했는가?
- `call_id`, `response.id`, request ID의 역할을 구분했는가?
- output array의 cardinality/type을 고정 가정하지 않았는가?
- tool result를 명시적 next-request input으로 연결했는가?
- side effect와 retry risk를 application responsibility로 남겼는가?

이 기준을 만족하면 Unit 5의 핵심 outcome인 **model이 제안한 function call을 application-owned control flow에서
검증·실행하고 `call_id`로 결과를 정확히 연결하는 능력**을 갖춘 것으로 본다.
