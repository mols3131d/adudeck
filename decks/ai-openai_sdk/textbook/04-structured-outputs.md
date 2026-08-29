# 4. Structured Outputs: text를 읽는 것에서 typed contract를 검사하는 것으로

앞 chapter까지 application은 주로 `response.output_text`를 사람이 읽는 방식으로 결과를 해석했다.

하지만 application code가 model output을 다음 단계의 machine-readable input으로 사용하려면 문제가 달라진다.

```text
"priority: high라고 적어 줘"
```

라는 prompt는 사람이 읽기에는 충분할 수 있지만 다음 contract를 보장하는 Python type은 아니다.

```python
class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"]
    priority: Literal["low", "medium", "high"]
    summary: str
```

이번 chapter의 목표는 Structured Outputs를 "JSON을 잘 만들어 주는 기능"으로 외우는 것이 아니다.

> **application이 기대하는 output shape를 schema로 선언하고, response lifecycle과 refusal을 포함해 언제 그 값을 typed application data로 받아들여도 되는지 판단하는 것**이다.

## 4.1 free text와 typed contract는 다른 책임이다

다음 response를 생각해 보자.

```text
This looks like a high-priority bug. The checkout button freezes after card submission.
```

사람은 쉽게 읽을 수 있다. 하지만 application이 `category`, `priority`, `summary` field를 안정적으로 사용하려면 다시 parsing
logic을 만들어야 한다.

```text
free text
→ application-specific parsing
→ field가 정말 있는가?
→ enum spelling이 맞는가?
→ type이 맞는가?
```

Structured Outputs는 이 문제를 **schema contract를 model-facing output format에 포함하는 방식**으로 바꾼다.

Python SDK에서는 Pydantic model을 `responses.parse()`에 전달할 수 있다.

```python
from pydantic import BaseModel
from openai import OpenAI


class TicketClassification(BaseModel):
    category: str
    priority: str
    summary: str


client = OpenAI()
response = client.responses.parse(
    model="...",
    input="The checkout button freezes after I submit my card.",
    text_format=TicketClassification,
)
```

SDK는 Python type을 model-facing structured output schema로 연결하고, 성공적으로 생성된 structured text를 다시 typed
Python value로 parse하는 integration을 제공한다.

## 4.2 schema는 prompt 문구가 아니라 application contract다

다음 두 접근을 비교한다.

### Prompt-only convention

```text
Return JSON with category, priority, summary.
```

application은 여전히 다음을 스스로 처리해야 한다.

```text
valid JSON인가?
required field가 모두 있는가?
category가 허용 enum인가?
priority spelling이 예상과 같은가?
```

### Structured schema

```python
class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"]
    priority: Literal["low", "medium", "high"]
    summary: str
```

이제 shape와 허용 값이 source code의 type contract로 드러난다.

중요한 차이는 "prompt가 짧아졌다"가 아니다.

> **application이 어떤 data를 받아들일 것인지가 prose instruction에서 executable schema로 이동했다.**

## 4.3 Pydantic model에서 API response까지의 경로

학습용으로 단순화하면 다음 data flow다.

```text
Pydantic model
      ↓
SDK structured-output helper
      ↓
model-facing JSON Schema contract
      ↓
Responses API generation
      ↓
Response output content
      ↓
SDK parsing
      ↓
TicketClassification instance
```

여기서 각 단계의 owner가 다르다.

| 단계 | 책임 |
| --- | --- |
| Pydantic class | application이 원하는 shape/type/enum 선언 |
| SDK helper | Python type과 API structured format 사이의 integration |
| API generation | supplied schema를 따르는 output 생성 |
| parsed object | application이 사용하는 typed result |

이번 playground의 `TicketClassification.model_json_schema()`를 출력하는 것은 **application-side Pydantic schema를 관찰**하는
것이다. SDK가 API request에 사용하는 최종 serialization 전체를 wire-level로 본 것은 아니다.

Unit 1의 boundary를 그대로 적용한다.

```text
local Python representation
!=
actual HTTP body
```

## 4.4 `response.output_parsed`만 바로 읽으면 충분한가

가장 짧은 happy path는 다음처럼 보일 수 있다.

```python
result = response.output_parsed
```

하지만 robust한 application mental model에서는 먼저 여러 gate를 구분한다.

```text
1. HTTP/SDK call 자체가 성공했는가?
2. Response generation status가 completed인가?
3. output content가 refusal인가, output_text인가?
4. expected schema로 parsed value가 존재하는가?
5. parsed value가 application business invariant도 만족하는가?
```

Unit 3의 transport/API failure와 이번 Unit의 output contract를 연결하면 다음과 같다.

