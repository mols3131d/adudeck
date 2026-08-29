# 1. Client → Arguments → Request → Response

첫 SDK 호출에서 가장 중요한 것은 method 이름을 외우는 것이 아니다. **내 Python process 안의 값이 어디까지 local
state이고, 어느 순간 network request가 되며, 돌아온 data를 SDK가 어떤 Python object로 바꾸는지** 구분하는 것이다.

이번 chapter의 목표는 한 번의 Responses API 호출을 다음 data flow로 설명하는 것이다.

```text
Python values
   ↓
application call arguments
   ↓
OpenAI client + SDK serialization
   ↓
HTTP request ───────────────→ OpenAI API
                              │
                              ↓
                        model processing
                              │
HTTP response ←───────────────┘
   ↓
SDK parsing
   ↓
typed Response object
   ↓
response id / request id / output / usage
```

이 그림에서 가장 중요한 경계는 두 개다.

1. **application → SDK/API boundary** — 내가 만든 Python 값이 endpoint call의 arguments가 되고, SDK가 network request를
   수행한다.
2. **API/SDK → application boundary** — HTTP response가 SDK의 typed `Response` object로 바뀌고 application이 필요한
   field를 읽는다.

## 1.1 `OpenAI()`는 model이 아니다

다음 두 줄은 비슷해 보이지만 완전히 다른 일을 한다.

```python
from openai import OpenAI

client = OpenAI()
response = client.responses.create(
    model="...",
    input="Explain a Python tuple.",
)
```

`OpenAI()`는 **API client object를 만든다.** authentication, base URL, timeout/retry 같은 request 실행 configuration과
transport가 이 client를 통해 사용된다. 이 시점에는 아직 model에게 input을 보내지 않았다.

실제 model interaction은 `client.responses.create(...)` 같은 endpoint method를 호출할 때 시작된다.

- `client` — API와 통신하기 위한 application-side object
- `responses` — Responses API resource에 접근하는 surface
- `create(...)` — 새 response를 요청하는 network operation
- `response` — server data를 SDK가 typed Python object로 표현한 결과

여기서 두 실패를 구분해야 한다. `OPENAI_API_KEY` 같은 필수 local configuration이 없으면 client construction에서 실패할
수 있다. 반면 설정된 credential이 유효하지 않거나 API가 request를 거절하는 문제는 network call 단계에서 드러난다.
**local configuration failure와 remote API rejection은 같은 실패가 아니다.**

## 1.2 API key는 code가 아니라 process configuration이다

SDK는 기본적으로 `OPENAI_API_KEY` environment variable을 사용할 수 있다.

```bash
export OPENAI_API_KEY='...'
```

핵심은 convenience가 아니라 **ownership boundary**다. source code는 secret 값을 소유하지 않고 실행 environment가
credential을 공급한다.

다음 방식은 피한다.

```python
client = OpenAI(api_key="sk-...")
```

학습용 repository라도 실제 key를 file, commit, notebook output, screenshot에 남기면 안 된다. Git history는 file을 나중에
삭제해도 남을 수 있다.

이번 lab의 `--preview` mode는 API key도 SDK installation도 필요하지 않다. 먼저 application-owned data만 관찰한 뒤 실제
network call로 넘어간다.

## 1.3 endpoint call arguments는 HTTP request 그 자체가 아니다

첫 실습에서 application이 만드는 값은 세 field뿐이다.

```python
call_args = {
    "model": model,
    "instructions": instructions,
    "input": prompt,
}
```

각 field의 책임을 분리해 보자.

### `model`

어떤 model을 사용할지 지정한다. model identifier는 version-sensitive하므로 application에서는 configuration으로 분리하는
편이 좋다. lab은 `OPENAI_MODEL` environment variable로 override할 수 있게 한다.

### `instructions`

response가 따라야 할 상위 수준의 행동 지침이다. lab에서는 답변 형식을 짧은 bullet로 제한한다.

### `input`

이번 response에서 처리할 user-side input이다. 지금은 문자열이지만 이후 unit에서는 구조화된 input item과 이전 output
item까지 다룬다.

