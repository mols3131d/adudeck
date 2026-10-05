# PR #33 · foundation 종료선 재조사 보고서

작성일: 2026-10-02

이 문서는 PR #33을 OpenTelemetry 전체 덱 완성 PR로 계속 확장할지, 현재 calibration slice를 foundation으로 닫을지
판단하기 위한 임시 조사 보고서다. Canonical curriculum과 진행 상태는 `decks/systems-opentelemetry/README.md`가
소유한다. 기존 `inbox/2026-10-01/pr-33-remaining-work.md`의 상세 Unit 3–9 계획은 후속 구현 참고로 유지하되,
**PR boundary에 대해서는 이 보고서의 결론을 우선 권고**한다.

## 결론

PR #33은 **Unit 0–2를 포함한 검증된 foundation + calibration slice PR로 마무리하는 것이 가장 적절하다.**
Unit 3–9을 같은 PR에서 계속 구현하는 것은 권장하지 않는다.

현재 PR은 이미 다음을 증명했다.

- beginner learning contract와 Unit 0–9의 dependency order
- Intro → Setup → First Trace의 진입 경로
- single-process current context와 parent/child span 관계
- prediction → execution → evidence → interpretation → controlled variation → transfer assessment 패턴
- learner-visible console JSON을 검사하는 runtime test
- deck-local dependency lock과 repository test integration

여기서 Unit 3부터는 단순한 같은 패턴의 문서 확장이 아니다. error semantics와 Semantic Conventions, instrumentation
library/zero-code, HTTP propagation, OTLP/Collector, metrics, fault injection처럼
**새로운 runtime boundary와 version-sensitive behavior**가 연속으로 등장한다. Repository의 `adudeck-deck-build`도
calibration slice를 먼저 end-to-end로 검토하고 실제 handoff point를 만든 뒤 다음 increment로 진행하도록 요구한다.

따라서 권장 흐름은 다음과 같다.

```text
PR #33
foundation + Unit 2 calibration slice
        ↓ merge
follow-up PR
Unit 3부터 새 validation mode를 하나씩 확장
```

## 현재 live 상태

조사 시점의 PR #33은 Draft이며 `feat/opentelemetry-deck-foundation` → `main`이다.
현재 head 기준 변경 규모는 14 files, 약 +1,091 lines이며 Unit 0–2가 구현되어 있다.
최근 확인한 `ci/validated` 상태는 success였다. 이 보고서 commit 이후에는 새 head에 대해 다시 검증해야 한다.

현재 덱 README는 “이후 unit을 같은 PR에서 작은 increment로 추가한다”고 적고 있다. foundation PR로 닫는 결정을 채택하면
이 문구는 후속 PR에서 increment를 이어가는 표현으로 바꿔야 한다.

## 왜 지금 PR을 나누는 편이 좋은가

### 1. Repository build contract와 더 잘 맞는다

`adudeck-deck-build`은 새 덱에서 먼저 하나의 calibration slice를 끝까지 구현하고, explanation depth, terminology,
practice, assessment evidence, hands-on pattern을 검토한 뒤 확장하도록 한다. Git-backed work도 한 coherent slice 또는
작은 coupled set을 reviewable change로 유지하는 쪽을 선호한다.

PR #33의 Unit 2는 이미 calibration slice로 기능한다. 더 많은 Unit을 추가해야 calibration 목적이 강화되는 것이 아니라,
오히려 review surface와 실패 원인이 늘어난다.

### 2. Unit 3부터 factual risk가 크게 달라진다

현재 OpenTelemetry error semantic conventions의 recording-errors 문서는 Development 상태다. Operation failure에는 span
status `Error`와 `error.type` 사용을 권고하고, handled/retried error를 최종 operation failure로 기록하지 않는 경계를
둔다. Exception conventions도 span event에서 log record로 이동하는 transition guidance가 존재한다.

즉 Unit 3은 단순히 `record_exception()` 호출법을 추가하는 장이 아니다. “실패란 무엇인가”, span status와 error evidence가
어떻게 다른가, 현재 transition을 beginner에게 어느 깊이까지 보여 줄 것인가를 새로 calibration해야 한다.

