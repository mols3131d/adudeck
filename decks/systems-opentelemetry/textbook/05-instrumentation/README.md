# 5장 · Instrumentation

지금까지는 직접 `start_as_current_span()`을 호출했다. 실제 애플리케이션에서는 모든 framework route, HTTP client, database call을 직접 감싸는 방식만 사용하지 않는다.

OpenTelemetry에서는 크게 세 관점을 구분해 두는 것이 유용하다.

```text
manual / code-based instrumentation
instrumentation libraries
zero-code / automatic instrumentation
```

Python zero-code instrumentation은 주로 instrumentation library를 runtime에 로드하고 monkey patching을 이용해 library/framework call을 계측한다.

## 학습 목표

- manual instrumentation과 instrumentation library의 책임 차이를 설명한다.
- zero-code가 “애플리케이션의 모든 business 의미를 자동으로 이해한다”는 오해를 피한다.
- edge/dependency telemetry와 business-specific telemetry를 구분한다.
- 같은 application에 여러 instrumentation 방식이 함께 존재할 수 있음을 설명한다.

## 1. 무엇을 보고 싶은가가 먼저다

다음 두 질문은 서로 다르다.

- “HTTP 요청이 들어오고 나가는 데 얼마나 걸렸는가?”
- “할인 정책 계산 단계가 왜 느렸는가?”

framework/library instrumentation은 첫 질문에 강하다. 두 번째 질문은 application business context를 알아야 하므로 manual instrumentation이 더 적합하다.

즉 다음처럼 역할을 나누는 편이 자연스럽다.

```text
framework / library boundary → instrumentation library / zero-code
business operation           → manual instrumentation
```

## 2. Manual instrumentation

[`flask_manual.py`](flask_manual.py)는 Flask route 안에서 business span을 직접 만든다.

실행:

```bash
uv run --with 'flask==3.1.3' textbook/05-instrumentation/flask_manual.py
```

다른 terminal에서:

```bash
curl http://127.0.0.1:8085/checkout
```

이 예제는 `checkout.calculate_total` 같은 **business 의미를 코드가 직접 선택**한다.

## 3. Zero-code instrumentation

[`flask_zero_code.py`](flask_zero_code.py)는 OpenTelemetry 코드를 전혀 포함하지 않는다.

먼저 그냥 실행하면 application 응답은 오지만 OTel span은 생성되지 않는다.

```bash
uv run --with 'flask==3.1.3' textbook/05-instrumentation/flask_zero_code.py
```

이번에는 Python agent를 붙인다.

```bash
OTEL_SERVICE_NAME=adudeck-otel-zero-code \
OTEL_TRACES_EXPORTER=console \
OTEL_METRICS_EXPORTER=none \
OTEL_LOGS_EXPORTER=none \
uv run \
  --with 'flask==3.1.3' \
  --with 'opentelemetry-distro==0.66b0' \
  --with 'opentelemetry-instrumentation-flask==0.66b0' \
  opentelemetry-instrument \
  python textbook/05-instrumentation/flask_zero_code.py
```

다른 terminal에서 같은 요청을 보낸다.

```bash
curl http://127.0.0.1:8086/checkout
```

### 예측할 것

- source code에 `start_as_current_span()`이 없는데도 왜 span이 생기는가?
- zero-code가 `checkout.calculate_total`이라는 business span까지 알아서 만들까?
- framework route와 HTTP metadata는 어느 방식이 더 쉽게 얻는가?

## 4. Instrumentation library와 zero-code는 같은 말이 아니다

Instrumentation library는 특정 library/framework를 계측하는 reusable component다.

Zero-code는 이런 instrumentation library와 SDK/exporter configuration을 **source code 수정 없이 runtime에 적용하는 방식**이다.

Python에서는 `opentelemetry-instrument`가 instrumentation libraries를 로드하고 monkey patching을 사용한다.

반대로 application code에서 `FlaskInstrumentor().instrument_app(app)`처럼 programmatic하게 instrumentation library를 적용할 수도 있다. 따라서 “library instrumentation = zero-code”로 등치시키지 않는다.

## 5. 비교표

| 방식 | 장점 | 한계 |
| --- | --- | --- |
| Manual | business 의미를 가장 정확히 표현 | 코드 수정과 설계가 필요 |
| Instrumentation library | framework/library 공통 동작을 재사용 가능 | library가 아는 의미까지만 표현 |
| Zero-code | source 수정 없이 빠르게 telemetry 확보 | application 내부 business 의미는 제한적 |

## 6. 변형 실험

`flask_zero_code.py`의 route 내부에 계산 단계 두 개를 추가한다.

```text
load_cart
calculate_discount
```

zero-code 실행만으로 두 단계가 별도 span으로 나타나는지 확인한다.

그 다음 “이 두 단계의 latency를 구분해서 보고 싶다”면 어떤 instrumentation을 추가해야 하는지 설명한다.

핵심은 “auto가 부족하다”가 아니라 **관찰하려는 operation boundary를 누가 알고 있는가**다.

## 이해도 점검

1. zero-code가 잘 관찰하는 영역과 manual instrumentation이 필요한 영역을 각각 예로 들어 보자.
2. instrumentation library와 zero-code의 관계를 설명해 보자.
3. 모든 함수에 manual span을 넣는 것이 좋은 instrumentation이 아닌 이유는 무엇인가?
4. framework span과 business span을 함께 사용할 때 Unit 4의 Instrumentation Scope가 왜 유용한가?

## 다른 사례에 적용하기

데이터 파이프라인 서비스가 HTTP 요청을 받고 DB query를 한 뒤 복잡한 ranking algorithm을 실행한다.

- HTTP/DB telemetry는 어떤 방식으로 시작하는 것이 효율적인가?
- ranking algorithm의 주요 단계는 어떤 방식으로 보강하는 것이 좋은가?
- 두 방식이 만든 span이 한 trace 안에서 연결되려면 Unit 2의 어떤 mechanism이 계속 중요할까?

### 참고 기준

- [OpenTelemetry Instrumentation concepts](https://opentelemetry.io/docs/concepts/instrumentation/)
- [OpenTelemetry Python instrumentation libraries](https://opentelemetry.io/docs/languages/python/libraries/)
- [OpenTelemetry Python zero-code instrumentation](https://opentelemetry.io/docs/zero-code/python/)
