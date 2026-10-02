# PR #33 · OpenTelemetry textbook 엄격 self-review

작성일: 2026-10-02  
검토 revision: `2c557ae984d699b0e42da75b752eb4de4e213098`  
대상: `decks/systems-opentelemetry/textbook/`과 이를 직접 소유·검증하는 deck README, tests, dependency/runtime integration

## 결론

현재 textbook은 **방향과 학습 progression이 강한 draft**다. 특히 mechanism-first 순서, Unit 2의 calibration pattern,
Unit 3·4·6·8의 learner-visible evidence test, Unit 9의 hop-by-hop diagnosis framing은 유지할 가치가 높다.

하지만 **아직 textbook quality-pass 또는 PR Ready로 판정하면 안 된다.**

핵심 이유는 네 가지다.

1. core path인 Unit 5와 Unit 7이 아직 end-to-end runtime validation을 통과하지 않았다.
2. Unit 9의 trace/metric correlation 목표에는 현재 material이 지원하지 않는 개별 execution correlation 주장이 섞여 있다.
3. Unit 3과 Unit 4에 현재 OpenTelemetry contract와 더 정확히 맞춰야 하는 factual/mental-model gap이 있다.
4. hands-on path의 reproducibility, safety, reset, repository lifecycle이 core textbook의 품질에 아직 못 미친다.

따라서 현재 상태는 **Draft 유지**가 맞다.

### Severity 요약

| 등급 | 수 | 의미 |
| --- | ---: | --- |
| P0 | 2 | completion/quality-pass를 막는 핵심 gap |
| P1 | 8 | Ready 전에 수정하는 것이 강하게 권장되는 material gap |
| P2 | 5 | correctness보다 유지보수·명료성·학습 UX 개선 |

## 검토 방법과 evidence boundary

이번 리뷰는 한 관점으로 읽고 끝내지 않고 다음 순서로 수행했다.

1. **Quality pass** — curriculum outcome, textbook contract, 개념 의존성, explanation/practice/assessment를 검토했다.
2. **Adversarial pass** — hidden prerequisite, partial failure, network exposure, mutation/reset, CI blind spot, version drift를 검토했다.
3. **Consistency pass** — deck README ↔ textbook ↔ runnable artifacts ↔ tests ↔ repository lifecycle을 대조했다.
4. **External correctness pass** — version-sensitive 항목은 현재 OpenTelemetry/Docker primary source와 다시 대조했다.
5. **Reconciliation** — 단순 취향이나 외부 best practice는 finding에서 제외하고, 현재 deck contract나 실제 학습 경로에 영향을 주는 항목만 남겼다.

현재 head의 repository CI `ci/validated`는 success다. 다만 현재 CI가 Unit 5 Flask zero-code와 Unit 7 Collector container
경로를 실행하지 않는다는 사실 자체가 아래 P0 finding에 포함된다.

이 runtime에서는 nested review subagent를 실제로 독립 호출하지 못했으므로 “독립 reviewer 두 명이 검증했다”고 주장하지
않는다. 대신 quality/challenge lens를 분리한 sequential pass를 사용했다.

---

# P0 · completion blocker

## P0-01 · Unit 5와 Unit 7은 core outcome인데 end-to-end runtime evidence가 없다

### Evidence

Deck curriculum은 다음을 substantial outcome으로 둔다.

- manual instrumentation과 library/zero-code instrumentation 비교
- OTLP를 통해 application telemetry가 Collector로 이동하는 경계 추적

하지만 현재 repository-managed tests는 Unit 2, 3, 4, 6, 8만 runtime으로 확인한다.
`decks/systems-opentelemetry/README.md`와 PR body도 Unit 5와 Unit 7 full runtime validation이 남았음을 명시한다.

Unit 5는 실제로 다음 external runtime surface를 추가한다.

- Flask 3.1.3
- `opentelemetry-distro==0.66b0`
- `opentelemetry-instrumentation-flask==0.66b0`
- `opentelemetry-instrument`

Unit 7은 다음을 추가한다.

- `opentelemetry-exporter-otlp-proto-http==1.45.0`
- Docker/container runtime
- Collector 0.162.0
- OTLP/HTTP transport
- receiver → processor → exporter pipeline

### Impact

이 두 unit은 textbook에서 가장 version/environment-sensitive한 부분이다. prose와 config가 그럴듯해 보여도 실제 learner path가
깨질 가능성이 가장 높다. `adudeck-deck-build` contract상 hands-on outcome에 필요한 runtime boundary가 미검증이면 completion을
선언할 수 없다.

