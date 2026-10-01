# PR #33 · OpenTelemetry deck 남은 작업

2026-10-01 기준 작업 인계 메모다. Curriculum과 진행 상태의 기준은
[deck README](../../decks/systems-opentelemetry/README.md)이며, 이 문서는 후속 작업을 위한 임시 정리다.

## 현재 상태

- PR: [#33 · feat(opentelemetry): build hands-on learning deck](https://github.com/mols3131d/adudeck/pull/33)
- Branch: `feat/opentelemetry-deck-foundation` → `main`, Draft.
- 현재 구현: `00-intro` → `01-setup` → `02-first-trace`.
- Unit 2 구현과 로컬 검토 완료: 첫 trace, identifier 관계, parent context 복원, context 변형, transfer 평가.
- `uv.lock` 추가. Python 3.14.6, OpenTelemetry API/SDK 1.45.0으로 실행 검증.
- 정상 실행과 context 변형을 실제 console JSON으로 검사하는 테스트 2개 통과.
- Python 3.10+ 전체 matrix, 학습자 평가, Collector 전송, backend UI는 아직 검증하지 않았다.
- Unit 3–9은 미구현이다. Deck 전체 완료를 선언하지 않는다.

## 2026-10-01 최신 tutorial 조사

### 현재 version calibration

후속 구현에서 version-sensitive 동작은 다음 기준으로 다시 검증한다.

- OpenTelemetry Python API/SDK: `1.45.0` — 2026-09-25 release, Python 3.10+.
- Python distro / instrumentation 계열: `0.66b0` — 2026-09-25 release. Contrib instrumentation은 Beta lifecycle을 가진다.
- OTLP exporter: `1.45.0`.
- OpenTelemetry Collector: `0.162.0` — 2026-09-29 release.
- OpenTelemetry Demo: `3.1.0` — 2026-09-18 release. `3.0.0`은 load-generator licensing 문제로 사용하지 않는다.

Version은 기억이나 vendor tutorial의 pin을 그대로 사용하지 않고 구현 시점의 official release/source를 다시 확인한다.

### 우선 참고할 tutorial / guide

1. **OpenTelemetry official Python documentation**
   - Getting Started, manual instrumentation, instrumentation libraries, zero-code, propagation, cookbook을 canonical behavior source로 사용한다.
   - 현재 deck의 manual-first 학습 방식은 유지한다. Official five-minute quickstart는 Flask auto-instrumentation부터 시작하지만,
     이 deck에서는 먼저 span/context 관계를 이해한 뒤 같은 application을 library/zero-code instrumentation으로 바꿔 비교한다.
2. **OpenTelemetry Collector official Quick Start**
   - Collector를 receiver → processor → exporter pipeline으로 이해하는 Unit 7의 기준으로 사용한다.
   - 별도 backend 없이 OTLP receiver와 debug exporter에서 먼저 evidence를 확인한다.
3. **Grafana OpenTelemetry / LGTM documentation and GrafanaCON 2026 instrumentation lab**
   - instrumentation 수준 선택 → SDK → end-to-end export → LGTM에서 관찰하는 실제 사용자 흐름을 참고한다.
   - `grafana/otel-lgtm`은 production architecture가 아니라 마지막 local visualization/diagnosis 환경으로만 사용한다.
4. **SigNoz Python tutorial series**
   - Flask와 zero-code instrumentation을 사용한 end-to-end onboarding 흐름을 참고한다.
   - 문서는 2026년에 갱신됐지만 일부 guide의 tested SDK가 1.27.0이므로 version authority로 사용하지 않는다.
5. **Better Stack OpenTelemetry guides**
   - SDK component 설명, metrics instrument 선택, production best-practice 관점을 교차검토하는 데 사용한다.
   - vendor recommendation인 auto-instrumentation-first를 학습 순서의 근거로 그대로 채택하지 않는다.
6. **Honeycomb / Uptrace guides**
   - OTLP backend portability, service/resource naming, 실제 telemetry 질문 설계의 보조 참고로 사용한다.
   - archived Honeycomb Python distro나 vendor wrapper를 deck의 canonical setup으로 사용하지 않는다.
7. **OpenTelemetry Demo 3.1.0**
   - 처음부터 실행하는 tutorial이 아니라 Unit 9 이후 실제 multi-service reference implementation을 읽는 optional capstone으로 사용한다.

### 최신 동작에서 특히 주의할 점

- Python Traces와 Metrics는 Stable, Logs는 Development이므로 beginner core는 traces → metrics 순서를 유지한다.
- Python default propagation은 W3C Trace Context와 W3C Baggage다.
- HTTP/database stable semantic conventions는 Python 1.44.0 / instrumentation 0.65b0부터 opt-in support가 있다.
  현재 instrumentation은 `OTEL_SEMCONV_STABILITY_OPT_IN`을 사용해 stable convention을 선택할 수 있으므로 Unit 5의
  learner-visible field를 검증할 때 convention mode를 명시해 version drift를 줄인다.
- Exception 기록과 span status는 같은 개념이 아니다. Unit 3에서는 `record_exception()`과 `StatusCode.ERROR`가 각각 남기는
  evidence를 분리해서 관찰하고, exact behavior는 SDK 1.45.0에서 실행 검증한다.
- OTLP transport를 배울 때는 Python convenience meta-package보다 선택한 protocol의 구체 exporter package를 우선한다.
  이 deck에서는 HTTP/protobuf와 port 4318을 기본 후보로 삼아 gRPC 자체가 학습 노이즈가 되지 않게 한다.

## 구현 전 repository 정리 후보

Unit 3 착수 전 현재 PR의 repository consistency를 한 번 정리한다.

1. `scripts/setup.sh`와 `scripts/update.sh`가 `decks/systems-opentelemetry`를 repository-managed uv project로 함께 처리하도록
   기존 explicit project pattern에 맞춰 보완한다.
2. OpenTelemetry deck 구현과 독립적인 repository-wide Agent Asset 변경은 같은 PR에 둘 필요가 있는지 다시 확인한다.
   별도 책임이라면 후속/별도 PR로 분리한다.
3. Deck build state는 deck README를 canonical owner로 유지하고, 이 inbox 문서는 작업 인계에 필요한 planning detail만 둔다.

## 다음 착수 범위: Unit 3 · Span data와 failure evidence

기존 Unit 2의 작은 local console 환경을 그대로 사용한다. Framework, Collector, backend는 아직 추가하지 않는다.

### 학습 목표

- attribute, event, status, exception event가 각각 어떤 질문에 답하는지 구분한다.
- 실패가 발생했다는 사실과 exception detail이 같은 정보가 아님을 설명한다.
- 성공 span과 실패 span의 learner-visible console evidence를 비교한다.
- 실패를 관찰하기 위한 instrumentation이 application failure semantics를 임의로 바꾸지 않아야 함을 설명한다.

### 실습 형태

```text
같은 operation
├─ success case
└─ controlled failure case
```

1. 실행 전에 status, event, exception attribute가 어떻게 달라질지 예측한다.
2. 성공 operation에 일반 attribute와 의미 있는 event를 남긴다.
3. 통제된 exception case에서 `record_exception()`과 `set_status(StatusCode.ERROR)`의 결과를 관찰한다.
4. console JSON에서 `status`, `events`, `exception.type`, `exception.message` 등 현재 SDK가 실제로 내보내는 evidence를 찾는다.
5. parent/trace 관계는 Unit 2와 동일하게 유지되는지 확인한다.
6. 한 가지 조건만 바꾼 variation으로 “exception을 기록했지만 status를 바꾸지 않은 경우” 또는 그 반대를 비교한다.
7. 테스트는 process 성공 여부가 아니라 learner-visible span evidence 차이를 검사한다.
8. 현재 Python manual instrumentation 문서와 Trace/Exception specification을 근거로 exact behavior를 검증한다.

Unit 3에서는 semantic-convention 전체를 가르치지 않는다. Exception field naming처럼 실습 해석에 필요한 부분만 소개한다.

## 이후 구현 순서

### Unit 4 · Resource + API / SDK boundary

Official Python manual instrumentation의 app/library boundary를 학습 대상으로 삼는다.

- library-side code는 OpenTelemetry API에만 의존한다.
- application이 SDK와 `TracerProvider`를 구성할 때 실제 recording/export가 생기는 것을 비교한다.
- `Resource`와 `service.name`을 “telemetry 발생 주체”로 연결한다.
- instrumentation scope가 tracer를 만든 instrumentation/library identity라는 점을 output에서 확인한다.
- processor/exporter는 data pipeline owner로 소개하되 Batch/OTLP 상세는 후속 unit에 남긴다.

핵심 실험 후보:

```text
same instrumented function
├─ SDK provider 없음 → recording/export evidence 없음
└─ SDK provider 구성 → span evidence 생성
```

### Unit 5 · Manual → library → zero-code instrumentation

Official Python Getting Started와 instrumentation-library/zero-code guide, GrafanaCON 2026 lab의 progression을 참고한다.

- 작은 Flask application 하나를 사용한다.
- 같은 HTTP endpoint를 manual span, Flask instrumentation library, `opentelemetry-instrument` 방식으로 비교한다.
- framework span과 business span의 책임 차이를 설명한다.
- `opentelemetry-distro` / Flask instrumentation `0.66b0` 계열을 lockfile로 고정해 실행한다.
- stable HTTP semantic convention을 사용할 경우 `OTEL_SEMCONV_STABILITY_OPT_IN=http`을 명시하고 output field contract를
  해당 mode에서만 검사한다.
- `opentelemetry-bootstrap`은 편의 automation으로 설명하고, 무엇을 설치했는지 감추는 magic으로 가르치지 않는다.

### Unit 6 · Cross-service context propagation

두 개의 작은 service를 처음 도입한다.

```text
client → service A → HTTP → service B
```

- 정상 상태에서 같은 `trace_id`가 service boundary를 넘어 이어지는지 확인한다.
- W3C `traceparent`가 carrier를 통해 전달되는 evidence를 관찰한다.
- propagation을 의도적으로 끊고 두 trace로 분리되는 것을 비교한다.
- Baggage는 Trace Context와 역할이 다르다는 정도만 소개하고 core exercise로 확대하지 않는다.
- framework/library instrumentation이 header inject/extract를 대신할 때도 current context가 핵심이라는 Unit 2 mental model을 유지한다.

### Unit 7 · OTLP + Collector boundary

Official Collector Quick Start를 기준으로 하되 deck의 Python application을 telemetry source로 재사용한다.

```text
Python app
  ↓ OTLP/HTTP :4318
Collector 0.162.0
  ↓ debug exporter
terminal
```

- `opentelemetry-exporter-otlp-proto-http`를 기본 후보로 사용한다.
- Collector는 Docker로 격리하고 version tag를 명시한다.
- 최소 config는 OTLP receiver → optional batch processor → debug exporter로 시작한다.
- 먼저 processor 없이 receive/export boundary를 확인한 뒤, 필요할 때 batch/resource processor를 하나씩 추가한다.
- application console exporter와 Collector debug output이 서로 다른 process boundary의 evidence임을 구분한다.
- Collector가 꺼졌거나 endpoint가 틀렸을 때 application business behavior와 telemetry export failure를 구분한다.

### Unit 8 · Metrics

Official Python Metrics API를 canonical source로 하고 Better Stack 등의 실전 guide를 instrument-selection 사례로 교차검토한다.

Core instrument는 현재 outcome에 맞춰 세 개만 다룬다.

```text
requests_total     → Counter
active_requests    → UpDownCounter
request_duration   → Histogram
```

- 먼저 ConsoleMetricExporter로 measurement/aggregation evidence를 확인한다.
- 이후 Unit 7의 Collector pipeline으로 같은 metrics를 보낸다.
- Gauge와 asynchronous instrument는 beginner core에서 제외하거나 optional note로 남긴다.
- attribute cardinality를 작은 variation으로 보여 주되 production cost engineering 전체로 확장하지 않는다.

### Unit 9 · Backend + telemetry pipeline diagnosis

Grafana의 `grafana/otel-lgtm`을 local development backend로 사용해 마지막 boundary를 추가한다.

```text
application
→ instrumentation
→ SDK/exporter
→ OTLP
→ Collector
→ Tempo / Mimir
→ Grafana
```

먼저 정상 trace/metric이 UI에서 앞선 raw evidence와 같은 execution을 가리키는지 확인한다. 그 다음 controlled failure를 준다.

- instrumentation 제거
- propagation 단절
- OTLP endpoint 오류
- Collector 중지 또는 receiver config 오류
- `service.name` 누락/변경

학습자는 “Grafana에 안 보인다”를 하나의 failure로 다루지 않고 어느 boundary까지 evidence가 존재하는지 따라가며 원인을
좁힌다. Vendor UI 사용법 자체는 학습 목표가 아니다.

## Optional capstone · OpenTelemetry Demo 3.1.0 읽기

Core completion 뒤에만 진행한다.

- 공식 Astronomy Shop Demo를 처음부터 구축하지 않는다.
- 이미 배운 instrumentation, propagation, Collector, Resource, metrics 개념이 실제 multi-language system에서 어디에 있는지
  찾아보는 repository exploration 과제로 사용한다.
- `3.0.0`은 사용하지 않고 current `3.1.0` 이상에서 다시 version을 확인한다.

## 각 increment의 공통 acceptance

각 단위는 다음을 모두 만족해야 다음 unit으로 넘어간다.

1. conceptual model이 앞선 unit의 mental model과 이어진다.
2. learner가 실행 전에 observable relationship을 예측한다.
3. runnable experiment에서 intermediate evidence를 직접 본다.
4. 한 learning-relevant condition을 바꾸고 결과 차이와 invariant를 설명한다.
5. 테스트는 command success가 아니라 learner-visible evidence를 검사한다.
6. version-sensitive behavior는 current official source와 실제 runtime 양쪽에서 확인한다.
7. vendor tutorial은 workflow 아이디어의 보조 근거로만 쓰고 technical contract는 official OpenTelemetry source로 검증한다.
8. Deck README의 build progress와 PR body의 validation claim을 실제 검증 범위까지만 갱신한다.

## 최종 통합 검토와 완료 조건

- [ ] 용어와 mental model이 unit 사이에서 일관적인지 확인한다.
- [ ] Prerequisite와 개념 순서를 점검하고, 설명 전에 사용하는 개념을 보완한다.
- [ ] 각 학습 목표에 충분한 설명·실습·평가가 연결되는지 확인한다.
- [ ] 교재가 독립적인 주 학습 자료로 역할을 하는지 검토한다.
- [ ] 필요한 playground의 실제 실행과 관찰 evidence를 검증한다.
- [ ] Curriculum 변경과 integration finding을 해결한다.
- [ ] 완료 주장에 필요한 검증 한계를 해결하고, 남는 한계는 명시한다.
- [ ] 최종 revision에 맞춰 전체 테스트와 CI 결과를 확인한다.
- [ ] Deck README와 PR 본문을 최종 구현 상태로 갱신한다.

Ready 전환과 merge는 별도 요청에 따라 진행한다. Deck의 완료와 storage state 변경도 별개다.

## 재개 시 확인

이 메모 작성 뒤 branch나 PR이 바뀔 수 있으므로 먼저 현재 상태를 확인한다.

```bash
git status --short --branch
gh pr view 33 --json headRefOid,isDraft,state,body
gh pr checks 33
mise run test:opentelemetry-deck
```

Repository guidance와 deck README를 읽고, 현재 head에서 미완료 범위를 재확인한 뒤 repository 정리 후보와 Unit 3부터 진행한다.

## Research references

Canonical:

- https://opentelemetry.io/docs/languages/python/
- https://opentelemetry.io/docs/languages/python/getting-started/
- https://opentelemetry.io/docs/languages/python/instrumentation/
- https://opentelemetry.io/docs/languages/python/libraries/
- https://opentelemetry.io/docs/zero-code/python/
- https://opentelemetry.io/docs/languages/python/propagation/
- https://opentelemetry.io/docs/collector/quick-start/
- https://opentelemetry.io/docs/demo/

Comparative tutorials:

- https://grafana.com/docs/opentelemetry/docker-lgtm/
- https://grafana.com/events/grafanacon/hands-on-labs/opentelemetry-instrumentation/
- https://signoz.io/opentelemetry/python/
- https://betterstack.com/community/guides/observability/opentelemetry-sdk/
- https://betterstack.com/community/guides/observability/otel-metrics-python/
- https://docs.honeycomb.io/send-data
- https://uptrace.dev/get/opentelemetry-python
