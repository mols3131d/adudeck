# PR #33 · OpenTelemetry 덱 잔여 작업 보고서

작성일: 2026-10-01. 갱신일: 2026-10-02.

현재 구현은 Unit 0–2까지다. 우선 Unit 2 검토 사항과 저장소 환경 관리 누락을 보완한 뒤,
Unit 3–9를 작은 단위로 구현하고 최종 통합 검토를 진행한다.

Curriculum과 진행 상태의 기준은 [덱 README](../../decks/systems-opentelemetry/README.md)다.
이 보고서는 임시 작업 인계 자료이며, 커리큘럼이나 PR 범위를 독자적으로 변경하지 않는다.

## 현재 상태

- PR: [#33 · feat(opentelemetry): build hands-on learning deck](https://github.com/mols3131d/adudeck/pull/33)
- Branch: `feat/opentelemetry-deck-foundation` → `main`, Draft.
- 현재 구현: `00-intro` → `01-setup` → `02-first-trace`.
- Unit 2 구현과 기존 로컬 검토 완료: 첫 trace, identifier 관계, parent context 복원, context 변형, transfer 평가.
  후속 문서 검토에서 발견한 세 보완 항목은 아래 체크리스트에 남아 있다.
- `uv.lock` 추가. Python 3.14.6, OpenTelemetry API/SDK 1.45.0으로 실행 검증.
- 정상 실행과 context 변형을 실제 console JSON으로 검사하는 테스트 2개 통과.
- Python 3.10+ 전체 matrix, 학습자 평가, Collector 전송, backend UI는 아직 검증하지 않았다.
- Unit 3–9은 미구현이다. Deck 전체 완료를 선언하지 않는다.

이번 갱신은 최신 PR 본문·코멘트, 덱 README, Unit 2 본문과 setup/update 스크립트를 대조한 문서 작업이다.
위 실행 결과는 기존에 기록된 검증 이력이며, 이번 보고서 작성에서 runtime 테스트나 원격 CI를 재실행하지 않았다.

## 실행 우선순위

| 순서 | 작업 | 현재 상태 | 완료 기준 |
| --- | --- | --- | --- |
| 1 | Unit 2 문서 보완 | 검토 사항 세 개 미반영 | 식별자 비교와 컨텍스트 복원 문제의 의미가 명확하다. |
| 2 | setup/update 환경 관리 연동 | OpenTelemetry 덱 처리 누락 확인 | 기존 explicit project 방식으로 환경 동기화·갱신을 처리하고 관련 검증을 통과한다. |
| 3 | PR 범위와 조사 권고 판단 | 미결정 | Agent Asset 변경의 처리와 curriculum 변경 후보의 채택·보류를 기록한다. |
| 4 | Unit 3 구현 | 미구현 | 성공·실패 의미와 telemetry 차이를 설명·실습·평가하고 실제 출력으로 검증한다. |
| 5 | Unit 4–9 순차 구현 | 미구현 | 각 단위의 공통 acceptance를 충족한 뒤 다음 단위로 진행한다. |
| 6 | 최종 통합 검토 | 미착수 | 학습 목표의 설명·실습·평가, 실행 검증, 최종 테스트·CI와 진행 상태가 일치한다. |

Unit 3를 시작할 때는 framework, Collector, backend를 추가하지 않는다. 현재 local console 환경을 재사용한다.
후속 단위의 상세 작업은 이 보고서의 Unit별 계획을 따른다.

## 우선 보완 체크리스트

### Unit 2 · 첫 트레이스

대상: [첫 트레이스 교재](../../decks/systems-opentelemetry/textbook/02-first-trace/README.md).

- [ ] **`service.name`과 동일 Resource를 구분한다.** 같은 서비스 이름은 같은 Resource나 프로세스라는 증거가 아니다.
  관찰 항목은 서비스 이름의 일치를 확인하도록 바꾸고, 이 예제의 Resource 공유는 하나의 provider 구성으로 설명한다.
- [ ] **적용 문제의 컨텍스트 조건을 명시한다.** 동기식 `start_as_current_span()` 블록을 중첩하고,
  `import_job` 시작 전에는 활성 스팬이 없다고 가정한다. “스팬이 끝난 직후” 대신
  “해당 `with` 블록을 빠져나온 직후”를 물어 종료와 컨텍스트 복원을 혼동하지 않게 한다.
- [ ] **변형 실험에서 같은 실행 안의 관계를 묻는다.** “`trace_id`는 이전과 같을까?”를
  “이번 실행에서도 `charge_payment`는 `checkout`과 같은 `trace_id`를 가질까?”로 바꾼다.

보완 후 정상 실행과 들여쓰기 변형의 관계가 본문 설명과 일치하는지 확인한다.
함수 호출만으로 스팬이 생기지 않는다는 반복 설명의 통합은 선택적인 가독성 개선이다.

### 저장소 환경 관리와 PR 범위

- [ ] [setup 스크립트](../../scripts/setup.sh)에 덱의 locked dependency 동기화를 연결한다.
- [ ] [update 스크립트](../../scripts/update.sh)에 덱의 lockfile 갱신과 환경 동기화를 연결한다.
- [ ] 변경한 shell 구문의 유효성을 확인하고, 덱 테스트로 갱신된 환경의 정상 실행과 변형 실험을 확인한다.
  실제 setup/update를 실행하지 않았다면 구문 검사만으로 전체 workflow 검증을 주장하지 않는다.
- [ ] 덱과 독립적인 ELI5 Skill 도입 등 Agent Asset 변경을 같은 PR에 유지할지 검토한다.
  분리는 미확정이며, 결정 전 기존 변경을 제거하거나 이 보고서 작성만으로 별도 PR을 만들지 않는다.

## 2026-10-02 조사 권고와 미결정 사항

@mols3131d가 PR #33에 추가한 `OpenTelemetry textbook research — 2026-10-02` 코멘트를 요약한 작업 후보다.
코멘트는 research evidence이며, 다음 권고가 채택된 curriculum이라는 뜻은 아니다.
Version-sensitive 주장은 구현 시점의 공식 문서·specification과 실제 runtime으로 다시 확인한다.

- [ ] **Semantic Conventions 학습 목표의 채택 여부를 결정한다.** 공통 이름·attribute·metric 단위가
  instrumentation 간 의미를 맞추는 원리를 Unit 3·5·8에 연결하는 후보다. 채택하면 덱 README의 학습 목표와
  평가 책임을 함께 갱신하고, 채택·보류 이유를 기록한다. 새 단위를 만드는 것이 전제는 아니다.
- [ ] **Unit 3 실패 설명의 기준을 대조한다.** 코멘트는 `span status=Error`, 낮은 cardinality의 `error.type`,
  exception의 log record 기록 방향을 권고한다. 기존 계획의 span exception event 실습과 최신 규약 사이의
  차이·안정성·SDK 지원 여부를 확인하고, `record_exception()`을 유일하거나 영구적인 표준 경로로 설명하지 않는다.
- [ ] **현재 범위 안에서 설명을 보강할지 검토한다.** 아래 후보는 해당 Unit 작성 시 누락 여부를 점검한다.

| 대상 | 보강 후보 |
| --- | --- |
| Intro | OpenTelemetry의 생성·수집·전송 책임과 저장·검색·UI 백엔드의 책임을 명시한다. |
| Unit 4 | Resource와 Instrumentation Scope를 구분하고 provider → processor → exporter의 역할을 연결한다. |
| Unit 5 | manual, instrumentation library, zero-code의 차이와 framework span·business span의 상호 보완을 설명한다. |
| Unit 6 | in-process Context와 cross-process Propagation을 구분한다. Baggage는 span attribute의 자동 전파가 아님을 밝힌다. |
| Unit 7 | Collector component 선언과 `service.pipelines` 연결을 구분하는 실패 실험을 검토한다. |
| Unit 8 | instrument 선택 근거와 attribute 조합에 따른 timeseries cardinality를 함께 관찰한다. |
| Unit 9 | 고장을 하나씩 주입해 경계별 근거로 진단한다. 데이터 부재가 항상 pipeline 고장인 것은 아님을 sampling 언급으로 보완한다. |

Logs 심화, advanced/tail sampling, production 운영으로 범위를 확대하지 않는다.
공식 Demo 분석은 core 완료 후 선택 과제이며, Ready 전환과 merge는 별도 요청 사항이다.

## 2026-10-01 최신 tutorial 조사

### 현재 version calibration

후속 구현에서 version-sensitive 동작은 다음 기준으로 다시 검증한다.

- OpenTelemetry Python API/SDK: `1.45.0` — 2026-09-25 release, Python 3.10+.
- Python distro / instrumentation 계열: `0.66b0` — 2026-09-25 release. Contrib instrumentation은 Beta lifecycle을
  가진다.
- OTLP exporter: `1.45.0`.
- OpenTelemetry Collector: `0.162.0` — 2026-09-29 release.
- OpenTelemetry Demo: `3.1.0` — 2026-09-18 release. `3.0.0`은 load-generator licensing 문제로 사용하지 않는다.

Version은 기억이나 vendor tutorial의 pin을 그대로 사용하지 않고 구현 시점의 official release/source를 다시 확인한다.

### 우선 참고할 tutorial / guide

1. **OpenTelemetry official Python documentation**
   - Getting Started, manual instrumentation, instrumentation libraries, zero-code, propagation, cookbook을 canonical
     behavior source로 사용한다.
   - 현재 deck의 manual-first 학습 방식은 유지한다. Official five-minute quickstart는 Flask auto-instrumentation부터
     시작하지만, 이 deck에서는 먼저 span/context 관계를 이해한 뒤 같은 application을 library/zero-code
     instrumentation으로 바꿔 비교한다.
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
   - 처음부터 실행하는 tutorial이 아니라 Unit 9 이후 실제 multi-service reference implementation을 읽는 optional
     capstone으로 사용한다.

### 최신 동작에서 특히 주의할 점

- Python Traces와 Metrics는 Stable, Logs는 Development이므로 beginner core는 traces → metrics 순서를 유지한다.
- Python default propagation은 W3C Trace Context와 W3C Baggage다.
- HTTP/database stable semantic conventions는 Python 1.44.0 / instrumentation 0.65b0부터 opt-in support가 있다.
  현재 instrumentation은 `OTEL_SEMCONV_STABILITY_OPT_IN`을 사용해 stable convention을 선택할 수 있으므로 Unit 5의
  learner-visible field를 검증할 때 convention mode를 명시해 version drift를 줄인다.
- Exception 기록과 span status는 같은 개념이 아니다. Unit 3에서는 `record_exception()`과 `StatusCode.ERROR`가 각각
  남기는 evidence를 분리해서 관찰하고, exact behavior는 SDK 1.45.0에서 실행 검증한다.
- OTLP transport를 배울 때는 Python convenience meta-package보다 선택한 protocol의 구체 exporter package를 우선한다.
  이 deck에서는 HTTP/protobuf와 port 4318을 기본 후보로 삼아 gRPC 자체가 학습 노이즈가 되지 않게 한다.

## 구현 전 repository 정리 후보

Unit 3 착수 전 위 체크리스트에 따라 현재 PR의 repository consistency를 정리한다.

1. `scripts/setup.sh`와 `scripts/update.sh`가 `decks/systems-opentelemetry`를 repository-managed uv project로 함께
   처리하도록 기존 explicit project pattern에 맞춰 보완한다.
2. OpenTelemetry deck 구현과 독립적인 repository-wide Agent Asset 변경은 같은 PR에 둘 필요가 있는지 다시 확인한다.
   별도 책임이라면 후속/별도 PR로 분리한다.
3. Deck build state는 deck README를 canonical owner로 유지하고, 이 inbox 문서는 작업 인계에 필요한 planning detail만
   둔다.

## 다음 착수 범위: Unit 3 · Span data와 failure evidence

기존 Unit 2의 작은 local console 환경을 그대로 사용한다. Framework, Collector, backend는 아직 추가하지 않는다.

아래 내용은 2026-10-01의 구현 계획이다. 구현 전에 위 2026-10-02 조사 권고와 대조해 예외 기록 방식의
현재 규약과 SDK 동작을 확인한다. 특히 처리되거나 재시도된 예외를 작업의 최종 실패와 자동으로 동일시하지 않는다.
학습 범위나 평가 목표를 바꾸는 결정은 먼저 덱 README에 반영하고, 보류한 후보를 확정된 요구처럼 구현하지 않는다.

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
4. console JSON에서 `status`, `events`, `exception.type`, `exception.message` 등 현재 SDK가 실제로 내보내는 evidence를
   찾는다.
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
- framework/library instrumentation이 header inject/extract를 대신할 때도 current context가 핵심이라는 Unit 2 mental
  model을 유지한다.

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

Official Python Metrics API를 canonical source로 하고 Better Stack 등의 실전 guide를 instrument-selection 사례로
교차검토한다.

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

먼저 정상 trace/metric이 UI에서 앞선 raw evidence와 같은 execution을 가리키는지 확인한다. 그 다음 controlled failure를
준다.

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
- 이미 배운 instrumentation, propagation, Collector, Resource, metrics 개념이 실제 multi-language system에서 어디에
  있는지 찾아보는 repository exploration 과제로 사용한다.
- `3.0.0`은 사용하지 않고 current `3.1.0` 이상에서 다시 version을 확인한다.

## 각 increment의 공통 acceptance

각 단위는 다음을 모두 만족해야 다음 unit으로 넘어간다.

1. conceptual model이 앞선 unit의 mental model과 이어진다.
2. learner가 실행 전에 observable relationship을 예측한다.
3. runnable experiment에서 intermediate evidence를 직접 본다.
4. 한 learning-relevant condition을 바꾸고 결과 차이와 invariant를 설명한다.
5. 테스트는 command success가 아니라 learner-visible evidence를 검사한다.
6. version-sensitive behavior는 current official source와 실제 runtime 양쪽에서 확인한다.
7. vendor tutorial은 workflow 아이디어의 보조 근거로만 쓰고 technical contract는 official OpenTelemetry source로
   검증한다.
8. Deck README의 build progress와 PR body의 validation claim을 실제 검증 범위까지만 갱신한다.
9. 해당 학습 목표를 새로운 사례에 적용하는 문제와 스스로 판단할 기준을 제공한다.

## 최종 통합 검토와 완료 조건

- [ ] 용어와 mental model이 unit 사이에서 일관적인지 확인한다.
- [ ] Prerequisite와 개념 순서를 점검하고, 설명 전에 사용하는 개념을 보완한다.
- [ ] 각 학습 목표에 충분한 설명·실습·평가가 연결되는지 확인한다.
- [ ] 교재가 독립적인 주 학습 자료로 역할을 하는지 검토한다.
- [ ] 필요한 playground의 실제 실행과 관찰 evidence를 검증한다.
- [ ] Curriculum 변경과 integration finding을 해결한다.
- [ ] 조사 권고의 채택·보류를 기록하고, 채택된 목표가 설명·실습·평가에 반영됐는지 확인한다.
- [ ] 완료 주장에 필요한 검증 한계를 해결하고, 남는 한계는 명시한다.
  Python 3.10+ 지원 선언과 실제 실행한 버전의 범위, 학습자 평가 여부를 구분한다.
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

Repository guidance와 deck README를 읽고, 현재 head에서 미완료 범위를 재확인한 뒤 repository 정리 후보와 Unit 3부터
진행한다. 먼저 Unit 2 보완 체크리스트와 조사 권고의 결정 상태를 확인한다.

## Research references

Canonical:

- <https://opentelemetry.io/docs/languages/python/>
- <https://opentelemetry.io/docs/languages/python/getting-started/>
- <https://opentelemetry.io/docs/languages/python/instrumentation/>
- <https://opentelemetry.io/docs/languages/python/libraries/>
- <https://opentelemetry.io/docs/zero-code/python/>
- <https://opentelemetry.io/docs/languages/python/propagation/>
- <https://opentelemetry.io/docs/collector/quick-start/>
- <https://opentelemetry.io/docs/demo/>

Comparative tutorials:

- <https://grafana.com/docs/opentelemetry/docker-lgtm/>
- <https://grafana.com/events/grafanacon/hands-on-labs/opentelemetry-instrumentation/>
- <https://signoz.io/opentelemetry/python/>
- <https://betterstack.com/community/guides/observability/opentelemetry-sdk/>
- <https://betterstack.com/community/guides/observability/otel-metrics-python/>
- <https://docs.honeycomb.io/send-data>
- <https://uptrace.dev/get/opentelemetry-python>
