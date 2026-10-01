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
- Resource와 `service.name`이 telemetry의 발생 주체를 어떻게 표현하는지 설명한다.
- manual instrumentation과 library/zero-code instrumentation의 차이를 비교한다.
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
| 0. First trace | 한 process 안에서 span은 어떻게 trace로 연결되는가? | [Bundle](textbook/00-first-trace/README.md) |
| 1. Span data + failure | span에는 어떤 상태와 실패 evidence를 남겨야 하는가? | planned |
| 2. Resource + API/SDK | telemetry를 누가 만들고, 누가 실제로 처리하는가? | planned |
| 3. Instrumentation | manual과 automatic instrumentation은 무엇이 다른가? | planned |
| 4. Propagation | 두 service의 span은 어떻게 하나의 trace가 되는가? | planned |
| 5. OTLP + Collector | telemetry가 application process 밖으로 어떻게 이동하는가? | planned |
| 6. Metrics | 어떤 상태를 어떤 metric instrument로 표현해야 하는가? | planned |
| 7. Diagnosis | telemetry가 끊겼을 때 어느 boundary부터 확인해야 하는가? | planned |

현재는 Unit 0 calibration slice만 구현한다. 이후 unit은 앞선 slice를 검토한 뒤 같은 PR에서 작은 increment로 추가한다.
전체 unit이 구현되기 전에는 deck completion을 선언하지 않는다.

## Start here

Deck directory에서 dependency를 준비하고 첫 실습을 실행한다.

```bash
cd decks/systems-opentelemetry
uv sync --locked
uv run --locked textbook/00-first-trace/first_trace.py
```

첫 실습에서는 external backend가 필요하지 않다. `ConsoleSpanExporter`가 span을 stdout에 출력한다.

## Dependency ownership

이 deck의 Python dependency range는 [`pyproject.toml`](pyproject.toml)이 소유한다.

[`uv.lock`](uv.lock)은 실제 실행 dependency를 고정한다. Dependency를 갱신할 때는 Unit 0의 정상 실행과 current context
변형을 다시 검증한다. Deck directory에서 다음 명령으로 console evidence의 관계를 검사할 수 있다.

```bash
uv run --locked python -m unittest discover -s tests -v
```

검사는 별도 process에서 실행하며 외부 `OTEL_*` 설정을 제거해 실습의 기본 SDK 환경을 유지한다. 직접 실습할 때도 별도
instrumentation 없이 실행하고, sampling 등을 바꾸는 `OTEL_*` 설정이 없는 환경을 사용한다.

## Build progress

- Curriculum baseline: 이 README의 Goal, Prerequisites, Learning scope, Learning path.
- Unit 0: 정상 실행과 호출 한 줄을 current span 밖으로 옮기는 변형을 검증했다. 세 span의 identifier 관계, attribute,
  `service.name`을 실제 `ConsoleSpanExporter` output에서 확인했다.
- 검증 환경: 2026-10-01, Python 3.14.6, OpenTelemetry API/SDK 1.45.0. Python 3.10+ 전체 matrix는 검증하지 않았다.
- Unit 0의 설명, 예측, 관찰, 변형, checkpoint를 검토했다. 학습자 평가와 external backend 검증은 수행하지 않았다.
- 다음 increment: Unit 1의 span data와 failure evidence. Unit 1–7은 미구현이며 deck 전체는 아직 완료되지 않았다.
- 현재 curriculum 변경 후보와 slice 간 integration finding은 없다.

## Version baseline

작성/검토 기준일: **2026-09-29**

- Python: 3.10+
- OpenTelemetry Python SDK reviewed baseline: `1.45.0`
- dependency range: `opentelemetry-api>=1.45,<2`, `opentelemetry-sdk>=1.45,<2`
- Traces / Metrics: Stable
- Logs: Development

`1.45.0`은 현재 material을 검토한 calibration version이다. Compatible update를 허용하되 lockfile을 도입한 뒤에는 실제
학습 실행 환경을 lockfile로 재현한다.

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Python manual instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [Python exporters](https://opentelemetry.io/docs/languages/python/exporters/)
- [Python propagation](https://opentelemetry.io/docs/languages/python/propagation/)