### 3. Unit 5부터 instrumentation mode가 바뀐다

공식 Python 문서는 manual instrumentation, instrumentation libraries, zero-code instrumentation을 구분한다. Python
zero-code는 agent + instrumentation libraries를 사용하고 주로 monkey patching으로 library/framework telemetry를 만든다.
반면 application business logic의 의미는 code-based manual instrumentation이 보완한다.

따라서 Unit 5는 Unit 2와 다른 recurring teaching mode다. 현재 foundation PR에 같이 밀어 넣기보다, 처음 등장할 때 별도로
calibrate하는 편이 repository build 원칙과 맞는다.

### 4. Unit 7부터 process/container boundary가 추가된다

공식 Python exporter 문서는 OTLP exporter 검증 경로로 local Collector의 OTLP receiver → debug exporter 구성을 제공한다.
Collector는 component를 선언하는 것과 `service.pipelines`에 실제 연결해 활성화하는 것이 별도다. 공식 troubleshooting도
local debug exporter로 receive/process/export evidence를 확인하도록 한다.

이는 현재 Unit 2의 in-process console exporter와 다른 실행 환경, dependency, Docker/process failure mode를 추가한다.
Foundation PR에 포함할 이유가 약하다.

### 5. 현재 Collector release도 실습 환경 자체가 검증 대상이다

2026-10-02 기준 Collector latest release 계열은 `v0.162.0`이다. Release 직후 contrib multi-arch manifest 관련 이슈도
보고되어 있다. Unit 7에서 Docker image를 선택할 때는 “latest니까 사용”이 아니라 실제 사용하는 distribution/tag가 학습
환경에서 pull/run 가능한지 다시 검증해야 한다.

이런 변화 가능성은 Unit 7을 PR #33과 분리할 추가 근거다.

## PR #33에 더 하면 좋은 것

아래는 **merge 전 권장 작업**이다. Unit 3 구현보다 우선한다.

### P0 · correctness와 boundary 정리

- [ ] **Unit 2의 `service.name` 설명을 교정한다.**
  - 같은 `service.name`은 같은 Resource object나 같은 process의 충분한 증거가 아니다.
  - 현재 예제에서 같은 Resource configuration을 보는 이유는 하나의 `TracerProvider(resource=...)` 설정을 공유하기
    때문이다.
- [ ] **context variation 질문을 같은 실행 안의 관계로 바꾼다.**
  - “이전과 trace_id가 같은가?” 대신 “이번 실행에서 `charge_payment`와 `checkout`이 같은 trace_id를 공유하는가?”를
    묻는다.
- [ ] **transfer problem의 context 전제를 명시한다.**
  - synchronous nested `start_as_current_span()`을 가정하고, “span 종료 직후”가 아니라 `with` block을 빠져나온 뒤
    복원되는 current context를 묻는다.
- [ ] **PR completion claim을 foundation으로 좁힌다.**
  - PR title/body/README의 build progress가 “전체 deck completion”을 암시하지 않도록 한다.
  - README의 “같은 PR에서 Unit 3–9 추가” 문구를 follow-up increment로 바꾼다.

### P0 · curriculum baseline 보강

현재 README에는 Goal, prerequisites, scope, outcomes, Unit sequence가 있지만 outcome coverage를 사람이 추론해야 한다.
최소한의 development/assessment responsibility를 README에 남기는 것을 권장한다.

예시:

| Outcome | Develop | Assess |
| --- | --- | --- |
| span/trace 관계와 current context | Unit 2 | Unit 2 |
| Resource와 API/SDK runtime boundary | Unit 4 | Unit 4 |
| instrumentation mode 비교 | Unit 5 | Unit 5 |
| cross-service propagation | Unit 6 | Unit 6 |
| OTLP/Collector boundary 추적 | Unit 7 | Unit 7 |
| metric instrument 선택 | Unit 8 | Unit 8 |
| telemetry pipeline diagnosis | Unit 9 | Unit 9 |

이 표의 목적은 chapter placeholder를 늘리는 것이 아니라, substantial outcome이 orphan되지 않도록 baseline 책임을
명시하는 것이다.

