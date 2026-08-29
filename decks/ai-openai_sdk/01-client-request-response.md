# 1. Client → Request → Response

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

`OpenAI()`는 **API client object를 만든다.** 여기에는 authentication, base URL, timeout/retry 같은 request 실행에 필요한
configuration과 transport가 연결된다. 이 시점에는 model에게 prompt를 보내지 않았다.

실제 model interaction은 `client.responses.create(...)` 같은 endpoint method를 호출할 때 시작된다. 이 call의 arguments가
request body와 request behavior를 구성하고, SDK는 그것을 API가 이해할 수 있는 형태로 serialize해 network를 건넌다.

따라서 다음 mental model을 유지하면 좋다.

- `client` — API와 통신하기 위한 application-side object
- `responses` — Responses API resource에 접근하는 surface
- `create(...)` — 새 response를 요청하는 network operation
- `response` — server가 보낸 data를 SDK가 typed Python object로 표현한 결과

“`OpenAI()`를 만들었으니 이미 연결되었다”라고 생각하면 error boundary를 잘못 잡기 쉽다. client construction이 성공해도
실제 request에서 authentication, network, quota, API validation 문제가 발생할 수 있다. 반대로 API key 자체가 설정되지 않은
경우처럼 필수 local configuration이 빠져 있으면 client construction 단계에서 더 일찍 실패할 수도 있다. **local
configuration failure와 remote API rejection은 같은 실패가 아니다.**

## 1.2 API key는 code가 아니라 process configuration이다

SDK는 기본적으로 `OPENAI_API_KEY` environment variable을 사용할 수 있다.

```bash
export OPENAI_API_KEY='...'
```

핵심은 convenience가 아니라 **ownership boundary**다. source code는 “어떤 secret 값인지”를 소유하지 않고, 실행
environment가 credential을 공급한다.

다음 방식은 피한다.

```python
client = OpenAI(api_key="sk-...")
```

학습용 repository라도 실제 key를 file, commit, notebook output, screenshot에 남기면 안 된다. Git history는 나중에 file을
삭제해도 credential이 남을 수 있다.

이번 lab의 `--preview` mode는 API key도 SDK installation도 필요하지 않다. 먼저 application이 endpoint method에 넘길 값을
local data로 관찰한 다음 실제 network call로 넘어간다.

## 1.3 endpoint call arguments는 명시적인 data다

첫 실습에서 사용하는 application-side arguments는 세 field만 둔다.

```python
request = {
    "model": model,
    "instructions": instructions,
    "input": prompt,
}
```

각 field의 책임을 분리해 보자.

### `model`

어떤 model endpoint behavior를 사용할지 지정한다. model identifier는 시간이 지나며 바뀔 수 있으므로 application에서는
configuration으로 분리하는 편이 좋다. lab은 `OPENAI_MODEL` environment variable로 override할 수 있게 한다.

### `instructions`

response가 따라야 할 상위 수준의 행동 지침을 전달한다. 예제에서는 답변 형식을 짧은 bullet로 제한한다.

### `input`

이번 response에서 처리할 실제 user-side input이다. 간단한 문자열도 가능하고, 이후에는 더 구조화된 input item을 다루게
된다.

여기서 중요한 점은 “prompt”라는 한 단어로 모든 것을 뭉개지 않는 것이다. SDK를 다룰 때는
**어떤 Python 값이 어떤 endpoint argument로 들어가는가**를 추적해야 한다. 그래야 structured output, tool calling,
multi-turn state가 추가되어도 data flow를 잃지 않는다.

다만 이 dictionary 자체를 곧바로 “실제 HTTP request body”라고 부르면 안 된다. 이 값은 application이 SDK public method에
넘길 arguments다. 그 뒤 SDK가 defaults, serialization, transport behavior를 적용한다. **application arguments를 관찰한 것과
wire-level HTTP payload를 관찰한 것은 다른 validation level**이다.

## 1.4 먼저 network 없이 application arguments를 본다

Deck directory에서 실행한다.

```bash
python lab/request_response.py --preview
```

예상해야 할 것은 model의 답변이 아니다. 아직 SDK import와 network request를 수행하지 않기 때문이다.

실행 전에 다음을 prediction해 보자.

1. stdout에 어떤 세 개의 endpoint argument가 나타날까?
2. `OPENAI_API_KEY`가 없어도 왜 성공할까?
3. `openai` package가 설치되어 있지 않아도 preview가 가능한 이유는 무엇일까?
4. 이 output만 보고 실제 HTTP body가 정확히 같다고 결론 내릴 수 없는 이유는 무엇일까?

lab은 live-call code의 `openai` import를 preview boundary 뒤에 둔다. 따라서 preview에서는 endpoint arguments를 만드는 local
Python logic만 실행한다.

이 구조는 작은 testing boundary도 보여준다. API를 실제 호출하지 않고도 **application-owned request-building logic**은
deterministic하게 검증할 수 있다. 반면 SDK serialization, authentication, transport, server behavior는 아직 검증하지 않았다.

