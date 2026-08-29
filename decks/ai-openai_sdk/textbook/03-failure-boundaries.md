# 3. Failure boundaries: Python call 하나와 HTTP attempt 수는 다를 수 있다

`client.responses.create(...)`는 application에서는 한 번의 method call이다. 그러나 SDK의 timeout/retry policy 때문에 transport
관점에서는 여러 HTTP attempt가 일어날 수 있다.

```text
application call
   ↓
SDK timeout / retry policy
   ↓
HTTP attempt
   ├─ retryable failure → next attempt
   └─ success / terminal failure
   ↓
typed Response or SDK exception
```

이번 chapter의 목표는 exception 이름을 외우는 것이 아니라 **실패가 어느 boundary에서 발생했고, 몇 번의 attempt가 있었는지**
설명하는 것이다.

## 3.1 실패를 네 층으로 나눈다

| Boundary | 예 | 먼저 볼 evidence |
| --- | --- | --- |
| local configuration | credential/configuration 누락 | client construction / local exception |
| transport / timeout | connection failure, timeout | `APIConnectionError`, `APITimeoutError` 계열 |
| API status | 400, 429, 5xx | `APIStatusError` 계열, status, request ID |
| application interpretation | 기대한 output/state가 없음 | typed Response와 application rule |

가장 중요한 구분은 마지막이다.

```text
HTTP/API success
!=
application이 원하는 결과를 얻음
```

`response.output_text`가 비어 있다는 이유만으로 network request 실패라고 결론 내리지 않는다.

## 3.2 Exception hierarchy는 boundary를 표현한다

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

개념적으로 다음처럼 읽는다.

```text
APIConnectionError
→ 정상적인 API status response를 받기 전 transport 문제

APIStatusError
→ HTTP response를 받았지만 non-success status

RateLimitError
→ 429를 표현하는 더 구체적인 status error
```

구체적인 subclass를 모두 외울 필요는 없다. **status response가 있었는가**가 첫 분기다.

## 3.3 Retry: `max_retries`는 retry 수이지 total attempt 수가 아니다

현재 deck의 OpenAI Python SDK v3.x baseline에서 default retry policy는 connection-related error와 일부 status
(408, 409, 429, 5xx 등)를 automatic retry할 수 있다. 기본 `max_retries`는 2다.

```python
client = OpenAI(max_retries=2)
```

계속 retryable failure가 난다면:

```text
initial attempt 1
+ retry 최대 2
= 최대 3 HTTP attempts
```

반대로 400처럼 같은 request를 반복해도 해결되지 않는 status는 기본 retry 대상이 아니다.

따라서 retry behavior는 다음 둘의 조합이다.

```text
failure class/status
+
client retry policy
```

## 3.4 Timeout도 retry와 함께 읽는다

```python
client = OpenAI(timeout=20.0)

client.with_options(timeout=5.0).responses.create(...)
```

Timeout은 "한 attempt를 얼마나 기다릴 것인가"와 관련된다. Retry가 켜져 있다면 다음 등식은 성립하지 않는다.

```text
timeout = 5초
→ 전체 application call이 반드시 5초 안에 끝남
```

전체 latency budget을 판단할 때는 **per-attempt timeout과 possible attempt count를 함께** 본다.

## 3.5 Worked trace: 계속 429가 반환된다

```python
client = OpenAI(max_retries=2)
client.responses.create(...)
```

Synthetic server가 모든 POST에 429를 반환한다고 가정한다.

```text
responses.create()      application call 1회
        ↓
HTTP #1 → 429
        ↓ retry
HTTP #2 → 429
        ↓ retry
HTTP #3 → 429
        ↓
RateLimitError
```

여기서 세 count를 섞지 않는다.

```text
application method call count
HTTP attempt count
business side-effect count
```

이 구분은 application-level retry를 추가할 때 특히 중요하다.

## 3.6 SDK retry 위에 application retry를 무작정 쌓지 않는다

```python
for _ in range(3):
    try:
        return client.responses.create(...)
    except openai.RateLimitError:
        continue
```

SDK가 call마다 최대 3 attempts를 만들 수 있다면 바깥 loop까지 합쳐 request 수와 latency가 크게 늘어날 수 있다.

Retry layer를 추가하기 전에 묻는다.

1. SDK가 이미 이 failure를 retry하는가?
2. application retry가 해결하는 **추가 business condition**은 무엇인가?
3. total latency/request budget은 얼마인가?
4. repeated request가 side effect를 만들 수 있다면 안전한가?