### Required action

Ready 전 최소 validation:

- Unit 5: clean environment에서 plain Flask → zero-code Flask를 실제 요청까지 실행하고 span evidence를 비교한다.
- Unit 7: pinned Collector image를 pull/run하고 Python span이 OTLP/HTTP → Collector → debug exporter까지 도달하는 것을 확인한다.
- 실패 변형도 최소 한 개씩 실행해 happy path만 검증하지 않는다.
- 실행 결과를 CI에 넣을지 manual acceptance로 둘지는 별도 판단 가능하지만, validation boundary는 deck README에 정확히 남긴다.

---

## P0-02 · Unit 9의 “trace/metric identity로 같은 logical execution 연결”은 현재 curriculum/material로 증명할 수 없다

### Evidence

`09-diagnosis/README.md` 학습 목표에는 다음 취지의 항목이 있다.

> trace/metric identity를 이용해 같은 logical execution을 여러 surface에서 연결한다.

하지만 Unit 8 metrics 예제는 active span 없이 metric만 기록한다. trace ID/span ID와 연결되는 exemplar를 생성하거나
관찰하지 않는다. 일반 metric time-series identity는 개별 request execution의 identity가 아니다.

OpenTelemetry Metrics SDK에서 개별 metric measurement와 trace/span context를 직접 연결하는 대표 mechanism은 **Exemplar**다.
Exemplar는 aggregated metric 안의 특정 measurement에 trace ID/span ID를 보존할 수 있다.

현재 accepted deck outcomes에는 exemplar 학습이 없다.

### Impact

현재 문구는 learner가 `trace_id`처럼 metric에도 개별 logical execution을 식별하는 일반적인 identity가 있다고 오해하게 만들
수 있다. 또한 downstream authoring이 curriculum baseline을 조용히 확장한 상태다.

### Required action

가장 작은 수정은 **goal을 좁히는 것**이다.

권장:

- Resource/time window/attributes를 이용한 signal-level correlation과,
- trace/span ID를 통한 execution correlation을 구분한다.
- exemplar를 새 core concept로 추가하지 않는다면 “같은 logical execution의 trace/metric identity” 표현은 제거한다.

Exemplar를 추가하고 싶다면 local prose repair가 아니라 curriculum delta로 다뤄야 한다.

Official references:

- <https://opentelemetry.io/docs/specs/otel/metrics/sdk/#exemplar>
- <https://opentelemetry.io/docs/specs/otel/metrics/data-model/#exemplars>

---

# P1 · Ready 전에 수정 권장

## P1-01 · Unit 3의 failure example은 current error guidance와 Python 1.45 default behavior를 완전히 설명하지 않는다

두 문제가 한 예제에 겹쳐 있다.

### A. status description

`span_failure.py`에서 `PaymentDeclined("issuer declined payment")`로 끝나는 `charge_payment` span은 status description을
`"payment declined"`로 수동 설정한다.

현재 Recording Errors guidance는 operation이 exception으로 실패할 때 status description에 exception message를 쓰는 방향을
권장한다. 현재 예제는 바로 그 guidance를 가르치는 장이므로 `str(exc)`와 맞추는 편이 더 정확하다.

### B. learner가 실제로 보는 exception event가 설명에서 빠졌다

OpenTelemetry Python 1.45.0의 `start_as_current_span()`은 기본적으로:

- `record_exception=True`
- `set_status_on_exception=True`

이고, span context manager 밖으로 exception이 빠져나오면 exception event를 기록한다.

따라서 현재 `charge_payment`의 ConsoleSpanExporter JSON에는 learner가 별도로 호출하지 않은 exception event가 나타날 수 있다.
본문은 `record_exception()`을 설명하지만 **현재 예제가 이미 implicit하게 exception event를 생성한다는 사실**을 연결하지 않는다.

이 gap은 learner가 “코드에는 `record_exception()`이 없는데 왜 event가 생겼지?”라고 보는 지점이다.

### Required action

둘 중 하나를 의도적으로 선택한다.

1. 현재 Python 1.45 default를 학습 evidence로 사용하고 `events`를 관찰하게 한 뒤 semantic-convention transition과 구분한다.
2. 이번 unit의 목표를 status/`error.type`에 좁히고 싶다면 `record_exception=False` 등으로 noise를 의도적으로 제거한 이유를 설명한다.

