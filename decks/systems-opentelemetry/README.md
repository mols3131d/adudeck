# OpenTelemetry

OpenTelemetry를 **telemetry data flow를 직접 만들고 관찰하면서** 배우는 deck이다.

이 deck의 중심 질문은 다음과 같다.

```text
application operation
→ instrumentation
→ span / metric
→ context
→ exporter
→ OTLP
→ Collector
→ backend
```

처음부터 dashboard를 띄우지 않는다. 먼저 한 Python process 안에서 span이 어떻게 만들어지고 연결되는지 확인한 뒤,
process와 service 경계를 하나씩 추가한다.

## Goal

이 deck을 마치면 다음을 할 수 있어야 한다.

- OpenTelemetry API, SDK, instrumentation, exporter의 역할을 구분한다.
- span과 trace의 관계를 `trace_id`, `span_id`, parent 관계로 설명한다.
- current context가 child span과 distributed trace 연결에 어떤 역할을 하는지 설명한다.
- Resource와 Instrumentation Scope가 telemetry의 발생 주체와 생성 주체를 어떻게 구분하는지 설명한다.
- manual instrumentation과 library/zero-code instrumentation의 차이를 비교한다.
- Semantic Conventions가 서로 다른 instrumentation의 telemetry 의미를 맞추는 이유를 설명한다.
- OTLP를 통해 application process의 telemetry가 Collector로 이동하는 경계를 추적한다.
- Counter, UpDownCounter, Histogram 중 목적에 맞는 metric instrument를 선택한다.
- telemetry가 보이지 않을 때 application → exporter → transport → Collector → backend 순서로 원인을 좁힌다.

## Prerequisites

- Python 함수와 `with` context manager를 읽고 작은 코드를 수정할 수 있다.
- terminal에서 Python program을 실행하고 dependency를 설치할 수 있다.
- process, environment variable, HTTP request/response의 기본 개념을 알고 있다.

Distributed Systems 전체나 observability backend 사용 경험은 prerequisite가 아니다. 필요한 network/process boundary는
해당 unit에서 최소 범위로 다룬다.

## Learning scope

Core path:

```text
first trace
→ span data and failure
→ Resource / API / SDK
→ instrumentation
→ context propagation
→ OTLP / Collector
→ metrics
→ diagnosis
```

현재 core scope가 아닌 것:

- production monitoring architecture 전체
- Kubernetes Operator와 Collector fleet 운영
- advanced sampling / tail sampling 설계
- logs pipeline의 심화 운영
- vendor-specific dashboard 사용법
- GenAI/LLM semantic conventions

Logs와 GenAI telemetry는 core tracing/metrics 경계를 이해한 뒤 별도 extension으로 다룬다.

## Learning path

| Unit | 핵심 질문 | Material |
| --- | --- | --- |
| 0. Intro | 무엇을 관찰하고 어떤 질문에 답할 것인가? | [Intro](textbook/00-intro/README.md) |
| 1. Setup | 같은 dependency 환경에서 실습을 시작할 수 있는가? | [Setup](textbook/01-setup/README.md) |
| 2. First trace | 한 process 안에서 span은 어떻게 trace로 연결되는가? | [First trace](textbook/02-first-trace/README.md) |
| 3. Span data + failure | span에는 어떤 상태와 실패 evidence를 남겨야 하는가? | [Span data + failure](textbook/03-span-data-failure/README.md) |
| 4. Resource + API/SDK | telemetry를 누가 만들고, 누가 실제로 처리하는가? | [Resource + API/SDK](textbook/04-resource-api-sdk/README.md) |
| 5. Instrumentation | manual과 automatic instrumentation은 무엇이 다른가? | [Instrumentation](textbook/05-instrumentation/README.md) |
| 6. Propagation | 두 service의 span은 어떻게 하나의 trace가 되는가? | [Propagation](textbook/06-propagation/README.md) |
| 7. OTLP + Collector | telemetry가 application process 밖으로 어떻게 이동하는가? | [OTLP + Collector](textbook/07-otlp-collector/README.md) |
| 8. Metrics | 어떤 상태를 어떤 metric instrument로 표현해야 하는가? | [Metrics](textbook/08-metrics/README.md) |
| 9. Diagnosis | telemetry가 끊겼을 때 어느 boundary부터 확인해야 하는가? | [Diagnosis](textbook/09-diagnosis/README.md) |

전체 textbook navigation과 outcome coverage는 [textbook index](textbook/README.md)에 정리한다.

## Start here

[Intro](textbook/00-intro/README.md)를 읽고 [Setup](textbook/01-setup/README.md)을 진행한다.
첫 실습에서는 external backend가 필요하지 않다. `ConsoleSpanExporter`가 span을 stdout에 출력한다.

## Dependency ownership

이 deck의 core Python dependency range는 [`pyproject.toml`](pyproject.toml)이 소유한다.

[`uv.lock`](uv.lock)은 core tracing/metrics 실습의 실제 실행 dependency를 고정한다. Unit 5의 Flask/zero-code 비교와 Unit 7의
OTLP HTTP exporter는 해당 장에서 version을 명시한 `uv --with` 환경으로 격리한다. 이 보조 환경은 deck lockfile과 같은
validation claim을 갖지 않는다.

Deck directory에서 현재 repository-managed runtime test를 실행할 수 있다.

```bash
uv run --locked python -m unittest discover -s tests -v
```

검사는 별도 process에서 실행하며 외부 `OTEL_*` 설정을 제거해 실습의 기본 SDK 환경을 유지한다.

## Build progress

- Curriculum baseline: 이 README의 Goal, Prerequisites, Learning scope, Learning path.
- Textbook: Unit 0–9의 chapter prose와 핵심 hands-on artifact가 작성되어 있다.
- Unit 2는 정상 실행과 current-context 변형을 Python 3.14.6 / OpenTelemetry API·SDK 1.45.0에서 검증했다.
- 새 core-only example(Unit 3, 4, 6, 8)은 authoring 과정에서 별도 Python 환경의 runtime smoke를 수행했지만,
  repository lockfile 기준의 정식 acceptance와 CI 확장은 아직 남아 있다.
- Unit 5의 Flask/zero-code와 Unit 7의 OTLP/Collector는 external dependency/container boundary를 사용하므로 full runtime
  validation을 별도로 수행해야 한다.
- Unit 9는 앞선 unit의 evidence를 재사용하는 diagnostic synthesis다. Backend UI 자체는 core completion claim에 포함하지 않는다.
- 전체 deck completion은 textbook 존재가 아니라 outcome coverage, runtime validation boundary, integration review가 모두
  충족된 뒤 선언한다.

## Version baseline

작성/검토 기준일: **2026-10-02**

- Python: 3.10+
- OpenTelemetry Python API/SDK: `1.45.0`
- OpenTelemetry Python contrib / zero-code calibration: `0.66b0`
- OpenTelemetry Collector calibration: `0.162.0`
- Traces / Metrics: Stable
- Logs: Development

Version-sensitive behavior는 구현 시점의 official OpenTelemetry source와 실제 runtime evidence를 함께 확인한다.

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Python manual instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [Python instrumentation libraries](https://opentelemetry.io/docs/languages/python/libraries/)
- [Python zero-code instrumentation](https://opentelemetry.io/docs/zero-code/python/)
- [Python exporters](https://opentelemetry.io/docs/languages/python/exporters/)
- [Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
- [Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
- [Collector configuration](https://opentelemetry.io/docs/collector/configuration/)
- [Collector troubleshooting](https://opentelemetry.io/docs/collector/troubleshooting/)
