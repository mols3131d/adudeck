# PR #33 · Merge readiness 결과

작성일: 2026-10-02  
최종 integration review 기준 revision: `99d8918da9b3b3f15d2106d3f64f3ad489d3fb3a`

대상: PR #33 `feat/opentelemetry-deck-foundation` → `main`

## 결론

**Merge blocker 0건. PR #33은 Ready 후보 수준에 도달했다.**

엄격 self-review에서 발견한 P0 blocker와 merge 전 material P1 gap을 재검토했고, 현재 learning contract에 필요한 runtime
boundary는 실제 end-to-end evidence로 닫았다. 기준 revision의 `ci/validated`는 success이며, 이 status는 locked core test뿐
아니라 Flask zero-code/mixed instrumentation과 실제 OpenTelemetry Collector container acceptance까지 포함한다.

이 결과 보고서 자체가 새 commit을 만들므로, **보고서가 포함된 최신 head에서도 같은 CI gate가 다시 success한 뒤** Draft를
해제하는 것을 최종 gate로 둔다.

## Strict self-review disposition

| Finding | Disposition | Evidence / 판단 |
| --- | --- | --- |
| P0 · Unit 5 end-to-end runtime 없음 | **Resolved** | Flask `3.1.3` + contrib/distro `0.66b0`, 실제 HTTP request로 plain vs mixed instrumentation 실행. framework span과 manual business span의 same trace, parent/child, distinct scope 검증. |
| P0 · Unit 7 OTLP → Collector runtime 없음 | **Resolved** | OTLP HTTP exporter `1.45.0` → Collector `0.162.0` receiver → batch → debug exporter를 실제 container로 실행하고 app/Collector trace+span ID 일치 검증. |
| P0/P1 · Unit 9 trace/metric execution identity 과장 | **Resolved** | trace execution identity와 metric Resource/attribute/time-window correlation을 분리. Exemplar는 명시적으로 out of core scope. |
| P1 · Unit 3 error semantics/runtime mismatch | **Resolved** | `record_exception=True` runtime evidence와 explicit operation status를 분리. `set_status_on_exception=False`의 학습 목적을 설명하고 test가 status description + exception event를 검증. |
| P1 · Resource mental model 부정확 | **Resolved** | Resource를 observed entity/workload 중심으로 교정하고 emitter와 observed entity가 다를 수 있음을 설명. |
| P1 · Unit 5 manual/zero-code가 실제로 만나지 않음 | **Resolved** | `flask_mixed.py` 추가. zero-code Flask server span 아래 manual business span을 실제 evidence로 확인. |
| P1 · Unit 6 propagation test가 parent identity를 검증하지 않음 | **Resolved** | `traceparent.trace_id`, `traceparent.parent_span_id`, exported B `parent_id`를 A span ID와 대조. `--once` server mode로 deterministic completion. |
| P1 · Unit 7 Docker port가 모든 interface에 publish | **Resolved** | learner command와 acceptance 모두 host publish를 `127.0.0.1`로 제한. |
| P1 · Unit 7 app ↔ Collector identity triangulation 없음 | **Resolved** | application이 trace/span ID를 출력하고 acceptance가 Collector debug output의 동일 ID를 검증. |
| P1 · Unit 5/7 helper dependency transitive lock 없음 | **Intentional non-blocking boundary** | exact direct version을 고정하고 매 CI에서 E2E resolve/run. Core `uv.lock`과 같은 transitive reproducibility는 주장하지 않는다고 README에 명시. 현재 learning outcome에는 실제 compatibility evidence가 더 직접적인 acceptance다. |
| P1 · Unit 7/9 fault injection이 source를 오염 | **Resolved** | wrong endpoint는 CLI argument, Collector config failure는 disposable copy를 사용하도록 변경. |
| P1 · repository setup/update lifecycle 누락 | **Resolved** | `scripts/setup.sh`와 `scripts/update.sh`가 `decks/systems-opentelemetry` lock/sync lifecycle을 관리. |
| P1 · unrelated ELI5 Agent Asset가 PR에 결합 | **Resolved** | Rulesync/ELI5 변경을 PR diff에서 제거. 현재 changed-file set에 해당 Agent Asset 변경 없음. |
| P2 · Docker/curl hidden prerequisite | **Resolved** | Unit 5/7에서 local prerequisite와 대체 request 방법 / Docker validation boundary 명시. |
| P2 · Semantic Conventions competence mapping 누락 | **Resolved** | textbook competence map에 development/assessment responsibility 추가. |
| P2 · sampling이 설명 없이 등장 | **Resolved** | Unit 9에 “일부 trace candidate를 의도적으로 선택할 수 있다” 수준의 최소 mental model 추가; advanced sampling은 여전히 out of scope. |
| P2 · test task/log wording stale | **Resolved** | core와 external acceptance task를 분리하고 실제 coverage로 description/log 수정. |
| P2 · contrib `0.66b0` maturity boundary | **Resolved** | current beta-series라는 사실을 learner-facing README에 명시. |