첫 번째가 현재 material의 “실제 SDK behavior를 관찰한다”는 방향과 더 잘 맞는다.

Official references:

- <https://opentelemetry.io/docs/specs/semconv/general/recording-errors/>
- <https://github.com/open-telemetry/opentelemetry-python/blob/v1.45.0/opentelemetry-api/src/opentelemetry/trace/__init__.py>
- <https://opentelemetry.io/docs/specs/semconv/exceptions/>

---

## P1-02 · Resource를 “telemetry를 발생시키는 주체”로 정의하면 current spec의 observed-entity model을 놓친다

### Evidence

Unit 4에는 Resource를 “telemetry를 발생시키는 entity”로 설명하는 문장이 있고 deck Goal도 “telemetry의 발생 주체”라는
표현을 사용한다.

현재 OpenTelemetry Resource specification은 Resource를 **telemetry가 생산되는 observed entity**로 정의한다. 기술적으로
telemetry를 emit하는 agent와 Resource가 설명하는 workload가 다를 수 있다. eBPF/agent-based instrumentation이 대표적이다.

Instrumentation Scope와 Resource를 구분하는 장에서 이 차이는 작은 용어 문제가 아니라 mental model의 핵심이다.

### Required action

Resource를 다음에 가깝게 통일한다.

> Resource는 telemetry가 설명하는 observed entity/workload를 나타낸다.

그 뒤 일반적인 in-process SDK에서는 application/service가 emitter이자 observed entity인 경우가 많다고 설명하면 충분하다.

Official reference:

- <https://opentelemetry.io/docs/specs/otel/resource/>

---

## P1-03 · Unit 5가 “mixed instrumentation”을 outcome으로 말하지만 learner-visible evidence는 제공하지 않는다

### Evidence

Unit 5는 다음을 가르치려 한다.

- manual instrumentation
- instrumentation library
- zero-code
- 같은 application에 여러 방식이 함께 존재할 수 있음

하지만 runnable path는 서로 다른 두 script를 각각 실행한다.

- `flask_manual.py`: business span만 직접 생성
- `flask_zero_code.py`: source OTel code 없이 framework instrumentation

둘을 **같은 trace 안에서 framework span + business span**으로 연결해 보는 실습은 없다.

### Impact

가장 중요한 synthesis인 “auto/library는 edge/framework를 보고 manual은 business 의미를 보강한다”가 prose comparison에
머문다. Unit 4에서 배운 Instrumentation Scope가 실제 mixed trace에서 어떻게 도움 되는지도 관찰하지 않는다.

### Required action

작은 mixed example을 하나 추가하거나 기존 예제를 재구성해 다음 evidence를 직접 보게 한다.

```text
framework/server span
└─ manual business span
```

그리고 각각의 instrumentation scope를 비교한다.

이렇게 하면 Unit 4 → Unit 5 dependency가 실제 evidence로 연결된다.

---

## P1-04 · Unit 6 runtime test는 핵심 parent 관계를 검증하지 않고 readiness signal도 race가 있다

### Evidence

Unit 6 본문은 정상 propagation의 핵심 불변 조건을 다음으로 둔다.

```text
A trace_id == B trace_id
B parent_id == A span_id
```

그러나 `test_textbook_examples.py`는 현재:

- A/B trace ID equality
- `traceparent` 형식
- drop-context에서 trace ID inequality

만 검사한다. **B `parent_id == A span_id`는 검사하지 않는다.** `traceparent` 내부 parent field와 A span ID의 equality도
검사하지 않는다.

또 `service_b.py`는 실제 `HTTPServer(...)` bind 전에 `listening` 문구를 출력한다. Test는 그 문구를 readiness signal로
사용한 즉시 client를 실행한다. 따라서 아주 짧지만 bind 이전 race가 존재한다.

### Required action

- server ConsoleSpanExporter JSON에서 `parent_id`를 읽어 A span ID와 비교한다.
- `traceparent`의 trace ID/parent span ID도 A의 값과 직접 비교한다.
- `HTTPServer`를 먼저 생성/bind한 뒤 readiness를 출력한다.
- arbitrary `sleep(0.05)`보다 필요한 exporter evidence가 실제로 나타날 때까지 bounded read를 사용한다.

---

## P1-05 · Unit 7 Docker command가 OTLP receiver를 host의 모든 network interface에 publish한다

### Evidence

현재 명령:

```bash
docker run --rm \
  -p 4318:4318 \
  ...
```

