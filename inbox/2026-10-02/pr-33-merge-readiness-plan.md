# PR #33 · Merge readiness 계획

작성일: 2026-10-02

대상: `decks/systems-opentelemetry/`과 PR #33의 직접 integration surface

## 목표

PR #33을 단순히 CI가 통과하는 상태가 아니라, 현재 deck curriculum이 요구하는 핵심 hands-on outcome을 실제 evidence로 검증하고 textbook factual/learning gap과 repository integration gap을 닫은 **merge-ready 상태**로 만든다.

Merge-ready 판정은 다음을 모두 만족해야 한다.

- 엄격 self-review의 P0 blocker 0건
- Ready 전에 고쳐야 할 P1 material gap 중 현재 scope에서 유효한 항목 해소
- Unit 5 instrumentation path와 Unit 7 OTLP/Collector path의 end-to-end runtime evidence 확보
- Unit 2–9의 핵심 learning claim과 runnable artifact/test가 서로 모순되지 않음
- repository setup/update/test lifecycle이 OpenTelemetry deck을 일관되게 소유함
- latest PR head의 `ci/validated`가 success
- final integration self-review에서 새 merge blocker가 발견되지 않음

Canonical curriculum/build state는 `decks/systems-opentelemetry/README.md`와 `textbook/README.md`가 소유한다. 이 문서는 작업 계획과 완료 evidence만 기록한다.

## 원칙

1. **P0 → P1 → integration → final review 순서**로 진행한다.
2. CI green을 runtime evidence로 과장하지 않는다. Unit 5/7은 실제 learner path를 실행한다.
3. version-sensitive behavior는 OpenTelemetry/Docker primary source와 actual runtime evidence를 함께 사용한다.
4. source-edit fault injection보다 runtime parameter/disposable state를 선호한다.
5. learner가 같은 logical execution을 여러 surface에서 비교할 때 identifier evidence를 제공한다.
6. curriculum을 넓히지 않는다. Exemplar, logs, advanced sampling, backend UI는 현재 core scope에 추가하지 않는다.
7. 변경은 현재 PR 안에서 필요한 최소 coherent repair로 제한한다.

## Phase A · Factual / curriculum repair

### A1. Unit 9 trace/metric correlation claim 좁히기

- [ ] metric series/resource/time-window correlation과 trace/span execution identity를 구분한다.
- [ ] exemplar를 가르치지 않는 현재 curriculum에서는 “trace/metric identity로 같은 logical execution 연결” 표현을 제거한다.
- [ ] competence/assessment 표현도 같은 boundary로 맞춘다.

Acceptance:

- learner가 일반 metric에 trace ID와 같은 per-execution identity가 있다고 오해할 문장이 없다.
- exemplar를 새 curriculum concept로 암묵적으로 도입하지 않는다.

### A2. Unit 3 failure semantics 정밀화

- [ ] `charge_payment` failure의 status description을 실제 exception message와 정렬한다.
- [ ] Python 1.45 `start_as_current_span()`의 기본 `record_exception=True`, `set_status_on_exception=True` behavior를 learner-visible evidence로 설명한다.
- [ ] exception event와 operation failure semantics/status를 구분한다.
- [ ] test가 expected exception event/status relationship을 필요 범위에서 검증한다.

Acceptance:

- 코드/본문/test가 같은 error model을 설명한다.
- current Python runtime behavior와 Semantic Conventions transition을 혼동하지 않는다.

### A3. Resource mental model 교정

- [ ] Resource 정의를 “telemetry가 설명하는 observed entity/workload” 중심으로 통일한다.
- [ ] emitter와 observed entity가 항상 같지는 않다는 boundary를 최소한으로 설명한다.
- [ ] deck Goal / Unit 4 용어를 일치시킨다.

## Phase B · Hands-on quality / runtime evidence

### B1. Unit 5 mixed instrumentation + end-to-end validation

- [ ] manual business span과 Flask instrumentation server span을 같은 trace 안에서 관찰할 수 있는 runnable path를 만든다.
- [ ] framework span과 business span의 parent/trace relationship 및 Instrumentation Scope 차이를 learner-visible evidence로 노출한다.
- [ ] plain Flask baseline과 zero-code/mixed instrumentation path를 실제 HTTP request까지 실행한다.
- [ ] source 수정 없이 repeatable하게 start/request/observe/cleanup할 수 있게 한다.
- [ ] current contrib `0.66b0`의 beta-series maturity boundary를 설명한다.

