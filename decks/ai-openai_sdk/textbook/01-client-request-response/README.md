# 1. Client → Request → Response

이번 unit의 목표는 `responses.create()`를 많이 외우는 것이 아니다.

**한 번의 호출에서 내가 만든 Python 값과 API가 돌려준 값을 구분하는 것**이다.

## 1.1 가장 작은 runnable example

[request_response.py](request_response.py)를 연다.

핵심 code는 다음 정도다.

```python
client = OpenAI()

response = client.responses.create(
    model=model,
    input="Explain the difference between a Python list and tuple in one sentence.",
)

print(response.output_text)
```

먼저 실행한다.

```bash
uv run textbook/01-client-request-response/request_response.py
```

### 실행 전 prediction

- network call을 일으키는 줄은 어디인가?
- `response`가 생기기 전까지 application이 이미 알고 있는 값은 무엇인가?
- `response.output_text`는 request 전에 알 수 있는 값인가?

## 1.2 `OpenAI()`와 `responses.create()`는 다른 일이다

```python
client = OpenAI()
```

`client`는 API 통신 configuration과 transport를 사용하는 Python object다.

```python
response = client.responses.create(...)
```

이 endpoint call이 request를 수행한다.

따라서 다음 두 실패는 같은 단계가 아니다.

```text
client construction 문제
!=
remote API request 문제
```

예를 들어 local configuration이 부족하면 client를 만드는 단계에서 막힐 수 있고,
credential이 remote API에서 거절되면 request 단계에서 드러난다.

## 1.3 첫 수정: input을 직접 바꾼다

playground의 `input=` 값만 바꾼다.

Before:

```python
input="Explain the difference between a Python list and tuple in one sentence."
```

After:

```python
input="Explain a Python dictionary in one sentence."
```

다시 실행한다.

```bash
uv run textbook/01-client-request-response/request_response.py
```

설명할 것은 단순하다.

- 어떤 Python value를 바꿨는가?
- 어떤 output이 새로 생겼는가?
- 바꾸지 않은 것은 무엇인가?

CLI option을 추가하지 않는다. 이번 실습의 조작 대상은 request argument 자체다.

## 1.4 Response가 문자열 하나는 아니다

처음에는 `output_text`만 읽었다.
이제 playground에 다음 줄을 **직접 추가**한다.

```python
print(type(response).__name__)
print(response.id)
print(response._request_id)
print([item.type for item in response.output])
```

다시 실행한다.

예상할 것:

```text
Response의 Python type
Response resource ID
request tracing ID
output item type들
```

`response.id`와 `_request_id`는 같은 identifier가 아니다.

```text
response.id
→ Response resource

response._request_id
→ HTTP/API request tracing
```

`output_text`도 Response 전체가 아니다. Function Calling unit에서는 `response.output` 안에 text가 아닌 item이 나타난다.

## 1.5 usage를 읽어 본다

다음 줄도 추가해 본다.

```python
print(response.usage)
```

여기서 중요한 것은 모든 field를 외우는 것이 아니다.
**request 이후에만 생기는 API/SDK-derived state가 늘어났다는 것**을 확인한다.

## 1.6 Worked trace

```text
1. model/input Python value가 존재한다.
2. OpenAI client를 만든다.
3. responses.create(...)를 호출한다.
4. SDK가 API request를 수행한다.
5. Response object가 돌아온다.
6. application이 필요한 field를 읽는다.
```

이 trace에서 Step 3 전후가 중요한 boundary다.

## 1.7 흔한 오해

### "`OpenAI()`가 답을 만든다"

아니다. client를 만든다. model interaction은 endpoint call에서 시작된다.

### "`output_text`가 Response 전체다"

아니다. text convenience view다.

### "`response.id`와 `_request_id`는 같은 ID다"

아니다. 하나는 resource, 다른 하나는 request tracing이다.

### "model ID는 영구적인 상수다"

아니다. model catalog는 version-sensitive하다. playground는 `OPENAI_MODEL`로 override할 수 있다.

## Practice

다음 code를 실행하지 않고 먼저 분류한다.

```python
client = OpenAI()
response = client.responses.create(model=model, input=prompt)
text = response.output_text
request_id = response._request_id
```

각 줄을 다음 중 하나로 분류하고 이유를 한 문장씩 적는다.

```text
local client construction
network/API operation
API/SDK-derived state read
```

## Checkpoint

새 Python file을 하나 만들고 다음 조건을 만족시킨다.

- `OpenAI()` client를 만든다.
- `responses.create()`로 한 번 호출한다.
- `output_text`를 출력한다.
- Response resource ID와 request ID를 모두 출력한다.
- 두 ID가 무엇을 식별하는지 설명한다.

다음 unit에서는 한 번의 call이 아니라 **두 call 사이에 context를 어떻게 이어 주는지** 다룬다.
