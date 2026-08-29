# 3. Failure boundaries: 한 번의 Python call 안에서 몇 번의 HTTP attempt가 일어나는가

첫 chapter에서는 `client.responses.create(...)`가 network boundary를 넘는다는 것을 배웠다. 두 번째 chapter에서는 call 사이의 conversation state ownership을 구분했다.

이제 application이 실패를 다뤄야 한다.

여기서 가장 위험한 mental model은 다음이다.

```text
client.responses.create(...)
=
HTTP request 정확히 한 번
=
실패하면 exception 하나
```

OpenAI Python SDK에는 automatic retry가 있다. 따라서 application code에서는 endpoint method를 한 번 호출했어도 **transport layer에서는 여러 HTTP attempt가 일어날 수 있다.**

이번 chapter의 목표는 예외 class를 외우는 것이 아니라 다음 boundary를 추적하는 것이다.

```text
application call
   ↓
SDK client policy
   ├─ timeout
   └─ retry
   ↓
HTTP attempt 1
   ↓ failure
retry decision
   ↓
HTTP attempt 2 ...
   ↓
final typed Response
or
SDK exception
```

그리고 failure를 다음 세 범주로 분리한다.

```text
transport / timeout failure
API status failure
application interpretation failure
```

## 3.1 failure는 어느 boundary에서 발생했는가

다음 코드를 보자.

```python
response = client.responses.create(
    model="gpt-5.6-luna",
    input="Explain a Python generator.",
)
```

겉으로는 한 줄이지만 실패 지점은 여러 개다.

### local configuration

예:

```text
필수 credential configuration이 없음
잘못된 client option
```

network attempt 전에 실패할 수 있다.

### transport / timeout

예:

```text
DNS / connection 실패
network path 문제
request timeout
```

HTTP success/failure status를 정상적으로 받은 것이 아닐 수 있다.

### API status

server가 HTTP response를 반환했지만 success status가 아니다.

```text
400 bad request
401 authentication
429 rate limit
5xx server error
```

### application interpretation

HTTP request는 성공했고 typed `Response`도 받았지만 application이 기대한 condition이 충족되지 않을 수 있다.

```text
expected text item이 없음
structured result가 business rule을 만족하지 않음
application이 wrong field를 읽음
```

이 마지막 경우를 "API call failure"와 동일시하면 debugging boundary가 흐려진다.

## 3.2 SDK exception hierarchy는 failure boundary를 드러낸다

OpenAI Python SDK의 public error surface에서 중요한 구분은 다음이다.

```python
import openai

try:
    response = client.responses.create(...)
except openai.APIConnectionError:
    ...
except openai.RateLimitError:
    ...
except openai.APIStatusError:
    ...
```

개념적으로 읽는다.

```text
APIConnectionError
→ API success/error HTTP response를 정상적으로 받기 전 transport boundary 문제

APIStatusError
→ HTTP response를 받았고 status가 non-success

RateLimitError
→ APIStatusError 계열 중 429를 더 구체적으로 표현
```

status code마다 더 구체적인 subclass가 존재할 수 있지만 첫 mental model은 **response가 존재하는 status failure와 transport failure를 분리하는 것**이다.

## 3.3 timeout은 "느린 response"와 application control flow 사이의 계약이다

SDK client에는 timeout configuration이 있다.

```python
from openai import OpenAI

client = OpenAI(timeout=20.0)
```

또는 특정 request에 override할 수 있다.

```python
client.with_options(timeout=5.0).responses.create(...)
```

현재 SDK documentation은 timeout에서 `APITimeoutError`가 발생한다고 설명한다.

중요한 것은 default 숫자를 외우는 것이 아니다.

> application이 "얼마나 오래 기다릴 것인가"를 명시적으로 통제할 수 있고, timeout은 retry policy와 결합될 수 있다.

따라서 다음 문장은 틀릴 수 있다.

```text
request timeout = 5초
→ application call은 반드시 5초 안에 끝난다
```

왜냐하면 timeout이 발생한 attempt가 automatic retry 대상이라면 추가 attempt가 이어질 수 있기 때문이다.

