# 4. Structured Outputs: text가 아니라 typed contract를 다룬다

사람이 읽을 답이라면 free text로 충분할 수 있다. 하지만 model output이 다음 application step의 input이 되면
"JSON처럼 보인다"보다 강한 contract가 필요하다.

```python
class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"]
    priority: Literal["low", "medium", "high"]
    summary: str
```

이번 chapter의 핵심은 다음이다.

> **schema는 output의 shape/type을 제한하지만, response lifecycle과 business correctness까지 대신 보장하지 않는다.**

## 4.1 Prompt convention과 schema contract를 구분한다

Prompt-only:

```text
Return JSON with category, priority, summary.
```

Application이 여전히 확인해야 한다.

```text
valid JSON인가?
required field가 있는가?
enum spelling이 맞는가?
type이 맞는가?
```

Structured Outputs에서는 application이 기대하는 representation을 schema로 선언한다.

```python
response = client.responses.parse(
    model="...",
    input="The checkout button freezes after card submission.",
    text_format=TicketClassification,
)
```

개념적으로:

```text
Pydantic type
→ SDK structured-output integration
→ API generation
→ parsed Python value
```

`model_json_schema()`를 출력해 보는 것은 **application-side schema**를 관찰하는 것이다. Wire-level HTTP body를 직접 본
것으로 해석하지 않는다.

## 4.2 Typed result를 받기 전 다섯 gate를 통과한다

`response.output_parsed`만 바로 읽으면 중요한 실패 상태를 놓칠 수 있다.

```text
1. SDK/API call이 성공했는가?
2. response.status가 expected lifecycle state인가?
3. output content가 refusal인가, expected output인가?
4. expected schema로 parsed value가 존재하는가?
5. parsed value가 business invariant를 만족하는가?
```

각 gate가 잡는 실패는 다르다.

| Gate | 대표 문제 |
| --- | --- |
| SDK/API | timeout, 429, 5xx |
| Response lifecycle | incomplete/failed 등 |
| Content state | refusal 또는 예상하지 않은 content type |
| Schema parsing | expected typed value 없음 |
| Business rule | schema-valid하지만 실제 정책에는 틀린 값 |

이 순서가 Unit 3의 failure boundary와 Structured Outputs를 연결한다.

## 4.3 Refusal, incomplete, invalid business result는 다른 상태다

다음을 하나의 "parse failure"로 묶지 않는다.

```text
refusal
→ model이 requested business result 대신 refusal content를 반환

incomplete response
→ generation lifecycle이 완료되지 않음

parsed value 없음
→ expected typed result를 얻지 못함

business-invalid
→ schema에는 맞지만 application rule에 맞지 않음
```

예를 들어 `priority="high"`는 enum에는 맞아도 실제 SLA policy상 잘못된 판단일 수 있다.

```text
schema-valid
!=
semantically correct
!=
authorized business action
```

Structured Outputs는 representation contract를 강화한다. Domain truth나 authorization boundary를 제거하지 않는다.

## 4.4 Worked trace: support ticket을 application data로 받아들일 때

Input:

```text
The checkout button freezes after I submit my card.
```

Schema:

```python
class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"]
    priority: Literal["low", "medium", "high"]
    summary: str
```

판단 순서를 추적한다.

| Step | evidence | 다음 질문 |
| --- | --- | --- |
| `responses.parse()`가 반환 | typed Response 계열 object | lifecycle이 completed인가? |
| `status` 확인 | generation state | refusal/expected content인가? |
| content 확인 | output state | parsed value가 있는가? |
| `output_parsed` 확인 | Pydantic instance | business rule도 맞는가? |

이 trace의 목적은 check를 많이 추가하는 것이 아니다. **root cause가 다른 실패를 같은 exception처럼 취급하지 않는 것**이다.

## 4.5 Schema는 "허용 표현"과 "field 의미"를 함께 드러낸다

```python
priority: Literal["low", "medium", "high"] = Field(
    description="The urgency implied by the ticket."
)
```

역할을 구분한다.

```text
Literal
→ 허용 representation

description
→ field semantic guidance
```

그리고 API-facing schema와 내부 domain model이 반드시 하나일 필요도 없다.

```text
model-facing structured result
→ business validation / lookup / authorization
→ domain decision
```

Model output을 destructive action에 바로 연결하지 않는 이유다.

## 4.6 Playground: schema → response state → parsed value를 한 번에 추적한다

먼저 local preview:

```bash
python playground/structured_output.py --preview
```

확인할 것:

1. application이 선언한 schema
2. call plan
3. preview가 실제 API generation을 증명하지 않는다는 boundary

Live access가 있다면:

```bash
uv run playground/structured_output.py
```

다음 순서로 output을 읽는다.

```text
response.status
→ output item/content type
→ refusal/incomplete evidence
→ parsed value
→ application interpretation
```

한 번에 모든 field를 암기하려 하지 않는다. **현재 gate를 판단하는 field만** 본다.

### Variation

Schema의 한 dimension만 바꾼다.

```python
priority: Literal["normal", "urgent"]
```

예측한다.

- 가능한 parsed value 범위는 어떻게 달라지는가?
- business truth가 자동으로 더 정확해지는가?
- application downstream contract도 같이 바뀌어야 하는가?

## 4.7 Validation boundary

| Evidence | 말할 수 있는 것 | 말할 수 없는 것 |
| --- | --- | --- |
| `--preview` | local Pydantic contract | server-side structured generation |
| live parsed response | current API/SDK가 typed result를 반환함 | classification이 business truth임 |
| Pydantic validation | representation이 schema에 맞음 | authorization / policy correctness |

신뢰도는 "typed이니 안전"이라고 말하는 데서 생기지 않는다. **어디까지 검증했는지 좁게 말하는 것**에서 생긴다.

## 4.8 흔한 오해

### "Structured Outputs = valid JSON"

핵심은 supplied schema와 typed parsing contract다.

### "Pydantic instance면 사실도 맞다"

Type validity와 semantic correctness는 다르다.

### "`output_parsed is None`이면 HTTP request가 실패했다"

먼저 response lifecycle과 content state를 본다.

### "refusal은 malformed schema output이다"

Refusal은 별도 output state다.

### "schema가 있으니 business validation은 필요 없다"

Schema와 domain authority는 다른 책임이다.

## 4.9 Practice

### A. Gate classification

다음을 가장 먼저 처리할 gate에 배치한다.

```text
HTTP 429
response.status == incomplete
content가 refusal
output_parsed is None
parsed priority는 high지만 SLA rule상 medium
```

### B. Schema repair

```python
class Job(BaseModel):
    action: str
    retry: str
```

실제 contract:

```text
action = create | cancel | inspect
retry = boolean
```

Type을 강화하고 **무엇이 구조적으로 보장되었고 무엇은 여전히 business check인지** 설명한다.

### C. Boundary design

다음 code를 review한다.

```python
result = client.responses.parse(...).output_parsed
save_to_database(result)
```

Application requirement를 하나 정하고, `save_to_database` 전에 필요한 최소 gate만 설계한다. 방어 check를 무작정 늘리지
않는다.

## Assessment checkpoint

다음을 독립적으로 할 수 있으면 통과한다.

1. Structured Outputs의 data flow를 `schema → response state → content → parsed value → business rule`로 추적한다.
2. refusal / incomplete / schema parsing / business-invalid를 서로 다른 failure로 분류한다.
3. schema가 보장하는 것과 보장하지 않는 것을 설명한다.
4. Preview와 live evidence의 validation boundary를 구분한다.
