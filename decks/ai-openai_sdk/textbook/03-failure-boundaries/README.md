# 3. Failure boundaries: 한 Python call과 HTTP attempt 수는 다를 수 있다

`client.responses.create(...)`는 application에서는 한 번의 function call이다.
하지만 SDK retry policy 때문에 HTTP request는 여러 번 발생할 수 있다.

이번 unit에서는 실제 quota를 소모해 실패를 만들지 않는다.
local synthetic server가 같은 status를 반복해서 반환하게 하고, SDK가 몇 번 요청하는지 관찰한다.

## 3.1 Learner-facing file은 retry 설정만 보여준다

실행한다.

```bash
uv run textbook/03-failure-boundaries/failure_boundaries.py
```

핵심 부분은 다음 정도다.

```python
STATUS = 429
MAX_RETRIES = 2

with synthetic_error_server(STATUS) as server:
    client = OpenAI(
        api_key="local-test-key",
        base_url=server.base_url,
        max_retries=MAX_RETRIES,
        timeout=5.0,
    )

    try:
        client.responses.create(model="gpt-5.5", input="retry experiment")
    except openai.APIStatusError as exc:
        print(type(exc).__name__)
        print(exc.status_code)
        print(server.request_count)
```

HTTP server 구현은 `retry_server.py`에 있다.
이번 학습 목표가 Python stdlib HTTP server 작성법이 아니므로 learner-facing file에서 숨긴다.

## 3.2 먼저 예상한다

기본값:

```text
STATUS = 429
MAX_RETRIES = 2
```

예상할 것:

- Python endpoint method call은 몇 번인가?
- HTTP attempt는 최대 몇 번인가?
- 마지막에 어떤 exception 계열이 보일까?

`max_retries=2`는 total attempt 2회라는 뜻이 아니다.

```text
initial attempt 1
+ retry 최대 2
= 최대 3 attempts
```

## 3.3 직접 한 값만 바꾼다

`STATUS`를 400으로 바꾼다.

```python
STATUS = 400
```

다시 실행하고 `request_count`를 비교한다.

그다음 500으로 바꾼다.

```python
STATUS = 500
```

마지막으로 429 상태에서:

```python
MAX_RETRIES = 0
```

으로 바꾼다.

표를 직접 채운다.

| status | max_retries | observed request_count | exception type |
| ---: | ---: | ---: | --- |
| 400 | 2 | | |
| 429 | 2 | | |
| 500 | 2 | | |
| 429 | 0 | | |

## 3.4 실패 boundary를 구분한다

| Boundary | 예 | 먼저 볼 evidence |
| --- | --- | --- |
| local configuration | credential/configuration 누락 | local exception |
| transport / timeout | connection failure, timeout | `APIConnectionError`, `APITimeoutError` |
| API status | 400, 429, 5xx | `APIStatusError` 계열, status, request ID |
| application interpretation | expected output/state 없음 | returned `Response`와 application rule |

중요한 등식:

```text
HTTP/API success
!=
application success
```

예를 들어 Response가 정상적으로 왔더라도 application이 기대한 function call이 없을 수 있다.

## 3.5 Timeout과 retry를 같이 본다

```python
OpenAI(
    timeout=5.0,
    max_retries=2,
)
```

`timeout=5.0`만 보고 전체 application call이 반드시 5초 안에 끝난다고 결론 내리면 안 된다.
여러 attempt가 가능하기 때문이다.

## 3.6 Synthetic evidence의 한계

이 playground가 직접 보여주는 것:

- 실제 실행에 resolve된 SDK version이 synthetic HTTP status를 어떤 exception으로 표현하는가
- configured retry policy에서 local HTTP request가 몇 번 발생하는가

`failure_boundaries.py`는 시작할 때 `openai.__version__`도 출력한다. 관찰 결과가 이 deck의 reviewed baseline과 다르면
실제 resolve된 version을 먼저 확인한다.

보여주지 않는 것:

- 실제 OpenAI API rate-limit 발생 조건
- production network behavior
- service availability
- server-side 정책 전체

local synthetic 429를 실제 OpenAI quota event와 같은 것으로 해석하지 않는다.

## Practice

다음 설정의 최대 HTTP attempt 수를 계산한다.

```text
application retry loop = 최대 2 calls
SDK max_retries = 2
```

그 뒤 "SDK retry 위에 application retry를 무조건 추가하면 왜 위험한가?"를
request count와 latency 관점에서 설명한다.

## Checkpoint

다음 네 증상을 각각 boundary에 배치하고 가장 먼저 확인할 evidence를 적는다.

```text
APITimeoutError
HTTP 400
RateLimitError + request_id
Response completed, but expected function_call 없음
```