Acceptance:

```text
framework/server span
└─ manual business span
```

관계와 서로 다른 instrumentation scope를 실제 output에서 확인할 수 있다.

### B2. Unit 6 propagation validation 강화

- [ ] Service B server socket bind 이후 readiness를 출력한다.
- [ ] normal case에서 `traceparent.trace_id == A.trace_id`를 검증한다.
- [ ] `traceparent.parent_span_id == A.span_id`를 검증한다.
- [ ] B exported span의 `parent_id == A.span_id`를 검증한다.
- [ ] arbitrary sleep 의존성을 줄이고 bounded evidence read를 사용한다.

### B3. Unit 7 safe/repeatable OTLP → Collector validation

- [ ] Docker publish를 `127.0.0.1:4318:4318`로 제한한다.
- [ ] application에서 trace ID/span ID를 출력한다.
- [ ] endpoint를 CLI parameter로 받아 source mutation 없이 happy/failure path를 실행한다.
- [ ] pinned Collector `0.162.0` + OTLP HTTP exporter `1.45.0`로 application → OTLP → receiver → batch → debug exporter를 실제 검증한다.
- [ ] wrong endpoint 등 최소 한 failure variant도 실행한다.
- [ ] cleanup/reset path를 명시하고 검증한다.

Acceptance:

- application-side trace/span identity가 Collector-side received span identity와 일치한다.
- wrong endpoint에서는 business work와 telemetry delivery failure를 분리해서 관찰할 수 있다.
- 실습이 host LAN에 receiver를 불필요하게 노출하지 않는다.

### B4. Reproducibility ownership 결정

- [ ] Unit 5/7 dependency를 core lock/group/subproject lock 중 가장 작은 적절한 owner로 수렴한다.
- [ ] 장기적으로 “core path인데 ephemeral transitive resolve” 상태를 남기지 않는다.
- [ ] 선택한 ownership을 README와 validation command에 반영한다.

## Phase C · Repository integration

### C1. setup/update lifecycle

- [ ] `scripts/setup.sh`가 `decks/systems-opentelemetry`를 `uv sync --project ... --locked`로 준비한다.
- [ ] `scripts/update.sh`가 해당 deck lock을 upgrade/sync한다.
- [ ] shell syntax와 repository test를 재검증한다.

### C2. test/log wording

- [ ] `mise.toml`과 `scripts/test.sh`의 OpenTelemetry task description을 실제 coverage에 맞춘다.

### C3. Agent Asset boundary

- [ ] ELI5 Rulesync 변경이 이 PR과 원자적으로 묶여야 하는 근거가 있는지 재판정한다.
- [ ] 독립적이면 PR #33에서 제거하고 별도 Agent Asset change로 넘긴다.
- [ ] 함께 둘 경우 PR body에 coupling rationale를 명시한다.

## Phase D · Learning UX polish

- [ ] Unit-local prerequisite로 Docker/curl 또는 대체 command 요구사항을 명시한다.
- [ ] Semantic Conventions outcome을 textbook competence map에 명시한다.
- [ ] Unit 9 sampling에 최소 mental model을 제공하되 advanced sampling으로 scope를 넓히지 않는다.
- [ ] Unit 7/9 failure experiment가 baseline state를 오염시키지 않는지 확인한다.

## Phase E · Final gate

1. 최신 head에서 repository CI를 확인한다.
2. Unit 5/7 runtime evidence가 실제 test/acceptance surface에 연결됐는지 확인한다.
3. README ↔ textbook ↔ runnable artifacts ↔ tests ↔ scripts ↔ PR body consistency를 다시 검토한다.
4. strict self-review의 각 P0/P1 finding을 `resolved / intentionally deferred / no longer applicable`로 disposition한다.
5. unresolved merge blocker가 0이면 Draft → Ready 후보로 판정한다.

## 완료 보고 형식

최종적으로 다음을 남긴다.

```text
Merge readiness
- P0 blockers: 0
- unresolved P1 material gaps: 0 (또는 명시적 비-blocking defer)
- Unit 5 runtime: PASS
- Unit 7 runtime: PASS
- repository CI: PASS
- integration review: PASS
- residual non-blocking follow-ups: ...
```

그 전에는 PR이 mergeable하고 CI가 green이어도 merge-ready라고 선언하지 않는다.
