# 5장 · Instrumentation

지금까지는 직접 `start_as_current_span()`을 호출했다. 실제 애플리케이션에서는 모든 framework route, HTTP client,
database call을 직접 감싸는 방식만 사용하지 않는다.

OpenTelemetry에서는 크게 세 관점을 구분해 두는 것이 유용하다.

```text
manual / code-based instrumentation
instrumentation libraries
zero-code / automatic instrumentation
```

Python zero-code instrumentation은 agent가 instrumentation library를 runtime에 로드하고, 주로 monkey patching으로
library/framework call을 계측한다.

이번 장에서는 각각을 따로 실행한 뒤 **같은 request 안에서 framework span과 manual business span을 함께 관찰**한다.

## 학습 목표

- manual instrumentation과 instrumentation library의 책임 차이를 설명한다.
- zero-code가 “애플리케이션의 모든 business 의미를 자동으로 이해한다”는 오해를 피한다.
- edge/dependency telemetry와 business-specific telemetry를 구분한다.
- 같은 application에 여러 instrumentation 방식이 함께 존재할 수 있음을 실제 trace에서 설명한다.
- framework span과 business span이 서로 다른 Instrumentation Scope를 가질 수 있음을 관찰한다.

## 준비할 것

이 장은 core lock 외에 다음 runtime dependency를 사용한다.

- Flask `3.1.3`
- OpenTelemetry Python contrib / distro `0.66b0`

`0.66b0`은 2026-10-02 calibration 시점의 current contrib release이지만 **beta-series version**이다. Stable API/SDK
`1.45.0`과 maturity를 같은 것으로 읽지 않는다.

HTTP request는 `curl` 예시를 사용하지만, 사용할 수 없다면 browser나 Python `urllib` 등으로 같은 localhost endpoint를
호출해도 된다.

## 1. 무엇을 보고 싶은가가 먼저다

다음 두 질문은 서로 다르다.

- “HTTP 요청이 들어오고 나가는 데 얼마나 걸렸는가?”
- “할인 정책 계산 단계가 왜 느렸는가?”

framework/library instrumentation은 첫 질문에 강하다. 두 번째 질문은 application business context를 알아야 하므로 manual
instrumentation이 더 적합하다.

즉 다음처럼 역할을 나누는 편이 자연스럽다.

```text
framework / library boundary → instrumentation library / zero-code
business operation           → manual instrumentation
```

## 2. Manual instrumentation

[`flask_manual.py`](flask_manual.py)는 Flask route 안에서 business span을 직접 만든다. SDK와 exporter도 application
code가 직접 구성한다.

실행:

```bash
uv run --locked --with 'flask==3.1.3' \
  textbook/05-instrumentation/flask_manual.py
```

다른 terminal에서:

```bash
curl http://127.0.0.1:8085/checkout
```

이 예제는 `checkout.calculate_total` 같은 **business 의미를 코드가 직접 선택**한다. 반면 Flask request boundary를
자동으로 설명하는 server span은 만들지 않는다.

## 3. Zero-code instrumentation

[`flask_zero_code.py`](flask_zero_code.py)는 OpenTelemetry 코드를 전혀 포함하지 않는다.

먼저 그냥 실행하면 application 응답은 오지만 OTel span은 생성되지 않는다.

```bash
uv run --locked --with 'flask==3.1.3' \
  textbook/05-instrumentation/flask_zero_code.py
```

이번에는 Python agent를 붙인다.

```bash
OTEL_SERVICE_NAME=adudeck-otel-zero-code \
OTEL_TRACES_EXPORTER=console \
OTEL_METRICS_EXPORTER=none \
OTEL_LOGS_EXPORTER=none \
uv run --locked \
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

Zero-code는 이런 instrumentation library와 SDK/exporter configuration을
**source code 수정 없이 runtime에 적용하는 방식**이다.

Python에서는 `opentelemetry-instrument`가 instrumentation libraries를 로드하고 monkey patching을 사용한다.

반대로 application code에서 `FlaskInstrumentor().instrument_app(app)`처럼 programmatic하게 instrumentation library를
적용할 수도 있다. 따라서 “library instrumentation = zero-code”로 등치시키지 않는다.

## 5. 둘을 같은 trace에서 본다

[`flask_mixed.py`](flask_mixed.py)는 business operation만 manual API로 표현하고, Flask request boundary와 SDK/exporter
configuration은 zero-code agent에 맡긴다.

application source 안에는 `TracerProvider`를 새로 만들거나 Flask instrumentor를 직접 호출하는 코드가 없다. 다만 Unit
4에서 배운 Instrumentation Scope와 parent 관계를 learner가 즉시 볼 수 있도록 `ScopeSummaryExporter`라는
**teaching probe**를 runtime provider에 추가한다. 이 probe는 framework를 계측하는 것이 아니라 이미 끝난 span의
identifier와 scope metadata를 출력한다.

실행:

```bash
OTEL_SERVICE_NAME=adudeck-otel-mixed \
OTEL_TRACES_EXPORTER=console \
OTEL_METRICS_EXPORTER=none \
OTEL_LOGS_EXPORTER=none \
uv run --locked \
  --with 'flask==3.1.3' \
  --with 'opentelemetry-distro==0.66b0' \
  --with 'opentelemetry-instrumentation-flask==0.66b0' \
  opentelemetry-instrument \
  python textbook/05-instrumentation/flask_mixed.py