## 1.5 `responses.create()`가 경계를 넘는다

실제 request를 보내려면 environment에 key를 둔 뒤 다음을 실행한다.

```bash
export OPENAI_API_KEY='...'
uv run lab/request_response.py
```

`uv`는 script 상단의 PEP 723 metadata를 읽어 `openai>=3,<4` dependency를 준비한다. 이 version range는 이 deck의 v3
public surface calibration을 유지하면서 v4 breaking change가 자동으로 섞이는 것을 막기 위한 학습용 boundary다.

실행 흐름을 code 관점에서 추적하면 다음과 같다.

```python
client = OpenAI()
response = client.responses.create(**request)
```

첫 줄은 client를 구성한다. 두 번째 줄에서 request dictionary의 key가 keyword argument가 되고, SDK가 request를
serialize해 API로 전송한다. synchronous client이므로 call이 완료되거나 exception이 발생할 때까지 현재 control flow는
다음 줄로 넘어가지 않는다.

여기까지의 invariant는 다음과 같다.

> 정상적인 live 실행에서 `response` 변수가 생겼다면 `responses.create()`는 local argument construction을 넘어 실제 API
> request/response boundary를 통과했다.

나중에 retry나 timeout을 다룰 때도 이 boundary가 기준이 된다. client construction 전에 실패한 것, transport에서 실패한 것,
API가 status code로 거절한 것, response를 받은 뒤 application code가 잘못 처리한 것은 서로 다른 문제다.

## 1.6 response는 문자열 하나가 아니다

lab은 우선 다음 정보를 보여준다.

```python
print(response.id)
print(response._request_id)
print(response.model)
print([item.type for item in response.output])
print(response.output_text)
print(response.usage.to_dict())
```

`response` 자체는 SDK의 typed model이다. 단순히 생성된 문자열만 담고 있지 않다.

- `id` — API가 생성한 **Response object**를 식별하는 값
- `_request_id` — HTTP response header의 request ID를 SDK가 공개한 debugging identifier
- `model` — 실제 response에 기록된 model identifier
- `output` — message, function call 등 여러 type의 output item을 담는 구조
- `output_text` — text output을 편하게 읽기 위한 SDK convenience property
- `usage` — input/output token usage 같은 metering metadata

여기서 `response.id`와 `response._request_id`를 같은 것으로 보면 안 된다. 전자는 API resource인 Response 자체의 identifier고,
후자는 API request를 추적·debugging하기 위한 identifier다. `_request_id`는 underscore prefix지만 OpenAI Python SDK가 public
property로 문서화한 예외다.

초보 코드에서는 `output_text`만 보고 끝내기 쉽다. text application이라면 편리하지만, SDK mental model은 여기서 멈추면 안
된다. function call이나 다른 output type을 다루기 시작하면
**full output structure를 순회하고 item type을 판단해야 하는 이유**가 생긴다. 그래서 lab은 먼저 `output_types`를 출력해
`output_text`가 response 전체가 아니라는 사실을 작은 관찰면으로 드러낸다.

다음 command로 SDK가 만든 typed response 전체를 dictionary 형태로 관찰할 수 있다.

```bash
uv run lab/request_response.py --full-response
```

이 option도 raw HTTP body를 보여주는 것이 아니다. `response.to_dict()`로 SDK의 typed response model을 Python dictionary로
바꾼 값을 보여준다. 실제 wire-level HTTP payload와 SDK object representation을 같은 것으로 취급하지 않는다.

## 1.7 request와 response를 같은 축에서 비교한다

실행 전에 다음 표의 왼쪽을 채우고, 실행 뒤 오른쪽을 관찰해 보자.

| Before call: 내가 소유한 값 | After call: API/SDK에서 돌아온 값 |
| --- | --- |
| `model` argument | `response.model` |
| `instructions` | output behavior에 반영된 결과 |
| `input` | generated output item / `output_text` |
| 없음 | `response.id` |
| 없음 | `response._request_id` |
| 없음 | `response.output[*].type` |
| 없음 | `response.usage` |

이 비교는 모든 field가 그대로 echo된다는 뜻이 아니다. **endpoint call 전에 application이 소유한 state와 외부 시스템과
상호작용한 뒤 새로 관찰 가능한 state를 구분하는 연습**이다.

특히 `response.id`, `_request_id`, `usage`는 application arguments를 만들 때 존재하지 않았다. live API boundary를 통과한 뒤
처음 관찰할 수 있다.

## 1.8 한 조건만 바꿔 비교한다

첫 variation에서는 prompt를 유지하고 `instructions`만 바꾼다.

```bash
uv run lab/request_response.py \
  --instructions 'Answer with one short sentence.'
```

그 전에 prediction한다.

- application arguments의 어떤 field만 달라지는가?
- `response.id`와 `_request_id`는 이전 실행과 같을까?
- output text의 형식은 어떻게 달라질 가능성이 있는가?
- `model`과 `input`은 바뀌지 않았다는 사실을 어떻게 확인할 수 있는가?