`call_args`는 **application이 SDK public method에 넘길 값**이다. 실제 HTTP body는 SDK가 defaults와 serialization을
적용한 뒤 만들어진다. 따라서 `call_args`를 출력했다고 해서 wire-level payload를 관찰한 것은 아니다.

이 구분이 중요한 이유는 이후 debugging에서 “내 code가 잘못된 argument를 만들었다”와 “SDK/network/API boundary에서
문제가 생겼다”를 분리해야 하기 때문이다.

## 1.4 Worked trace: 값의 owner가 어떻게 바뀌는가

다음 호출을 생각해 보자.

```python
call_args = {
    "model": "gpt-5.6-luna",
    "instructions": "Answer in one short sentence.",
    "input": "What is a Python tuple?",
}

client = OpenAI()
response = client.responses.create(**call_args)
text = response.output_text
```

실행 흐름을 한 줄씩 추적하면 다음과 같다.

| Step | 상태 / 동작 | 누가 현재 값을 소유하는가? | 지금 확인할 수 있는 것 |
| --- | --- | --- | --- |
| 1 | `call_args` 생성 | application | 세 argument의 정확한 Python 값 |
| 2 | `OpenAI()` | application + SDK client configuration | client construction 성공/실패 |
| 3 | `responses.create(**call_args)` 시작 | SDK가 arguments를 받아 request 수행 | network boundary를 건넌다는 사실 |
| 4 | API processing | remote API | application에서는 내부 model processing을 직접 관찰하지 못함 |
| 5 | `response` 반환 | application이 SDK typed object를 보유 | type, IDs, output items, usage |
| 6 | `response.output_text` 읽기 | application | text output의 convenience view |

여기서 Step 1의 dictionary와 Step 5의 `Response`는 서로 다른 종류의 state다. Step 1은 내가 호출 전에 만든 값이고, Step
5는 외부 API와 상호작용한 뒤 새로 얻은 값이다.

또한 Step 3의 network boundary를 통과했다고 해서 API 내부 processing 과정 전체를 관찰한 것은 아니다. 학습에서
**관찰한 것과 추론한 것을 분리하는 습관**을 유지해야 한다.

## 1.5 먼저 network 없이 application arguments를 본다

Deck directory에서 실행한다.

```bash
python lab/request_response.py --preview
```

실행 전에 다음을 prediction한다.

1. stdout에 어떤 세 개의 endpoint argument가 나타날까?
2. `OPENAI_API_KEY`가 없어도 왜 성공할까?
3. `openai` package가 설치되어 있지 않아도 왜 실행 가능한가?
4. 이 output만 보고 실제 HTTP body가 정확히 같다고 결론 내릴 수 없는 이유는 무엇인가?

lab은 live-call code의 `openai` import를 preview boundary 뒤에 둔다. 따라서 preview에서는 `build_call_args()`와 stdout
출력 같은 local Python logic만 실행한다.

이 실험으로 검증할 수 있는 것은 **application-owned argument construction**이다. SDK serialization, authentication,
transport, server behavior는 아직 검증하지 않았다.

## 1.6 `responses.create()`가 network boundary를 넘는다

실제 request를 보내려면 environment에 key를 둔 뒤 다음을 실행한다.

```bash
export OPENAI_API_KEY='...'
uv run lab/request_response.py
```

`uv`는 script 상단의 PEP 723 metadata를 읽어 `openai>=3,<4` dependency를 준비한다. 이 version range는 이 deck의 v3
public surface를 사용하면서 v4 breaking change가 자동으로 섞이는 것을 막는 boundary다.

핵심 code는 다음과 같다.

```python
client = OpenAI()
response = client.responses.create(**call_args)
```

두 번째 줄에서 SDK는 keyword arguments를 받아 request를 serialize하고 API로 전송한다. synchronous client이므로 call이
완료되거나 exception이 발생할 때까지 현재 control flow는 다음 줄로 넘어가지 않는다.

> 정상적인 live 실행에서 `response` 변수가 생겼다면 local argument construction을 넘어 실제 API request/response
> boundary를 통과한 것이다.

이 문장은 “모든 application 기대가 충족되었다”는 뜻은 아니다. API call은 성공했지만 원하는 output type이 없거나,
application이 response를 잘못 해석할 수도 있다. transport/API/application failure를 더 세밀하게 나누는 것은 Unit 3에서
다룬다.

