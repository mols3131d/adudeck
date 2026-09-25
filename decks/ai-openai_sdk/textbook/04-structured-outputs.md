# 4. Structured Outputs: text를 typed data로 받는다

Model output이 다음 application step의 input이 된다면 단순한 free text보다 강한 contract가 필요할 수 있다.

이번 unit에서는 Pydantic model을 직접 schema로 사용한다.

## 4.1 먼저 실행한다

```bash
uv run playground/structured_output.py
```

Playground의 중심은 다음 code다.

```python
class TicketClassification(BaseModel):
    category: Literal["bug", "question", "request"]
    priority: Literal["low", "medium", "high"]
    summary: str

response = client.responses.parse(
    model=model,
    input="The checkout button freezes after I submit my card.",
    text_format=TicketClassification,
)

print(response.output_parsed)
```

처음에는 `output_parsed`가 어떤 Python object인지 확인한다.

## 4.2 Schema가 무엇을 제한하는가

```python
priority: Literal["low", "medium", "high"]
```

이 field는 허용 representation을 제한한다.

하지만 다음은 별개다.

```text
"high"라는 값이 schema-valid한가?
!=
실제 business rule상 high priority가 맞는가?
```

Structured Outputs는 representation contract를 강화하지만 domain truth를 대신하지 않는다.

## 4.3 직접 schema를 바꾼다

다음 한 줄만 바꾼다.

Before:

```python
priority: Literal["low", "medium", "high"]
```

After:

```python
priority: Literal["normal", "urgent"]
```

실행 전에 예측한다.

- parsed value가 가질 수 있는 범위는 어떻게 바뀌는가?
- business correctness가 자동으로 좋아지는가?
- downstream code가 기존 enum을 가정하고 있다면 무엇이 깨질 수 있는가?

다시 실행하고 관찰한다.

## 4.4 Typed result 전에 봐야 할 상태

`output_parsed`만 무조건 사용하지 않는다.

개념적으로 다음 gate를 구분한다.

```text
SDK/API call
→ response lifecycle
→ content state
→ parsed value
→ business rule
```

대표적인 서로 다른 상태:

```text
HTTP/API failure
response incomplete/failed
refusal
parsed value 없음
schema-valid하지만 business-invalid
```

이것을 전부 "parse 실패"라고 부르면 root cause를 잃는다.

## 4.5 Response state를 직접 더 본다

playground에 다음 줄을 추가한다.

```python
print(response.status)
print(response.incomplete_details)
print(response.error)
```

그 다음 `response.output`을 순회해 content type도 확인해 본다.

이번 단계의 목표는 모든 output type을 외우는 것이 아니라
**typed value를 사용하기 전에 어떤 state를 확인할 수 있는지** 찾는 것이다.

## 4.6 `BaseModel`은 API-facing contract일 뿐일 수 있다

Application이 destructive action을 수행한다면 보통 다음 boundary가 더 필요하다.

```text
model-facing structured result
→ business validation
→ authorization / policy
→ domain action
```

Schema-valid output을 바로 database write나 payment action으로 연결하지 않는다.

## Practice

다음 model을 더 정확하게 고친다.

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

Type을 고친 뒤, 여전히 schema가 보장하지 못하는 business rule 하나를 적는다.

## Checkpoint

다음 code를 review한다.

```python
result = client.responses.parse(...).output_parsed
save_to_database(result)
```

`save_to_database` 전에 필요한 최소 gate를 설계한다.
check를 많이 넣는 것이 아니라, 서로 다른 failure boundary를 필요한 만큼만 분리하는 것이 목표다.