### P0 · Semantic Conventions delta 결정

**채택을 권장한다.** 다만 별도 Unit을 만들지 않는다.

권장 outcome의 크기:

> Semantic Conventions가 서로 다른 instrumentation에서 공통 telemetry 의미를 맞추는 역할을 설명한다.

개발 책임은 Unit 3의 error/attribute, Unit 5의 library instrumentation, Unit 8의 metric name/unit에 분산할 수 있다.
개별 convention의 안정성을 모두 보장하는 학습 목표로 확대하지 않는다. 공식 문서도 Semantic Conventions 전체와 개별
영역의 stability가 동일하지 않음을 경고한다.

### P0 · repository environment lifecycle 연결

현재 `scripts/setup.sh`와 `scripts/update.sh`는 root project, dataset generator, OpenAI SDK deck을 explicit project로
처리하지만 `decks/systems-opentelemetry`는 누락되어 있다.

- [ ] setup에서 `uv sync --project decks/systems-opentelemetry --locked`
- [ ] update에서 해당 project의 `uv lock --upgrade` + locked sync
- [ ] shell syntax와 deck runtime test를 다시 검증
- [ ] 실제 setup/update workflow를 실행하지 않았다면 syntax check만으로 end-to-end 성공을 주장하지 않기

새 deck이 repository-managed dependency surface를 만들었으므로 이 연결은 foundation PR에 포함하는 편이 응집도가 높다.

### P0 · ELI5 Agent Asset 변경 분리

현재 PR에는 OpenTelemetry deck 외에 external `dreambigou/eli5` Rulesync dependency와 generated projection 변경이 함께
있다. 교육 prose 개선에 사용했다는 이유는 이해되지만, repository-wide Agent Asset dependency의 lifecycle은 deck 내용과
독립적이다.

권장:

1. PR #33에서는 ELI5 external dependency / projection 변경을 제거한다.
2. repository에 지속적으로 필요한 Skill이라면 별도의 Agent Asset PR에서 도입 근거, license, lock, generation
   validation을 독립적으로 검토한다.

분리가 어려우면 최소한 PR body에서 왜 OpenTelemetry foundation과 원자적으로 묶여야 하는지 설명해야 하지만,
현재 evidence로는 별도 PR이 더 단순하다.

### P1 · final validation matrix 정리

Ready 전환 전에는 README와 PR body에 다음 validation boundary가 일치하면 좋다.

| 대상 | PR #33에서 주장할 수준 |
| --- | --- |
| Python runtime | 실제 실행한 3.14.6 |
| declared Python support | package/project contract의 3.10+, 전체 matrix 실행을 의미하지 않음 |
| OTel API/SDK | locked 1.45.0 runtime evidence |
| Unit 2 baseline | three-span relation + attributes + service.name output |
| Unit 2 variation | payment span이 current context 밖에서 새 root trace가 됨 |
| Collector/backend | 미검증 / follow-up |
| learner study evaluation | 미실시 |

CI success와 learner-visible runtime evidence를 같은 것으로 취급하지 않는다.

## PR #33에서 하지 않는 것을 권장하는 작업

아래는 중요하지만 현재 PR을 더 좋게 닫는 데 필요하지 않다.

- Unit 3–9 전체 구현
- Flask/FastAPI 같은 framework 추가
- zero-code instrumentation dependency 추가
- Docker/Collector runtime 추가
- Grafana/Tempo/Mimir backend 추가
- logs pipeline 확대
- advanced/tail sampling
- production Collector deployment
- OpenTelemetry Demo를 직접 실행하는 capstone
- GenAI/LLM semantic conventions

이 항목들은 삭제 대상이 아니라 **follow-up scope**다.

## 후속 PR의 권장 시작점

다음 PR은 Unit 3 하나만 구현·검토하는 것이 가장 안전하다.

### Unit 3 calibration target

```text
successful operation
vs
failed operation
vs
handled/retried error
```

학습자는 먼저 무엇을 operation failure로 볼지 예측하고, 실제 span output에서 다음 evidence를 비교한다.