Retry는 "더 많을수록 안전"한 기능이 아니다.

## 3.7 Request ID와 resource ID를 구분한다

성공한 Response:

```python
response.id
response._request_id
```

Status failure:

```python
except openai.APIStatusError as exc:
    print(exc.request_id)
```

역할은 다르다.

```text
response.id
→ Response resource identity

_request_id / exc.request_id
→ API request debugging identity
```

장애 기록에서 둘을 모두 "response ID"라고 부르면 추적성이 나빠진다.

## 3.8 Playground: 실제 quota를 건드리지 않고 retry policy를 비교한다

`playground/failure_boundaries.py`는 localhost synthetic HTTP endpoint를 사용한다. 실제 OpenAI API rate limit을
만들지 않는다.

먼저 prediction한다.

| status | `max_retries` | 예상 request count | 예상 exception |
| ---: | ---: | ---: | --- |
| 400 | 2 | | |
| 429 | 2 | | |
| 500 | 2 | | |
| 429 | 0 | | |

그 다음 실행한다.

```bash
uv run playground/failure_boundaries.py --status 400 --max-retries 2
uv run playground/failure_boundaries.py --status 429 --max-retries 2
uv run playground/failure_boundaries.py --status 500 --max-retries 2
uv run playground/failure_boundaries.py --status 429 --max-retries 0
```

관찰할 값은 세 개면 충분하다.

```text
python exception type
status_code
request_count
```

### Validation boundary

이 synthetic lab이 검증하는 것:

- 현재 SDK가 해당 status를 어떤 exception으로 표현하는가
- configured retry policy에서 local HTTP request가 몇 번 발생하는가
- status failure에서 request ID를 읽을 수 있는가

검증하지 않는 것:

- 실제 OpenAI API의 rate-limit 발생 조건
- production network behavior
- 실제 service availability
- server-side retry recommendation 전체

Synthetic endpoint evidence를 real API evidence로 확대하지 않는다.

## 3.9 실패 진단 순서

실제 application에서 call이 실패했다고 하자.

```text
1. local configuration 단계까지 갔는가?
2. HTTP status response가 있었는가?
   ├─ 아니오 → transport/timeout
   └─ 예 → status/error class 확인
3. SDK 내부 retry가 몇 번 가능했는가?
4. typed Response를 받았다면 application success condition은 무엇인가?
```

이 순서를 따르면 "429", "timeout", "빈 output"을 같은 종류의 실패로 처리하지 않게 된다.

## 3.10 흔한 오해

### "endpoint method 한 번 = HTTP request 한 번"

Automatic retry가 있으면 다를 수 있다.

### "`max_retries=2`면 총 두 번 요청한다"

Initial attempt와 retry count를 구분한다.

### "모든 HTTP error는 retry하면 된다"

Failure semantics와 retry policy가 다르다.

### "timeout 값이 전체 latency upper bound다"

Retry가 결합되면 전체 call은 더 길어질 수 있다.

### "APIStatusError와 application validation failure는 같은 실패다"

하나는 remote HTTP status, 다른 하나는 Response 이후 application contract다.

## 3.11 Practice

### A. Attempt arithmetic

다음 설정에서 **최대 possible attempt 수**를 계산하고, 실제 count가 더 적을 수 있는 이유를 설명한다.

```text
application retry loop = 최대 2 calls
SDK max_retries = 2
```

### B. Diagnosis

다음 증상을 boundary에 배치한다.

```text
APITimeoutError
HTTP 400
RateLimitError + request_id
Response는 completed지만 expected function_call이 없음
```

### C. Policy review

한 service가 `RateLimitError`를 잡아 무조건 5회 재호출한다. SDK default retry가 그대로다.

요청량, latency, side effect 관점에서 위험을 설명하고 **어느 layer가 retry를 책임질지** 제안한다.

## Assessment checkpoint

다음을 독립적으로 설명할 수 있으면 통과한다.

1. 한 Python endpoint call이 여러 HTTP attempt를 만들 수 있는 이유.
2. transport / API status / application interpretation failure를 evidence로 구분하는 방법.
3. retry와 timeout을 함께 고려해 bounded client policy를 설계하는 방법.
4. synthetic lab이 증명하는 것과 실제 OpenAI API에 대해 아직 증명하지 못한 것을 구분하는 방법.