실제 latency budget을 설계할 때는 **per-attempt timeout과 retry count를 함께** 본다.

## 3.4 automatic retry: Python call 한 번, HTTP attempt 여러 번

현재 OpenAI Python SDK documentation은 기본적으로 특정 failure를 두 번까지 자동 retry한다고 설명한다.

대표적인 retry 대상은 다음과 같다.

```text
connection errors
408 Request Timeout
409 Conflict
429 Rate Limit
>=500 server errors
```

`max_retries`로 client-level policy를 바꿀 수 있다.

```python
client = OpenAI(max_retries=0)
```

특정 call에서만 override할 수도 있다.

```python
client.with_options(max_retries=5).responses.create(...)
```

여기서 `max_retries=2`의 의미를 attempt count와 혼동하지 않는다.

```text
initial attempt 1회
+
retry 최대 2회
=
조건이 계속 실패하면 최대 3번의 attempt 가능
```

이것이 side effect와 latency를 생각할 때 중요하다.

## 3.5 worked trace: 429가 계속 반환되는 경우

application code는 한 번만 호출한다.

```python
client = OpenAI(max_retries=2)
response = client.responses.create(...)
```

server가 모든 attempt에 429를 반환한다고 가정한다.

```text
application
  |
  | responses.create() 1회
  v
SDK attempt 1
  |
  | 429
  v
retry decision
  |
  v
SDK attempt 2
  |
  | 429
  v
retry decision
  |
  v
SDK attempt 3
  |
  | 429
  v
RateLimitError
```

application stack에서는 마지막에 exception 하나를 받을 수 있지만 network 관점에서는 세 번의 request가 있었다.

따라서 다음 질문을 분리한다.

```text
application method call count
HTTP attempt count
API resource creation / side effect count
```

## 3.6 모든 status error가 자동 retry되는 것은 아니다

400 Bad Request를 생각하자.

request argument 자체가 invalid해서 server가 400을 반환했다면 같은 request를 그대로 반복하는 것은 일반적으로 문제를 해결하지 않는다.

현재 SDK default retry set에 400은 포함되지 않는다.

따라서 같은 `APIStatusError` 계열이어도 다음을 구분한다.

```text
400
→ request를 바꾸어야 할 가능성이 큼

429
→ rate limit / timing 문제이므로 retry policy가 관여할 수 있음

500
→ transient server failure일 수 있어 retry policy가 관여할 수 있음
```

"HTTP error면 전부 retry"는 좋은 policy가 아니다.

## 3.7 request ID는 observability identity다

성공한 typed response에서는 다음 public property를 사용할 수 있다.

```python
response._request_id
```

underscore prefix지만 OpenAI Python SDK가 public property로 문서화한 예외다.

status failure에서는 Response object가 application에 정상 반환되지 않으므로 exception에서 request ID를 확인한다.

```python
except openai.APIStatusError as exc:
    print(exc.request_id)
```

여기서 다시 identity를 구분한다.

```text
response.id
→ API Response resource identity

response._request_id / exc.request_id
→ HTTP/API request debugging identity
```

failure diagnosis에서 resource ID와 request tracing ID를 하나로 부르지 않는다.

## 3.8 application retry를 SDK retry 위에 무작정 쌓지 않는다

다음 코드를 생각하자.

```python
for _ in range(3):
    try:
        return client.responses.create(...)
    except openai.RateLimitError:
        continue
```

client default가 `max_retries=2`라면 application loop 한 번마다 SDK 내부에서 여러 attempt가 일어날 수 있다.

최악의 단순 계산을 해 보자.

```text
application attempts = 3
SDK attempts per call = 최대 3

possible HTTP attempts = 최대 9
```

실제 retry timing/termination은 error와 policy에 따라 달라질 수 있지만 핵심은 **retry layer가 곱해질 수 있다**는 것이다.

따라서 retry를 추가할 때는 먼저 묻는다.

- SDK가 이미 retry하는 failure인가?
- application retry는 어떤 additional business condition을 해결하는가?
- overall latency/request budget은 얼마인가?
- request가 side effect를 만들 수 있다면 repeated attempt가 안전한가?

