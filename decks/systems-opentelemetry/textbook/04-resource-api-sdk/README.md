# 4장 · Resource와 API/SDK

앞 장까지는 span 안의 관계와 의미를 읽었다. 이제 한 단계 뒤로 물러나
**누가 telemetry를 만들고 누가 실제로 처리하는지**를 본다.

이번 장의 핵심 구분은 두 개다.

```text
Resource              = telemetry가 설명하는 실행 주체
Instrumentation Scope = telemetry를 만든 논리적 software unit
```

그리고 runtime 책임은 다음처럼 나뉜다.

```text
API → Provider/SDK → Processor → Exporter
```

## 학습 목표

- API와 SDK의 책임을 구분한다.
- `Resource`와 `Instrumentation Scope`를 구분한다.
- `TracerProvider → SpanProcessor → Exporter` 데이터 흐름을 설명한다.
- 같은 `service.name`이 곧 같은 process나 같은 Resource object를 뜻하지 않는다는 것을 설명한다.

## 1. API는 “무엇을 기록할지” 말한다

애플리케이션 코드가 호출하는 `trace.get_tracer()`와 `start_as_current_span()`은 API 표면이다. library code는 가능하면 이
API에 의존하고, telemetry를 어디로 보낼지까지 결정하지 않는다.

SDK는 실제 Provider, sampling, processing, export 같은 runtime behavior를 제공한다.

따라서 library가 OpenTelemetry API를 사용한다고 해서 특정 backend에 종속되는 것은 아니다.

## 2. Resource는 “누구의 telemetry인가”를 설명한다

Resource는 telemetry를 발생시키는 entity를 설명한다.

예를 들면:

```text
service.name = checkout-service
service.version = 2026.10
```

실제 환경에서는 process, container, pod, cloud resource 같은 정보도 Resource에 들어갈 수 있다.

중요한 점은 Resource가 Provider에 연결되고, 그 Provider에서 만들어진 telemetry에 함께 붙는다는 것이다.

## 3. Instrumentation Scope는 “누가 만들었는가”를 설명한다

다음 두 tracer를 생각해 보자.

```python
checkout_tracer = trace.get_tracer("adudeck.checkout", "1.0.0")
payment_tracer = trace.get_tracer("adudeck.payment", "1.0.0")
```

둘 다 같은 service process에서 실행될 수 있다. Resource는 같지만 instrumentation scope는 다르다.

```text
same Resource
├─ scope: adudeck.checkout
└─ scope: adudeck.payment
```

이 구분 덕분에 “어느 service인가?”와 “어느 library/module이 telemetry를 만들었는가?”를 섞지 않을 수 있다.

## 4. 실행 전에 예측한다

[`sdk_boundaries.py`](sdk_boundaries.py)는 같은 Resource와 Provider를 공유하면서 서로 다른 tracer scope로 span을 만든다.

예측한다.

1. 두 span의 `resource.attributes.service.name`은 같은가?
2. instrumentation scope name도 같은가?
3. span이 끝난 뒤 ConsoleSpanExporter까지 가는 경로에 어떤 SDK component가 있는가?

## 5. 실행한다

```bash
uv run --locked textbook/04-resource-api-sdk/sdk_boundaries.py
```

스크립트가 먼저 `boundary-summary` 한 줄로 `service.name`, scope name, scope version을 출력한다. 이어지는
ConsoleSpanExporter JSON에서 Resource를 다시 확인할 수 있다.

```text
boundary-summary span=charge_payment service.name=... scope=adudeck.payment scope.version=1.0.0
```

이 summary exporter는 학습용 probe다. **안정적인 contract는 Resource와 Instrumentation Scope 개념 자체**이고, console
JSON formatting이나 이 teaching probe를 외부 protocol contract처럼 취급하지 않는다.

## 6. Processor와 Exporter

현재 예제는 다음 구조다.

```text
span.end()
   ↓
SimpleSpanProcessor
   ↓
ConsoleSpanExporter
   ↓
stdout
```

`SimpleSpanProcessor`는 span이 끝날 때 바로 exporter를 호출해 학습하기 쉽다. 네트워크 export에서는 보통 batch
processing이 더 적합하다.

여기서 중요한 것은 **Processor와 Exporter를 같은 것으로 보지 않는 것**이다.

- Processor: finished span을 언제, 어떤 방식으로 exporter에 넘길지 관여한다.
- Exporter: span 데이터를 특정 destination/transport로 내보낸다.

## 7. 변형 실험

`payment_tracer`의 scope name을 `adudeck.checkout`으로 바꿔 다시 실행한다.

- Resource는 바뀌는가?
- scope distinction은 어떻게 달라지는가?
- span name이 같더라도 scope가 다르면 어떤 분석이 가능했는가?

그 다음 `service.name`을 다른 값으로 바꿔 보자. 이번에는 Resource와 scope 중 어느 축이 바뀌는지 설명한다.

## 이해도 점검

1. Resource와 Instrumentation Scope의 질문을 각각 한 문장으로 표현해 보자.
2. API를 사용하는 library가 특정 exporter를 직접 설정하지 않는 편이 좋은 이유는 무엇인가?
3. Processor와 Exporter의 책임을 구분해 설명해 보자.
4. 같은 `service.name` 값만으로 같은 process라고 결론 내릴 수 없는 이유는 무엇인가?

## 다른 사례에 적용하기

하나의 web service에서 framework instrumentation과 application의 business instrumentation이 함께 span을 만든다.

- Resource는 어떻게 공유될 수 있는가?
- framework와 business span을 instrumentation scope로 어떻게 구분할 수 있는가?
- 이 구조가 Unit 5의 instrumentation 비교에서 왜 유용한가?

### 참고 기준

- [OpenTelemetry Resources](https://opentelemetry.io/docs/concepts/resources/)
- [OpenTelemetry Instrumentation Scope](https://opentelemetry.io/docs/concepts/instrumentation-scope/)
- [OpenTelemetry Python instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