Docker는 host IP를 생략한 published port를 기본적으로 모든 host interface에 bind한다. 학습 material의 application은
`127.0.0.1:4318`만 사용할 필요가 있으므로 외부 interface에 열 이유가 없다.

### Impact

학습자의 laptop/LAN 환경에서 인증 없는 OTLP receiver가 불필요하게 노출될 수 있다. 안전한 disposable local playground라는
repository 방향에도 맞지 않는다.

### Required action

host publish를 loopback으로 제한한다.

```bash
docker run --rm \
  -p 127.0.0.1:4318:4318 \
  ...
```

Collector 내부 receiver는 container 안에서 `0.0.0.0:4318`을 유지해도 된다.

Official Docker reference:

- <https://docs.docker.com/engine/network/port-publishing/>

---

## P1-06 · Unit 7은 application → Collector를 “같은 execution”으로 triangulate할 identity evidence가 약하다

### Evidence

`otlp_trace.py`의 application-side visible output은 현재:

```text
checkout: business work completed
```

뿐이다. trace/span ID를 출력하지 않는다. Collector debug output에서 `checkout` span을 발견하더라도 learner는 이름과 isolated
lab assumption으로 대응시키게 된다.

`adudeck-playground` contract는 같은 logical execution/object를 여러 surface에서 비교할 때 identity evidence를 충분히 제공하는
방향을 선호한다.

### Required action

application에서 현재 span의 trace ID/span ID를 출력하고 Collector debug output의 동일 ID와 비교하게 한다.

```text
application trace_id/span_id
           ==
Collector received trace_id/span_id
```

그러면 “business output 있음”과 “그 telemetry가 Collector까지 갔음”을 더 강하게 연결할 수 있다.

---

## P1-07 · Core textbook의 reproducibility contract가 Unit 5/7에서 약해진다

### Evidence

Unit 1은 비교 가능한 학습 결과를 위해 deck-local `uv.lock`과 `uv run --locked`를 사용한다.

반면 Unit 5와 Unit 7은 `uv --with`로 일부 top-level package만 exact pin하고 나머지 dependency를 ephemeral resolve한다.
Deck README도 이 환경이 lockfile과 같은 validation claim을 갖지 않는다고 명시한다.

이 honesty는 좋지만, **두 unit 모두 optional side quest가 아니라 core path**다.

### Impact

시간이 지나면 direct version은 같아도 transitive dependency resolution이 달라질 수 있다. 재현성과 future maintenance 비용이
커진다.

### Required action

가능하면 현재 deck lock의 dependency group/optional group으로 Unit 5와 Unit 7 runtime을 함께 소유한다. 구조가 불필요하게
복잡해진다면 별도 minimal subproject lock도 가능하지만, “core path인데 unlocked” 상태를 장기 owner로 만들지는 않는 편이
좋다.

---

## P1-08 · Unit 7/9의 fault injection은 source mutation 후 baseline 복원 경계가 약하다

### Evidence

Unit 7은 learner에게 `otlp_trace.py`의 port를 4319로 직접 바꾸게 한다. 그 뒤 원래 상태로 복원하라는 명시적인 reset step이
없다. Unit 9는 다시 Unit 7 baseline을 재사용한다.

Unit 3/5에도 source modification exercise가 있지만 Unit 7은 특히 후속 diagnosis에 직접 영향을 준다.

### Impact

이전 실습에서 남은 잘못된 endpoint가 Unit 9의 fault injection과 섞이면 learner는 의도하지 않은 stale state를 diagnosis하게
된다. controlled failure의 전제인 “한 조건만 바꾼다”가 깨진다.

### Required action

가장 좋은 방법은 source edit 대신 runtime parameter를 두는 것이다.

예:

```bash
... otlp_trace.py --endpoint http://127.0.0.1:4319/v1/traces
```

또는 disposable copy를 사용하고 각 experiment 끝에 explicit reset/verification step을 둔다.

---

# P2 · 품질/유지보수 개선

## P2-01 · Docker와 `curl` 같은 tool prerequisite가 학습 경로에서 늦게 암묵적으로 등장한다

Root prerequisites는 Python/terminal/process/HTTP knowledge를 설명하지만 Unit 5는 `curl`, Unit 7은 Docker runtime을 요구한다.
특히 Docker는 단순 개념 prerequisite가 아니라 실습 수행에 필요한 external tool이다.

권장:

- Unit-local prerequisites에 Docker 설치/실행 가능 여부를 명시한다.
- `curl`은 prerequisite로 선언하거나 Python stdlib request command로 대체해 외부 도구 수를 줄인다.
- Docker를 사용할 수 없는 learner용 “이 unit은 여기까지 읽고 runtime evidence는 skip” boundary를 명확히 한다.

---

## P2-02 · Semantic Conventions outcome이 competence map의 명시적 row에서 빠져 있다

Deck Goal에는 Semantic Conventions 역할을 설명하는 outcome이 추가됐다. Textbook index 본문은 Unit 3/5/8에 분산한다고
설명하지만 competence map 표에는 이 substantial outcome이 독립적으로 보이지 않는다.

표의 목적이 outcome → develop/assess traceability라면 다음 정도로 한 줄을 추가하는 편이 명확하다.

```text
Semantic Conventions의 interoperability 역할 | 3, 5, 8 | 8, 9
```

---

## P2-03 · Unit 9에서 sampling을 diagnosis 원인으로 처음 꺼내지만 최소 mental model이 없다

Sampling은 valid diagnosis consideration이지만 앞 unit에서 설명하지 않는다. Advanced/tail sampling은 명시적으로 out of
scope이므로 별도 장을 만들 필요는 없다.

권장: Unit 9에서 “sampling은 일부 trace를 의도적으로 record/export 대상에서 제외할 수 있다” 정도의 최소 정의를 붙여
새 jargon이 갑자기 나타나는 느낌을 없앤다.

---

## P2-04 · repository test task 설명이 현재 coverage보다 오래된 상태다

`mise.toml`의 `test:opentelemetry-deck` description과 `scripts/test.sh`의 출력은 여전히 “first trace/current-context” 중심으로
표현한다. 실제 suite는 Unit 3, 4, 6, 8까지 검증한다.

동작 오류는 아니지만 CI log를 읽는 maintainer에게 현재 validation surface를 축소해 보이게 한다.

---

## P2-05 · OpenTelemetry Python contrib `0.66b0`이 current이지만 pre-release라는 boundary를 learner-facing text에 명확히 둘 가치가 있다

2026-10-02 기준:

- OpenTelemetry Python API/SDK `1.45.0`은 current stable release다.
- Python contrib / Flask instrumentation `0.66b0`은 current release이지만 PyPI에서 pre-release로 표시된다.
- Collector `0.162.0`은 current Collector release다.

따라서 version 선택 자체는 stale하지 않다. 다만 stable API/SDK와 beta-series instrumentation의 maturity를 learner가 같은
것으로 읽지 않도록 Unit 5 또는 version baseline에 한 문장 남기는 편이 정확하다.

References:

- <https://pypi.org/project/opentelemetry-api/>
- <https://pypi.org/project/opentelemetry-instrumentation-flask/0.66b0/>
- <https://github.com/open-telemetry/opentelemetry-collector/releases>

---

# Repository / PR integration finding

아래 항목은 textbook prose 자체의 품질과 별개지만 PR Ready 판단에는 중요하다.

## R-01 · OpenTelemetry deck project가 repository `setup` / `update` lifecycle에 아직 연결되지 않았다

Current repository scripts는:

- root project
- `tools/dataset_generator`
- `decks/ai-openai_sdk`

를 explicit sync/update하지만 `decks/systems-opentelemetry`는 누락한다.

반면 tests는 OpenTelemetry deck을 repository-managed suite에 포함한다.

즉:

```text
repository test lifecycle     ✅
repository setup lifecycle    ❌
repository update lifecycle   ❌
```

이 gap은 이전 `pr-33-finalization-research.md`에서도 P0로 발견됐지만 아직 남아 있다.

권장:

- setup: `uv sync --project decks/systems-opentelemetry --locked`
- update: 해당 project `uv lock --upgrade` + locked sync

---

## R-02 · ELI5 Agent Asset dependency는 여전히 OpenTelemetry PR과 원자적으로 묶여 있다

PR changed files에는 textbook뿐 아니라 repository-wide `dreambigou/eli5` Rulesync dependency/lock/route 변경이 남아 있다.
이 변경은 textbook을 작성할 때 사용한 방법과 repository dependency lifecycle을 결합한다.

이전 finalization report의 판단과 동일하게, repository가 ELI5를 지속적으로 소유할 이유가 별도로 있다면 Agent Asset PR로
분리하는 편이 rollback/review boundary가 더 명확하다.