## 1.7 typed `Response`를 직접 관찰한다

lab은 live call 뒤 다음 정보를 보여준다.

```python
print(type(response).__name__)
print(response.id)
print(response._request_id)
print(response.model)
print([item.type for item in response.output])
print(response.output_text)
print(response.usage.to_dict())
```

`response`는 문자열이 아니라 SDK의 typed model이다.

- Python type — SDK가 parsing한 object가 단순 `dict`가 아니라 typed `Response`라는 evidence
- `id` — API가 생성한 **Response resource**의 identifier
- `_request_id` — HTTP response header의 request ID를 SDK가 공개한 debugging identifier
- `model` — 실제 response에 기록된 model identifier
- `output` — message, function call 등 여러 type의 output item을 담는 구조
- `output_text` — text output을 편하게 읽기 위한 SDK convenience property
- `usage` — input/output token usage 같은 metering metadata

`response.id`와 `response._request_id`는 역할이 다르다. 전자는 Response resource를 식별하고, 후자는 API request를
추적·debugging하는 데 사용한다. `_request_id`는 underscore prefix지만 OpenAI Python SDK가 public property로 문서화한
예외다.

`output_text`도 response 전체가 아니다. text application에는 편리하지만 function calling처럼 다른 output item이 등장하면
`response.output`을 보고 item type을 판단해야 한다. 그래서 lab은 `output_types`를 별도로 출력한다.

전체 typed response를 dictionary로 펼쳐 보고 싶다면 다음을 실행한다.

```bash
uv run lab/request_response.py --full-response
```

이것도 raw HTTP body가 아니다. `response.to_dict()`로 **이미 parsing된 SDK object**를 Python dictionary로 바꾼 값이다.

## 1.8 Before / after를 같은 축에서 비교한다

실행 전에 왼쪽을 알고 있고, live call 뒤 오른쪽을 새로 관찰할 수 있다.

| Before call: application-owned | After call: API/SDK-derived |
| --- | --- |
| `model` argument | `response.model` |
| `instructions` | output behavior에 반영된 결과 |
| `input` | generated output item / `output_text` |
| 없음 | Python `Response` type |
| 없음 | `response.id` |
| 없음 | `response._request_id` |
| 없음 | `response.output[*].type` |
| 없음 | `response.usage` |

이 표는 request field가 그대로 echo된다는 뜻이 아니다. **call 전 state와 외부 상호작용 뒤 새로 생긴 observable state를
분리하는 도구**다.

## 1.9 한 조건만 바꾸고 비교한다

첫 variation에서는 prompt와 model을 유지하고 `instructions`만 바꾼다.

```bash
uv run lab/request_response.py \
  --instructions 'Answer with one short sentence.'
```

실행 전에 prediction한다.

- application arguments의 어떤 field만 달라지는가?
- `response.id`와 `_request_id`는 이전 실행과 같을까?
- `python_type`은 달라질 이유가 있는가?
- output text의 형식은 어떻게 달라질 가능성이 있는가?

이 실험은 “instructions가 정확한 format을 항상 보장한다”는 causal proof가 아니다. model generation에는 변동성이 있다.
확실히 통제한 것은 **application argument 한 dimension을 바꿨다는 사실**이다. live output 차이는 그 변경과 model
generation을 함께 거친 결과이므로 지나치게 강한 인과 결론을 내리지 않는다.

## 1.10 흔한 잘못된 mental model

### “SDK가 답을 생성한다”

SDK는 client library다. Python 값을 API request로 전달하고 response를 typed object로 다루기 쉽게 한다. model
processing은 remote API boundary 뒤에서 일어난다.

### “`call_args`가 실제 HTTP payload다”

아니다. `call_args`는 public endpoint method에 넘길 application-side arguments다. SDK serialization 이후의 wire-level
request와 구분한다.

### “`output_text`가 response 전체다”

`output_text`는 text convenience view다. full response에는 identifiers, usage, 여러 output item이 있다.

### “`response.id`와 `_request_id`는 같은 ID다”

둘 다 한 interaction에서 관찰되지만 식별 대상이 다르다. 하나는 Response resource, 다른 하나는 API request tracing이다.