## 3.9 Observable Lab A: 실제 API 없이 SDK retry를 관찰한다

실제 429를 만들기 위해 API quota를 소모하지 않는다.

이번 playground는 localhost에 작은 synthetic HTTP server를 띄우고 OpenAI SDK의 `base_url`을 그 endpoint로 바꾼다.

```bash
uv run playground/failure_boundaries.py --status 429 --max-retries 2
```

server는 모든 POST request에 synthetic 429 JSON error를 반환한다.

이 실험은 다음을 검증한다.

```text
OpenAI Python SDK가 해당 HTTP status를 어떻게 exception으로 분류하는가
configured max_retries에서 몇 번 local HTTP request가 발생하는가
status failure의 request ID를 exception에서 읽을 수 있는가
```

이 실험은 다음을 검증하지 않는다.

```text
OpenAI API가 실제로 rate limit을 발생시키는 조건
production network behavior
server-side rate-limit algorithm
실제 API availability
```

local synthetic endpoint와 real API evidence를 섞지 않는다.

## 3.10 먼저 prediction한다

실행 전에 적는다.

```text
status = 429
max_retries = 2
```

질문:

1. Python에서 `responses.create()`를 몇 번 호출하는가?
2. local server는 POST를 몇 번 받을 것으로 예상하는가?
3. 마지막 exception은 `APIStatusError` 계열인가?
4. 더 구체적으로 `RateLimitError`인가?

그 다음 실행 output의 `request_count`와 exception type을 확인한다.

## 3.11 Observable Lab B: retry되지 않는 400과 비교한다

```bash
uv run playground/failure_boundaries.py --status 400 --max-retries 2
```

같은 `max_retries=2`라도 request count를 비교한다.

```text
429 experiment request_count
vs.
400 experiment request_count
```

중요한 것은 숫자를 외우는 것이 아니라 **retry decision이 client setting 하나만으로 결정되지 않고 failure class/status와 결합된다는 것**이다.

## 3.12 Observable Lab C: retry policy를 제거한다

다시 429를 사용하되 retry를 끈다.

```bash
uv run playground/failure_boundaries.py --status 429 --max-retries 0
```

prediction:

```text
request_count = ?
exception type = ?
```

결과를 `max_retries=2`와 비교한다.

```text
같은 synthetic server behavior
+
다른 client policy
=
application이 exception을 받기 전 attempt history가 달라짐
```

이것이 client configuration이 control flow를 바꾸는 방식이다.

## 3.13 Observable Lab D: 500과 비교한다

```bash
uv run playground/failure_boundaries.py --status 500 --max-retries 2
```

429와 request count가 비슷할 수 있지만 exception 의미는 다르다.

질문한다.

- 둘 다 retry될 수 있다는 사실이 같은 root cause를 의미하는가?
- 429와 500에서 application logging/alerting에 남길 context는 같아야 하는가?
- `RateLimitError`처럼 더 구체적인 type이 주는 debugging benefit은 무엇인가?

retry policy와 failure semantics를 분리한다.

## 3.14 transport failure와 status failure를 구분한다

synthetic lab은 HTTP response를 일부러 반환하므로 status failure를 관찰한다.

transport failure에서는 정상적인 HTTP error response 자체가 없을 수 있다.

```text
status failure
request sent
→ HTTP 429/500 response received
→ APIStatusError hierarchy

transport failure
request path에서 connection/timeout problem
→ normal API status response 없음
→ APIConnectionError / APITimeoutError 계열
```

따라서 status code가 없는 failure에 `exc.status_code`를 기대하는 것은 boundary를 잘못 이해한 것이다.

## 3.15 application failure는 Response 이후에도 존재한다

다음 code는 network/API 관점에서 성공할 수 있다.

```python
response = client.responses.create(...)
```

그 뒤 application이 다음처럼 잘못 가정할 수 있다.

```python
if not response.output_text:
    raise RuntimeError("API failed")
```

`output_text`가 비어 있는 것과 HTTP request failure는 같은 사건이 아니다.