사용자가 이번 PR에 함께 두기로 명시적으로 결정한다면 blocker까지는 아니지만, **결합 근거 없이 우연히 남아 있는 상태**는
정리하는 것이 좋다.

---

# 잘된 부분 · 유지해야 할 것

엄격 리뷰에서도 아래는 오히려 보호해야 한다.

## 1. Mechanism-first progression

```text
single-process context
→ error semantics
→ Resource/scope/runtime ownership
→ instrumentation ownership
→ process propagation
→ transport/Collector
→ metrics
→ diagnosis
```

Dashboard-first tutorial보다 state/data flow 이해에 훨씬 적합하다.

## 2. Unit 2 calibration pattern

`predict → run → observe → interpret → vary → transfer`가 실제 textbook pattern으로 기능한다.
후속 unit이 이를 기계적으로 복제하지 않고 scaffolding을 줄인 점도 좋다.

## 3. Unit 3의 handled error vs final failure framing

세부 gap은 있지만 **“exception 발생 = operation failure”가 아니다**라는 중심 모델은 current Recording Errors guidance와 잘
맞는다. 이 framing은 유지해야 한다.

## 4. Unit 4의 Resource vs Instrumentation Scope 분리

Resource wording만 보정하면, service identity와 telemetry producer software scope를 별도 축으로 보는 장의 위치와 실습은
좋다.

## 5. Unit 6의 deliberate propagation break

HTTP business request는 성공하지만 correlation만 끊기는 실험은 좋은 causal contrast다. 첫 CI에서 실제 header casing bug를
잡은 것도 hands-on evidence의 가치가 컸다.

## 6. Unit 8의 instrument-by-question framing

Instrument 이름부터 외우지 않고 measurement semantics에서 Counter/UpDownCounter/Histogram을 선택하게 한 것은 좋다.
High-cardinality ID를 metric에 넣지 않는 transfer question도 실전적인 reasoning task다.

## 7. Unit 9의 boundary diagnosis framing

“마지막 확인 evidence와 첫 사라진 evidence 사이를 좁힌다”는 mental model은 이 덱 전체를 묶는 강한 synthesis다.
P0-02의 cross-signal identity 문구를 고쳐도 이 diagnosis structure는 그대로 유지할 수 있다.

---

# Ready 전 권장 순서

수정 비용과 risk reduction을 기준으로 다음 순서를 권장한다.

1. **P0-02** Unit 9 cross-signal correlation 문구를 좁힌다.
2. **P1-02** Resource 정의를 observed entity 기준으로 통일한다.
3. **P1-01** Unit 3 status description과 implicit exception-event 설명을 맞춘다.
4. **P1-05** Collector Docker publish를 loopback으로 제한한다.
5. **P1-04** Unit 6 parent identity test + deterministic readiness를 강화한다.
6. **P1-08** Unit 7 fault injection을 source edit 없이 수행하도록 만든다.
7. **P1-03/P1-06** Unit 5 mixed evidence와 Unit 7 application↔Collector identity evidence를 보강한다.
8. Unit 5/7 dependency ownership과 hidden prerequisites를 정리한다.
9. **P0-01** clean runtime에서 Unit 5와 Unit 7을 end-to-end 검증한다.
10. repository `setup.sh` / `update.sh` lifecycle을 연결한다.
11. P2와 PR boundary를 정리한다.
12. latest head에서 repository CI와 deck-specific runtime evidence를 다시 확인한다.

---

# 최종 판정

현재 상태:

```text
Curriculum structure       PASS
Mechanism-first pedagogy   PASS
Core prose depth           PASS with findings
Core locked examples       PASS (Unit 2/3/4/6/8)
Unit 5 runtime             NOT VALIDATED
Unit 7 runtime             NOT VALIDATED
Cross-slice correctness    FAIL until P0/P1 factual gaps are repaired
Playground safety          FAIL until Docker host binding is narrowed
Repository integration     INCOMPLETE
PR Ready                   NO
Deck completion            NO
```

수정 후 목표는 “파일 0–9가 존재한다”가 아니라 다음 상태여야 한다.

> **각 substantial outcome이 정확한 explanation, observable evidence, reasoning practice, assessment path와 검증된 runtime
> boundary를 가지고 있으며, learner가 실습 상태를 오염시키지 않고 처음부터 끝까지 재현할 수 있다.**

그 상태가 되면 이 textbook은 OpenTelemetry beginner material로 상당히 강한 수준까지 올라갈 수 있다.