### “client가 만들어졌으니 authentication도 검증됐다”

client construction 성공과 remote API authentication 성공은 다른 단계다.

### “예제의 model ID는 영구적인 상수다”

model catalog는 version-sensitive하다. lab default는 학습 편의를 위한 calibration 값이며 application에서는 configuration
boundary를 두고 현재 공식 model catalog를 확인해야 한다.

## Practice

### A. Trace

다음 code에서 각 줄을 **local construction**, **client construction**, **network operation**,
**server/API-derived state read** 중 하나로 분류한다.

```python
client = OpenAI()
call_args = {"model": model, "input": prompt}
response = client.responses.create(**call_args)
request_id = response._request_id
text = response.output_text
```

각 분류에 한 문장 근거를 쓴다. 실패 가능성도 표시한다. 예를 들어 `OpenAI()`와 `responses.create()`가 실패한다면 같은
종류의 실패인지 설명한다.

### B. Predict → Observe

`--preview`를 두 번 실행한다. 두 번째 실행에서는 `--prompt`만 변경한다.

실행 전에 어떤 JSON field가 달라질지 적고 실제 output과 비교한다. 그 뒤 다음 두 목록을 만든다.

- 이 실험으로 **검증한 것** 2개
- 이 실험으로 **검증하지 못한 것** 2개

### C. Inspect

live call이 가능한 경우 기본 실행에서 `python_type`, `response_id`, `request_id`, `output_types`를 기록한다. 이어서
`--full-response`로 실행하고 다음을 설명한다.

1. `output_text`가 full response의 어떤 부분만 편리하게 보여주는가?
2. `response.id`와 `_request_id`는 각각 무엇을 식별하는가?
3. `response.to_dict()`가 raw HTTP response body가 아닌 이유는 무엇인가?

### D. Debug

아래 주장을 반박한다.

> `response.output_text`가 비어 있으면 OpenAI API 호출 자체가 실패한 것이다.

“network/API request 성공 여부”와 “application이 기대한 output content/type”이 왜 다른 판단인지 설명한다.
`response.output`에 text가 아닌 item이 있을 가능성도 고려한다.

### E. Transfer

다른 개발자가 다음 helper를 작성했다.

```python
def ask(client, prompt):
    response = client.responses.create(model="gpt-5.6-luna", input=prompt)
    return response.output_text
```

이 함수가 간단한 text application에는 쓸 수 있지만 SDK boundary를 관찰하거나 debugging하기에는 어떤 정보가 사라지는지
세 가지를 고른다. 그중 하나를 보존하도록 함수의 return shape를 바꾸고, 왜 그 정보를 선택했는지 설명한다.

완성 code보다 **어떤 information boundary를 application이 유지해야 하는가**를 판단하는 것이 목표다.

## Assessment checkpoint

이 chapter는 다음 두 과제를 독립적으로 수행할 수 있을 때 통과한다.

### 1. Execution map

처음 보는 `responses.create()` 기반 5~8줄짜리 program을 보고 각 줄을 다음 범주에 배치한다.

- application-owned state construction
- local client configuration
- network/API operation
- API/SDK-derived state observation

각 경계에서 가능한 실패를 최소 하나씩 설명한다. 단, 아직 배우지 않은 구체적인 retry policy를 외울 필요는 없다.

### 2. Evidence boundary

누군가 `--preview` output만 보여주며 “OpenAI API request가 정상적으로 전송되는 것을 검증했다”고 주장한다고 가정한다.
다음 세 요소를 포함해 반박한다.

- 실제로 검증된 것
- 아직 검증되지 않은 것
- live call 뒤 추가로 관찰할 evidence 두 가지

평가 기준은 용어 암기가 아니라 **state owner와 observation boundary를 일관되게 추적하는가**다.

다음 unit에서는 이 mental model을 유지한 채 `response.output` item 구조를 더 깊게 보고, application이 history/output
items를 직접 운반하는 방식, `previous_response_id` response lineage, durable Conversations API의 state ownership을
비교한다.

## References

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Responses API reference](https://platform.openai.com/docs/api-reference/responses)
- [Conversation state](https://platform.openai.com/docs/guides/conversation-state)