- span status
- `error.type` 적용 여부
- attributes
- 현재 Python SDK의 exception recording behavior

`record_exception()`을 “OpenTelemetry에서 실패를 기록하는 정답”으로 가르치지 않는다. Current official Semantic
Conventions와 Python SDK 실제 output의 차이를 명시하고, transition 중인 behavior는 versioned note로 둔다.

이 slice가 accepted된 뒤 Unit 4로 간다.

## Source authority 권고

후속 textbook implementation에서 technical contract의 우선순위는 다음이 적절하다.

```text
OpenTelemetry specification / Semantic Conventions
→ current official language + Collector documentation
→ official releases / Demo
→ Linux Foundation / CNCF training
→ vendor tutorials and labs
```

Vendor material은 onboarding UX, analogy, failure scenario, lab flow의 아이디어에 사용하고 API semantics나 current
version의 권위로 사용하지 않는다.

Linux Foundation LFS148은 beginner course에서도 framework overview, instrumentation, manual traces/metrics/logs,
Collector를 hands-on lab으로 분리한다. GrafanaCON 2026 lab은 SDK, instrumentation mode, cross-service, backend까지 한
번에 연결하지만 3시간 lab 목적이므로 adudeck의 mechanism-first core path를 대체하기보다 후속 실습 UX 참고로 보는 편이
좋다.

## PR #33 종료 체크리스트

다음이 모두 끝나면 PR #33은 foundation PR로 Ready 후보가 된다.

- [ ] Unit 2 correctness 3건 해결
- [ ] Semantic Conventions curriculum delta 채택/보류 결정 및 기록
- [ ] outcome → development/assessment coverage 명시
- [ ] setup/update에 OpenTelemetry uv project 연결
- [ ] ELI5 Agent Asset 변경 분리 또는 결합 근거 명시
- [ ] README의 build progress와 PR body를 foundation completion boundary에 맞춤
- [ ] `mise run test:opentelemetry-deck`
- [ ] repository 전체 deterministic validation
- [ ] changed Markdown / shell / lock 관련 validation
- [ ] 새 head의 remote CI 확인

이 단계에서 **Unit 3이 없다는 이유로 PR #33을 미완성으로 보지 않는다.**
PR #33의 completion unit은 전체 OpenTelemetry curriculum이 아니라 foundation + accepted calibration slice다.

## 조사 출처

Repository / PR:

- PR #33: <https://github.com/mols3131d/adudeck/pull/33>
- `docs/VISON.md`
- `docs/decks.md`
- `.rulesync/skills/adudeck-deck-build/SKILL.md`
- `.rulesync/skills/adudeck-deck-curriculum/SKILL.md`
- `.rulesync/skills/adudeck-textbook/SKILL.md`
- `decks/systems-opentelemetry/README.md`
- `inbox/2026-10-01/pr-33-remaining-work.md`

Canonical OpenTelemetry:

- <https://opentelemetry.io/docs/languages/python/>
- <https://opentelemetry.io/docs/languages/python/instrumentation/>
- <https://opentelemetry.io/docs/languages/python/libraries/>
- <https://opentelemetry.io/docs/zero-code/python/>
- <https://opentelemetry.io/docs/specs/otel/semantic-conventions/>
- <https://opentelemetry.io/docs/specs/semconv/general/recording-errors/>
- <https://opentelemetry.io/docs/specs/semconv/exceptions/exceptions-logs/>
- <https://opentelemetry.io/docs/languages/python/exporters/>
- <https://opentelemetry.io/docs/collector/>
- <https://opentelemetry.io/docs/collector/troubleshooting/>
- <https://github.com/open-telemetry/opentelemetry-collector/releases>
- <https://github.com/open-telemetry/opentelemetry-demo/releases>

Comparative learning material:

- Linux Foundation / CNCF LFS148:
  <https://training.linuxfoundation.org/training/getting-started-with-opentelemetry-lfs148/>
- GrafanaCON 2026 instrumentation lab:
  <https://grafana.com/events/grafanacon/hands-on-labs/opentelemetry-instrumentation/>