```

다른 terminal에서:

```bash
curl http://127.0.0.1:8087/checkout
```

### 실행 전에 예측한다

한 request에 대해 다음 관계를 먼저 그려 보자.

```text
Flask server span
└─ checkout.calculate_total
```

예측할 것:

- 두 span의 `trace_id`는 같은가?
- manual business span의 `parent_id`는 어떤 span을 가리킬까?
- 두 span의 Instrumentation Scope는 같은가?

### 관찰한다

`scope-summary`는 finished span의 관계와 scope를 한 줄에 바로 보여 준다.

```text
scope-summary span=checkout.calculate_total trace_id=... span_id=... parent_id=... \
  scope=adudeck.checkout.business ...
scope-summary span=GET /checkout trace_id=... span_id=... parent_id=<root> \
  scope=opentelemetry.instrumentation.flask ...
```

ConsoleSpanExporter JSON에서도 같은 identifier와 Resource를 다시 확인할 수 있다. 하지만 관계를 판단할 때 JSON export
timing에 기대지 않아도 된다. teaching probe는 `SimpleSpanProcessor`로 끝난 span의 evidence를 즉시 출력한다.

확인할 핵심은 다음이다.

```text
business.trace_id == framework.trace_id
business.parent_id == framework.span_id
business.scope != framework.scope
```

즉 zero-code Flask instrumentation이 request boundary를 만들고, 그 current context 안에서 manual business span이 child로
연결된다. Unit 2의 current context와 Unit 4의 Instrumentation Scope가 실제 mixed instrumentation에서 만나는 지점이다.

## 6. 비교표

| 방식 | 장점 | 한계 |
| --- | --- | --- |
| Manual | business 의미를 가장 정확히 표현 | 코드 수정과 설계가 필요 |
| Instrumentation library | framework/library 공통 동작을 재사용 가능 | library가 아는 의미까지만 표현 |
| Zero-code | source 수정 없이 빠르게 framework/library telemetry 확보 | application 내부 business 의미는 제한적 |
| Mixed | framework boundary와 business 의미를 한 trace에서 결합 | operation boundary와 중복 instrumentation을 의도적으로 설계해야 함 |

## 7. 변형 실험

`flask_mixed.py`의 route 내부에 계산 단계 하나를 더 만든다고 가정한다.

```text
checkout.calculate_total
└─ calculate_discount
```

먼저 질문한다.

- zero-code만으로 `calculate_discount`라는 business operation을 알 수 있는가?
- 별도 span으로 만들 가치가 있다면 어떤 API instrumentation이 필요한가?
- framework server span의 Instrumentation Scope까지 바뀌어야 하는가?

핵심은 “auto가 부족하다”가 아니라 **관찰하려는 operation boundary를 누가 알고 있는가**다.

## 이해도 점검

1. zero-code가 잘 관찰하는 영역과 manual instrumentation이 필요한 영역을 각각 예로 들어 보자.
2. instrumentation library와 zero-code의 관계를 설명해 보자.
3. 모든 함수에 manual span을 넣는 것이 좋은 instrumentation이 아닌 이유는 무엇인가?
4. mixed example에서 framework span과 business span이 한 trace로 연결되는 이유는 무엇인가?
5. 두 span의 Instrumentation Scope가 다른 것이 분석에 어떤 도움을 주는가?

## 다른 사례에 적용하기

데이터 파이프라인 서비스가 HTTP 요청을 받고 DB query를 한 뒤 복잡한 ranking algorithm을 실행한다.

- HTTP/DB telemetry는 어떤 방식으로 시작하는 것이 효율적인가?
- ranking algorithm의 주요 단계는 어떤 방식으로 보강하는 것이 좋은가?
- 여러 방식이 만든 span이 한 trace 안에서 연결되려면 Unit 2의 어떤 mechanism이 계속 중요할까?
- framework, DB library, business ranking span을 어떤 scope 축으로 구분할 수 있을까?

### 참고 기준

- [OpenTelemetry Instrumentation concepts](https://opentelemetry.io/docs/concepts/instrumentation/)
- [OpenTelemetry Python instrumentation libraries](https://opentelemetry.io/docs/languages/python/libraries/)
- [OpenTelemetry Python zero-code instrumentation](https://opentelemetry.io/docs/zero-code/python/)