```text
SDK exception 없음
      ↓
typed Response/ParsedResponse 획득
      ↓
response.status 확인
      ↓
output content type 확인
      ↓
parsed value 확인
      ↓
application rule 확인
```

각 gate는 다른 실패를 잡는다.

## 4.5 Response status는 schema parsing보다 바깥쪽 state다

Responses API의 response status에는 `completed` 외에도 `failed`, `in_progress`, `cancelled`, `queued`, `incomplete` 같은 state가
존재할 수 있다.

따라서 다음 코드는 너무 강한 가정을 한다.

```python
result = response.output_parsed
assert result is not None
```

먼저 response lifecycle을 본다.

```python
if response.status != "completed":
    details = response.error or response.incomplete_details
    ...
```

예를 들어 output token limit 때문에 generation이 incomplete라면 "schema가 틀렸다"고 진단하기 전에 **response 자체가
terminal completed state에 도달했는가**를 확인해야 한다.

`response.output_parsed`가 `None`이라는 증상 하나만으로 root cause를 결정하지 않는다.

## 4.6 Refusal은 malformed JSON과 다른 output state다

Structured Outputs를 사용할 때도 model이 요청을 거절할 수 있다.

Responses output message의 content는 `output_text`뿐 아니라 `refusal` 같은 별도 content type을 가질 수 있다.

개념적으로 다음을 구분한다.

```text
output_text
→ structured text가 존재하고 parsed result를 확인할 수 있음

refusal
→ model이 structured business result 대신 refusal을 반환

incomplete response
→ generation lifecycle 자체가 완료되지 않음
```

따라서 refusal을 "Pydantic validation error"라고 처리하면 안 된다.

```text
refusal
!=
invalid schema-shaped JSON
!=
incomplete generation
```

각 state는 application에서 다른 UX/diagnosis를 요구할 수 있다.

## 4.7 worked trace: support ticket 하나를 typed result로 바꾼다

input:

```text
The checkout button freezes after I submit my card.
Classify this support ticket and summarize it.
```

application contract:

```python
class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"]
    priority: Literal["low", "medium", "high"]
    summary: str
```

execution을 state 기준으로 추적한다.

| Step | state / evidence | 아직 결론 내릴 수 없는 것 |
| --- | --- | --- |
| 1 | Pydantic class 존재 | model이 실제 structured output을 만들었는지 |
| 2 | `responses.parse(...)` 호출 | API response status |
| 3 | ParsedResponse 반환 | business 의미가 정확한지 |
| 4 | `status == completed` | refusal인지 output text인지 |
| 5 | output content=`output_text` | parsed value가 존재하는지 |
| 6 | `output_parsed`가 `TicketClassification` | classification의 business correctness |

마지막 구분이 중요하다.

```text
schema-valid
!=
semantically correct
```

`priority="high"`가 enum contract에는 맞아도 실제 support policy상 priority 판단이 틀릴 수 있다.

Structured Outputs는 **shape/type contract**를 강화하지만 domain truth를 자동으로 보장하지 않는다.

## 4.8 Observable Lab A: API 없이 schema ownership을 본다

먼저 preview를 실행한다.

```bash
python playground/structured_output.py --preview
```

output에서 두 영역을 구분한다.

```text
application-owned Pydantic schema
call plan
```

실행 전에 다음을 답한다.

1. `category`에는 어떤 값만 허용되는가?
2. `priority` spelling을 application이 어디에서 정의했는가?
3. `summary`의 "좋은 요약" 여부까지 schema가 검증하는가?
4. 이 preview가 server-side structured generation을 증명하는가?

마지막 질문의 답은 아니다.

preview는 local schema와 application call plan만 보여 준다.

## 4.9 Observable Lab B: completed response의 여러 observation surface를 본다

valid credential과 model access가 있다면 실행한다.

```bash
uv run playground/structured_output.py
```

playground는 다음을 별도로 출력한다.

```text
response.status
response.id
response._request_id
response.incomplete_details
response.error
output item type
content type
content text
content.parsed
response.output_parsed
```

`output_parsed`만 보고 끝내지 않는다.

다음 chain을 실제 값으로 설명한다.

```text
HTTP/SDK call returned
→ response status
→ message/content type
→ parsed typed value
→ application result
```

## 4.10 schema를 한 dimension만 바꾸고 비교한다

예를 들어 priority enum을 다음처럼 줄인 local copy를 만든다.

```python
priority: Literal["normal", "urgent"]
```

실행 전에 예측한다.

- application-side schema에서 무엇이 바뀌는가?
- 같은 input이라도 parsed Python value의 가능한 범위가 어떻게 바뀌는가?
- 이것이 실제 ticket urgency를 더 정확하게 판단한다는 뜻인가?

핵심은 schema 변경이 **output contract를 바꾼다**는 것이지 business truth를 자동 개선한다는 뜻이 아니다.