## Runtime validation

### Locked core

Repository-managed locked environment에서 다음 learner-visible relation을 검증한다.

- Unit 2: span tree/current-context variation
- Unit 3: recovered error vs final failure, status, `error.type`, exception event
- Unit 4: same Resource + distinct Instrumentation Scope
- Unit 6: actual two-process propagation, W3C `traceparent`, exported parent relation, deliberate context break
- Unit 8: Counter total, UpDownCounter return-to-zero, Histogram observation count

### External acceptance

CI의 별도 acceptance는 다음 boundary를 실제로 실행한다.

```text
Flask request
→ zero-code Flask instrumentation
→ current context
→ manual business span
```

그리고:

```text
Python SDK
→ OTLP/HTTP exporter
→ localhost transport
→ Collector OTLP receiver
→ batch processor
→ debug exporter
```

Unit 7에서는 application-side trace/span ID와 Collector-side ID를 직접 비교한다. Wrong endpoint case에서는 business work가
완료되더라도 해당 trace가 Collector에 도착하지 않는 것을 확인한다.

기준 revision `99d8918da9b3b3f15d2106d3f64f3ad489d3fb3a`의 `ci/validated`: **success**.

## Integration review

다음 cross-artifact relation을 다시 확인했다.

```text
README learning outcomes
↔ textbook competence map
↔ chapter explanation/practice
↔ runnable artifact
↔ automated evidence
↔ CI merge gate
```

현재 확인 결과:

- Unit 0–9 sequence는 dependency order를 유지한다.
- Unit 3의 error model은 code / prose / test가 같은 boundary를 설명한다.
- Unit 4 Resource/Scope model이 Unit 5 mixed instrumentation에서 재사용된다.
- Unit 2 current context → Unit 5 framework/manual nesting → Unit 6 process propagation이 점진적으로 확장된다.
- Unit 7 transport evidence가 Unit 9 diagnosis의 concrete boundary가 된다.
- Unit 8 metric aggregation과 Unit 9 cross-signal correlation이 per-execution identity로 잘못 합쳐지지 않는다.
- Repository setup/update/test/CI ownership이 새 deck과 연결되어 있다.
- unresolved PR review thread는 없다.

## Residual non-blocking boundaries

다음은 남아 있지만 현재 PR merge blocker로 보지 않는다.

1. **Unit 5/7 helper dependency transitive lock**  
   direct dependency version은 exact pin이며 실제 compatibility를 CI E2E에서 검증한다. Core lock과 같은 재현성은 주장하지
   않는다. 미래에 offline repeatability나 long-term transitive freeze가 필요해지면 별도 lock/group으로 승격할 수 있다.

2. **Python support matrix**  
   project contract는 Python 3.10+지만 현재 CI runtime evidence는 Python 3.14.6이다. README가 이 차이를 명시한다.

3. **External backend / UI**  
   vendor backend storage/query/UI는 명시적 out-of-core boundary다. Unit 7은 Collector debug exporter까지를 검증한다.

4. **Learner study evaluation**  
   automated evidence는 mechanism correctness와 runnable path를 검증하지만 실제 learner cohort의 이해도 평가는 수행하지 않았다.
   이는 현재 repository merge gate가 아니다.

## Historical inbox note

`inbox/2026-10-02/pr-33-finalization-research.md`의 “Unit 0–2 foundation에서 PR을 닫는다”는 당시 권고는 이후 사용자가
**Unit 0–9 textbook 전체 구현과 merge-ready 수준까지 계속 진행하라고 명시적으로 요청**하면서 superseded되었다.

현재 learning/build state의 authority는 `decks/systems-opentelemetry/README.md`, `textbook/README.md`, runnable artifacts/tests와
live PR state다. 과거 inbox 보고서를 현재 completion boundary로 사용하지 않는다.

## Final gate

이 보고서 commit 이후 최신 head에서 다음이 모두 만족되면 Draft 해제를 권장한다.

- [ ] `ci/validated = success`
- [x] P0 blocker = 0
- [x] unresolved material P1 merge blocker = 0
- [x] Unit 5 E2E = PASS
- [x] Unit 7 E2E = PASS
- [x] repository integration review = PASS
- [x] unresolved PR review thread = 0

최신-head CI가 success하면 최종 verdict는 **MERGE-READY / Ready for review**다.
