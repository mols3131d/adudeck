# 0. Introduction: Python code와 API 사이의 경계

OpenAI Python SDK를 처음 배울 때 가장 먼저 필요한 것은 큰 architecture가 아니다.
**한 번의 호출이 어디서 시작하고 어디서 끝나는지** 볼 수 있으면 된다.

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="gpt-5.5",
    input="Explain a Python tuple in one sentence.",
)

print(response.output_text)
```

이 짧은 code에는 이미 deck 전체에서 반복할 구조가 들어 있다.

```text
Python input
→ OpenAI client
→ responses.create(...)
→ network/API
→ Response object
→ application이 필요한 값 읽기
```

## 0.1 먼저 세 object만 구분한다

### `client`

```python
client = OpenAI()
```

API와 통신하기 위한 Python object다. model 자체가 아니다.

### `response`

```python
response = client.responses.create(...)
```

이 줄에서 실제 Responses API operation이 시작된다. 성공하면 SDK가 typed `Response` object를 돌려준다.

### `response.output_text`

```python
print(response.output_text)
```

Response 전체가 아니라 text output을 편하게 읽기 위한 view다.

처음에는 이 세 가지면 충분하다. Response의 세부 item, request ID, retry, schema, tool call은 필요해질 때 추가한다.

## 0.2 이 deck의 학습 방식

각 playground는 가능한 한 작은 runnable file로 시작한다.

chapter를 읽을 때 다음 순서를 지킨다.

1. code를 실행하기 전에 결과를 예상한다.
2. 핵심 줄을 찾는다.
3. 한 가지를 직접 수정한다.
4. 다시 실행한다.
5. 바뀐 결과를 설명한다.

예를 들어 Unit 1에서는 prompt를 직접 바꾼다.

```python
input="Explain a Python tuple in one sentence."
```

다음처럼 바꾸고 다시 실행한다.

```python
input="Explain a Python dictionary in one sentence."
```

이 작은 수정은 CLI flag를 외우는 것보다 중요한 것을 보여준다.
**어떤 Python 값이 request를 바꾸는지 직접 확인할 수 있다.**

## 0.3 관찰한 것과 추론한 것을 구분한다

실습에서는 output을 얻는 것보다 무엇을 실제로 봤는지가 중요하다.

예를 들어 `response.output_text`가 출력되었다면 다음은 직접 관찰했다.

- Python code가 SDK call까지 실행됐다.
- API call이 성공해 `Response`가 반환됐다.
- text convenience view를 읽었다.

하지만 이것만으로 API 내부 model processing 과정을 본 것은 아니다.

이 구분은 이후 retry, conversation state, Structured Outputs, Function Calling에서 더 중요해진다.

## 0.4 Learning path

```text
1. 한 번 호출한다.
2. Response를 조금 더 들여다본다.
3. 두 호출 사이의 context를 연결한다.
4. 실패와 retry를 관찰한다.
5. text 대신 typed data를 받는다.
6. model이 제안한 tool call을 application이 실행한다.
```

각 단계는 이전 단계의 code와 mental model을 조금씩 확장한다.

먼저 [00-environment.md](00-environment.md)에서 실행 환경을 준비한 뒤
[01-client-request-response.md](01-client-request-response.md)로 이동한다.