## 4.11 field description은 type과 다른 역할을 가진다

Pydantic `Field(description=...)`를 사용할 수 있다.

```python
priority: Literal["low", "medium", "high"] = Field(
    description="The urgency implied by the ticket."
)
```

`Literal`은 allowed value set을 구조적으로 제한한다.

`description`은 field의 의미를 model에 설명한다.

둘을 하나로 생각하지 않는다.

```text
allowed representation
!=
semantic instruction
```

좋은 schema는 type만 맞는 object가 아니라 각 field의 responsibility도 명확하게 만든다.

## 4.12 schema를 application domain model 전체와 동일시하지 않는다

API output contract와 내부 domain model이 항상 같은 type일 필요는 없다.

예를 들어 API에서 다음을 받는다고 하자.

```python
class ModelClassification(BaseModel):
    category: str
    priority: str
    summary: str
```

application은 그 뒤 별도 business validation을 수행할 수 있다.

```text
model classification
      ↓
business rule / authorization / database lookup
      ↓
application domain decision
```

Structured Outputs type이 있다는 이유로 model output을 validation 없이 곧바로 destructive action에 연결하지 않는다.

schema contract와 business authority는 별개다.

## 4.13 흔한 잘못된 mental model

### "Structured Outputs는 JSON mode와 같은 뜻이다"

이번 chapter의 핵심은 단순 valid JSON보다 **supplied schema에 맞춘 structured contract와 SDK typed parsing**이다.

### "Pydantic model이 있으니 model 답도 사실이다"

schema validity와 semantic/business correctness는 다르다.

### "`output_parsed is None`이면 API request가 실패했다"

Response status, refusal, incomplete details 등 더 바깥쪽 state를 먼저 본다.

### "refusal은 schema parsing bug다"

refusal은 별도 content state다.

### "preview에서 Pydantic JSON schema를 출력했으니 실제 HTTP schema를 검증했다"

application-side representation만 확인했다.

### "structured result를 받으면 `response.id`나 request ID는 필요 없다"

observability/debugging identity는 output data contract와 별도 책임이다.

## 4.14 Practice

### A. Gate classification

다음 상황을 어느 gate에서 처리할지 분류한다.

```text
HTTP 429
response.status == incomplete
message content가 refusal
output_parsed is None
parsed priority가 high지만 사내 SLA rule상 medium이어야 함
```

후보:

```text
SDK/API failure
response lifecycle
content state
schema parsing
business validation
```

### B. Schema repair

다음 contract의 약점을 찾는다.

```python
class Job(BaseModel):
    action: str
    retry: str
```

실제 application은 action이 `create | cancel | inspect` 중 하나이고 retry는 boolean이어야 한다.

Pydantic type을 수정하고 무엇이 구조적으로 강해졌는지 설명한다.

### C. Boundary reasoning

개발자가 다음 코드를 작성했다.

```python
result = client.responses.parse(...).output_parsed
save_to_database(result)
```

중간에 어떤 state/business checks가 필요한지 요구사항을 가정해 설계한다.

### D. Transfer

structured result가 다음 API call의 input이 된다.

```text
TicketClassification
→ routing service
```

routing service가 요구하는 invariant와 model-facing schema가 어디까지 같고 어디서 달라져야 하는지 설명한다.

## Assessment checkpoint

이번 chapter는 다음 두 과제를 독립적으로 수행할 수 있을 때 통과한다.

### 1. Structured response execution map

Pydantic class부터 application domain decision까지 다음 경계를 그린다.

```text
Python schema
→ SDK parse call
→ Response status
→ output content type
→ parsed value
→ business validation
```

각 단계에서 얻은 evidence와 아직 보장되지 않은 것을 적는다.

### 2. Contract redesign

자유형 text를 downstream code가 regex로 parsing하는 작은 application을 받는다.

learner는:

1. Pydantic schema를 설계한다.
2. `responses.parse()` boundary를 배치한다.
3. incomplete/refusal/parsed-result 처리 순서를 설계한다.
4. schema만으로 검증할 수 없는 business invariant를 하나 분리한다.
5. response/request identity를 observability에 남긴다.

평가 기준:

- prose format instruction과 schema contract를 구분했는가?
- Response lifecycle, refusal, parsed value를 서로 다른 state로 처리했는가?
- type correctness를 semantic truth로 과장하지 않았는가?
- local Pydantic schema와 wire/API evidence를 혼동하지 않았는가?
- downstream application responsibility를 명시했는가?

이 기준을 만족하면 Unit 4의 핵심 outcome인 **model output을 typed application contract로 받되 response lifecycle과 business
validation boundary를 함께 지키는 능력**을 갖춘 것으로 본다.