이 실험이 “instructions가 항상 정확히 원하는 format을 보장한다”는 인과 증명은 아니다. model generation은
deterministic하지 않을 수 있다. 여기서 확인하려는 것은 **application이 통제한 request dimension이 무엇인지**와
**각 live 실행이 별도 response/request identifiers를 만든다는 점**이다.

## 1.9 흔한 잘못된 mental model

### “SDK가 답을 생성한다”

SDK는 client library다. application의 Python object를 API request로 만들고 response를 typed object로 다루기 쉽게 해준다.
model processing은 remote API boundary 뒤에서 일어난다.

### “`--preview`가 실제 HTTP payload를 보여준다”

아니다. 이 lab의 preview는 SDK import 전에 application이 만들 endpoint call arguments만 보여준다. SDK serialization과
wire-level body를 관찰하려면 별도의 transport-level instrumentation이 필요하다.

### “`output_text`가 response 전체다”

`output_text`는 매우 편리하지만 convenience view다. full response에는 identifier, usage, output items 등 다른 state가
있다. 이 차이는 tool calling을 배울 때 중요해진다.

### “`response.id`와 `_request_id`는 같은 요청의 같은 ID다”

둘 다 한 live interaction에서 관찰할 수 있지만 ownership과 용도가 다르다. `response.id`는 Response resource를 식별하고,
`_request_id`는 API request를 추적·debugging하는 데 쓰인다.

### “client가 만들어졌으니 authentication도 검증됐다”

client construction과 successful API request는 다른 단계다. missing local configuration은 client construction에서 실패할 수
있고, 설정된 credential이 API에서 거절되는 문제는 request execution에서 드러날 수 있다.

### “예제에 나온 model ID는 영구적인 상수다”

model catalog는 version-sensitive하다. 학습용 default가 있더라도 application에서는 configuration boundary를 두고 공식
model catalog를 확인하는 습관이 필요하다.

## Practice

### A. Trace

다음 code에서 각 줄이 **local-only**, **network boundary**, **server-produced state read** 중 어디에 속하는지 표시한다.

```python
client = OpenAI()
request = {"model": model, "input": prompt}
response = client.responses.create(**request)
request_id = response._request_id
text = response.output_text
```

답만 적지 말고 그렇게 분류한 근거를 한 문장씩 쓴다. `OpenAI()`가 항상 local-only로 성공한다고 가정하지 말고, local
configuration failure가 가능한 지점도 별도로 표시한다.

### B. Predict → Observe

`--preview`를 두 번 실행한다. 두 번째 실행에서는 `--prompt`만 변경한다.

관찰 전에 어떤 JSON field가 달라질지 적고, 실제 output과 비교한다. network call이 없는데도 어떤 부분을 검증할 수
있었는지 설명한다. 이어서 **이 실험으로 검증할 수 없는 것 두 가지**도 적는다.

### C. Inspect

live call이 가능한 경우 먼저 기본 실행의 `response_id`, `request_id`, `output_types`를 기록한 뒤 `--full-response`로 다시
실행한다. `output_text`가 full response의 어느 정보만 편리하게 보여주는지 찾아 설명하고, `response.id`와 `_request_id`의
역할을 구분한다. response 전체를 그대로 외우는 것이 아니라, **현재 application이 왜 특정 field를 읽는지**를 기준으로
분류한다.

### D. Debug

아래 주장을 반박한다.

> `response.output_text`가 비어 있으면 OpenAI API 호출 자체가 실패한 것이다.

힌트: “network/API request의 성공 여부”와 “application이 기대한 output type/content”를 같은 조건으로 볼 수 있는지
생각한다. `response.output`에 text가 아닌 item이 있을 가능성도 함께 고려한다.

## Checkpoint

이 chapter를 통과하려면 다음을 code를 보지 않고 설명할 수 있어야 한다.

1. `OpenAI()`와 `client.responses.create(...)` 중 어느 지점이 실제 model request를 시작하는가?
2. `model`, `instructions`, `input`은 호출 전 누구의 state인가?
3. `--preview` output과 실제 HTTP request body를 같은 것으로 보면 안 되는 이유는 무엇인가?
4. `response.id`와 `response._request_id`는 각각 무엇을 식별하는가?
5. `output_text`와 full `response.output`을 구분해야 하는 이유는 무엇인가?
6. local preview와 live API call이 서로 다른 validation boundary를 갖는 이유는 무엇인가?

다음 unit에서는 이 mental model을 유지한 채 `response.output` item 구조를 더 깊게 보고, `previous_response_id`를 사용한
response lineage와 durable Conversations API의 state ownership이 어떻게 다른지 확장한다.

## References

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Responses API reference](https://platform.openai.com/docs/api-reference/responses)
- [Conversation state](https://platform.openai.com/docs/guides/conversation-state)