Responses API에는 text가 아닌 output item도 존재할 수 있고, 이후 structured output/function calling에서는 application success condition이 더 명시적으로 필요하다.

따라서 failure taxonomy를 다음처럼 유지한다.

```text
transport success?
API status success?
typed Response obtained?
application expected output/state satisfied?
```

## 3.16 흔한 잘못된 mental model

### "endpoint method 한 번 호출 = HTTP request 한 번"

automatic retry가 있으면 다를 수 있다.

### "`max_retries=2`면 총 두 번 요청한다"

retry count와 initial attempt를 구분한다.

### "모든 4xx/5xx는 같은 retry 대상이다"

failure semantics와 SDK policy가 다르다.

### "429 exception을 잡아서 loop를 하나 더 만들면 더 안전하다"

SDK retry와 application retry가 중첩되면 attempt/latency가 예상보다 커질 수 있다.

### "timeout 5초면 전체 call도 최대 5초"

retry와 결합되면 전체 wall-clock latency는 더 길 수 있다.

### "Response를 못 받았으면 request ID도 항상 없다"

status failure에서는 `APIStatusError.request_id`를 사용할 수 있다.

### "HTTP 200이면 application success"

transport/API success와 application-level output contract는 별도다.

## 3.17 Practice

### A. Count attempts

다음 조건에서 maximum HTTP attempt 수를 계산한다.

```text
SDK max_retries = 2
application outer retry = 최대 4회 endpoint call
모든 failure가 SDK retry 대상
```

계산 뒤 왜 이 upper bound가 latency/cost/side-effect review에 필요한지 설명한다.

### B. Classify

다음 증상을 가장 가까운 failure boundary에 배치한다.

```text
DNS resolution 실패
HTTP 401
HTTP 429
response.output에 expected text item 없음
client construction에서 credential configuration 없음
```

후보:

```text
local configuration
transport
API status
application interpretation
```

### C. Repair

다음 code를 검토한다.

```python
while True:
    try:
        return client.responses.create(...)
    except openai.APIError:
        time.sleep(1)
```

문제를 최소 세 가지 찾는다.

힌트:

- 어떤 error까지 영원히 retry하는가?
- SDK 내부 retry와 어떤 관계인가?
- termination/latency budget이 있는가?
- request가 side effect를 가진다면 안전한가?

### D. Observability

실패 로그에 다음 값 중 무엇을 남길지 판단한다.

```text
exception class
HTTP status
request ID
Response resource ID
API key
full sensitive input
attempt policy
```

각 값의 usefulness와 exposure boundary를 설명한다.

## Assessment checkpoint

이번 chapter는 다음 두 과제를 독립적으로 수행할 수 있을 때 통과한다.

### 1. Failure execution map

다음 두 scenario의 control flow를 그린다.

```text
A. 400 with max_retries=2
B. 429 with max_retries=2
```

각각에서 다음을 표시한다.

```text
application endpoint-call count
HTTP attempt count
retry decision point
final exception family
available request/status evidence
```

### 2. Retry policy review

주어진 application code가 SDK call 바깥에서 자체 retry를 수행한다.

learner는 다음을 판단한다.

1. SDK default/explicit retry와 중복되는 failure가 무엇인가?
2. upper-bound HTTP attempt 수는 얼마인가?
3. timeout과 결합한 latency risk는 무엇인가?
4. application retry가 정말 필요한 business condition은 무엇인가?
5. logging할 request identity와 failure classification은 무엇인가?

평가 기준:

- transport/API/application failure를 구분했는가?
- `APIConnectionError`, `APIStatusError`, `RateLimitError`의 boundary를 설명했는가?
- retry count와 HTTP attempt count를 구분했는가?
- timeout과 retry의 결합을 이해했는가?
- request ID와 Response resource ID를 혼동하지 않았는가?
- SDK retry 위에 application retry를 추가할 때 multiplicative effect를 계산했는가?

이 기준을 만족하면 Unit 3의 핵심 outcome인 **SDK call의 failure boundary와 retry control flow를 evidence로 진단하고 합리적인 timeout/retry policy를 선택하는 능력**을 갖춘 것으로 본다.
