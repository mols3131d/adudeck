# Apache Airflow Basic Curriculum Plan

이 문서는 이 deck의 **intra-deck curriculum baseline**과 현재 구현 상태를 기록한다.

목표는 Airflow 기능을 폭넓게 나열하는 것이 아니라, learner가 작은 scheduled batch workflow를 직접 정의하고 실행한 뒤
runtime state와 evidence를 사용해 동작을 설명하고 기본적인 failure/reprocessing 문제를 진단할 수 있는 **Basic 수준의
competence**를 만드는 것이다.

Curriculum unit은 chapter/file 경계가 아니다. 하나의 chapter가 여러 unit을 개발할 수 있고, 하나의 unit이 여러 learning
slice에 걸쳐 구현될 수 있다.

## Goal

학습이 끝나면 learner는 작은 batch workflow에 대해 다음 cycle을 스스로 수행할 수 있어야 한다.

```text
workflow 의도와 logical input 정의
        ↓
Dag / Task와 dependency 작성
        ↓
schedule과 run boundary 예측
        ↓
실행
        ↓
DagRun / TaskInstance state 관찰
        ↓
log / metadata / external side effect 해석
        ↓
failure 또는 historical reprocessing 판단
        ↓
안전하게 수정하고 다시 검증
```

production deployment를 운영하는 것이 이 deck의 목표는 아니다. 먼저 **한 machine의 local lab에서도 보이는 Airflow의
control flow, time model, task state, data/configuration boundary를 정확히 이해하는 것**을 목표로 한다.

## Learner Prerequisites

core path는 다음만 가정한다.

- Python 함수, module, decorator의 기본 문법
- terminal에서 command를 실행하고 file path와 environment variable을 다루는 기초
- batch processing에서 "한 번의 logical work가 특정 input/partition을 담당한다"는 기본 감각

SQL 기초는 data-engineering example을 이해하는 데 도움이 되지만 core Airflow mechanism의 필수 prerequisite로 두지
않는다. Docker, Kubernetes, distributed systems 지식도 prerequisite가 아니다.

`uv` 사용 가능 여부처럼 lab을 실행하기 위한 조건은 learner prerequisite가 아니라 runtime requirement로 취급한다.

## Learning Outcomes

Basic curriculum을 마치면 다음을 할 수 있어야 한다.

1. `Dag`, `DagRun`, `Task`, `TaskInstance`를 구분하고 같은 logical execution을 UI, CLI, log, metadata에서 연결한다.
2. `airflow.sdk`와 TaskFlow를 사용해 작은 Dag를 정의하고 dependency를 표현하며, prebuilt Operator도 Task를 만드는
   authoring surface임을 구분한다. Dag parsing/loading과 task execution이 서로 다른 단계라는 것을 설명한다.
3. 선택된 timetable의 semantics를 확인한 뒤 `schedule`, `start_date`, logical date, data interval, manual/scheduled run,
   catchup의 관계를 시간축에서 예측하고 실제 DagRun으로 검증한다. Airflow 3의 bare cron default와 explicit
   data-interval timetable이 다를 수 있음을 구분한다.
4. dependency와 TaskInstance state transition을 바탕으로 task가 왜 실행되었거나 막혔는지 설명하고, 관측·retry·side
   effect 책임을 고려해 task boundary를 판단한다.
5. runtime input, task-to-task metadata, 실제 dataset, external-system credential/configuration이 서로 다른 책임임을
   설명하고 `Params`, XCom, external storage, Connection을 적절한 boundary에 배치한다. Airflow Variable은 runtime
   configuration key/value로 인식하되 task-to-task data channel과 혼동하지 않고, credential을 Params나 XCom에 전달하지
   않는다. Variable/Connection의 논리적 역할과 environment/metadata DB/external secrets backend 같은 resolution
   backend도 구분한다.
6. retry, TaskInstance clear/re-run, catchup, backfill을 같은 개념으로 뭉개지 않고, 같은 logical work의 반복 실행이
   external side effect를 어떻게 다루어야 하는지 idempotence 관점에서 설명하고 수정한다.
7. "Airflow가 안 돈다"는 증상을 parsing/loading, DagRun scheduling, dependency/state, task runtime, external side effect
   문제로 좁히고 최소한의 evidence로 원인을 설명한다.

## Concept Dependencies

```text
U1 Runtime mental model
        |
        v
U2 Dag authoring and loading
        |
        +-------------------+-------------------+
        |                   |                   |
        v                   v                   v
U3 DagRun time model   U4 Task lifecycle   U5 Data/config boundaries
        |                   |                   |
        +-------------------+-------------------+
                            |
                            v
                 U6 Recovery and reprocessing
                            |
                            v
                 U7 Evidence-first integration
```

U3, U4, U5는 모두 U2의 작은 runnable Dag를 공통 실험 대상으로 삼지만 서로 다른 mechanism을 학습한다. U6는 time,
TaskInstance state, data/side-effect boundary가 모두 잡힌 뒤에 다룬다. U7은 앞 unit을 다시 요약하지 않고 learner가 작은
workflow에서 독립적으로 통합 판단하게 한다.

## Unit Architecture

| Unit | Learning responsibility | Learner evidence |
| --- | --- | --- |
| **U1. Runtime mental model** | Airflow가 필요한 이유, Dag/Task definition과 DagRun/TaskInstance runtime identity, Dag Processor → metadata → scheduler/executor → task runtime → API/UI의 state flow | 같은 DagRun/TaskInstance를 여러 observation surface에서 식별하고 각 component가 어떤 state를 읽거나 바꾸는지 설명한다. |
| **U2. Dag authoring and loading** | `airflow.sdk`, TaskFlow, prebuilt Operator의 역할 구분, Dag/Task declaration, dependency, module parsing과 task execution의 분리, Dag loading/import error | 작은 Dag를 직접 작성하고, file 존재 → parse/load → DagRun 생성 → TaskInstance 실행이 서로 다른 단계임을 evidence로 보인다. |
| **U3. DagRun time model** | bare cron default와 explicit timetable의 차이, schedule, `start_date`, logical date, data interval, manual vs scheduled run, catchup | 먼저 실제 timetable을 식별하고 interval/run timing을 예측한 뒤 UI/CLI/metadata timestamp와 비교한다. |
| **U4. Task lifecycle and boundaries** | dependency, 기본 downstream 조건, TaskInstance state, retry-visible state, task boundary의 state/log/retry/side-effect 의미 | intentional failure에서 `running`, `up_for_retry`, `failed`, `upstream_failed`, `success`를 추적하고 task boundary를 설명한다. |
| **U5. Data and configuration boundaries** | TaskFlow/XCom, external storage, DagRun Params, Connection, Variable의 역할과 resolution backend 구분 | 큰 business data와 작은 orchestration metadata를 분리하고, run input·credential/config·task output identifier가 왜 서로 다른 channel을 써야 하는지 판단하며 credential이 task data channel로 흐르지 않게 설계한다. Environment-backed Variable/Connection이 metadata DB row와 다른 visibility를 갖는 이유도 설명한다. |
| **U6. Recovery, reprocessing, idempotence** | retry와 terminal failure, TaskInstance clear/re-run, catchup/backfill, logical input과 wall-clock time, partial side effect, idempotent modification | 같은 logical work를 반복하는 이유와 runtime identity를 구분하고, selected TaskInstance를 controlled clear/re-run한 뒤 side-effect invariant를 검증하며 retry·clear/re-run·backfill·catchup을 근거와 함께 선택한다. |
| **U7. Evidence-first integration** | parsing → scheduling → dependency/state → task runtime → external output을 연결한 diagnosis와 전체 workflow 설계 | 작은 batch workflow를 작성·실행·실패·재처리하고, UI/CLI/log/metadata/output evidence로 동작과 원인을 end-to-end 설명한다. |

## Outcome Development and Assessment Coverage

| Outcome | 먼저 개발하는 unit | Basic 수준의 판단 evidence |
| --- | --- | --- |
| O1 runtime identity와 component/state flow | U1 | 같은 run/task identity를 cross-view로 trace하고 state owner를 설명한다. |
| O2 작은 Dag authoring/loading | U2 | 주어진 요구를 runnable Dag/dependency로 바꾸고 parse/load failure와 runtime failure를 구분한다. |
| O3 schedule/data interval 이해 | U3 | 실제 timetable을 먼저 식별하고 prediction과 실제 DagRun evidence가 일치하는지 설명하며 trigger/data-interval semantics를 구분한다. |
| O4 TaskInstance lifecycle/task boundary | U4 | failure/retry trace를 해석하고 task split/merge 선택을 정당화한다. |
| O5 data/configuration channel 선택 | U5 | Params/XCom/external storage/Connection/Variable 후보를 비교해 책임에 맞는 channel을 선택하고 credential boundary를 지키며 resolution backend와 logical role을 구분한다. |
| O6 recovery/reprocessing/idempotence | U6 | retry, selected TaskInstance clear/re-run, backfill, catchup을 logical-work identity로 비교하고 repeated execution에서 invariant와 side effect를 검증한다. |
| O7 evidence-first diagnosis | U7 | 여러 layer의 evidence를 최소 순서로 모아 하나의 failure를 설명하고 수정 후 재검증한다. |

U7의 cumulative work는 앞 unit의 API나 용어를 다시 말하는 quiz가 아니다. Learner가 다음 흐름을 독립적으로 수행하는
것으로 평가한다.

```text
작은 workflow 설계
→ 결과와 state 예측
→ 실행
→ evidence 관찰
→ failure 또는 reprocessing 판단
→ 수정
→ 재검증
```

## Out of Scope for Basic

다음은 core Basic outcome에 필요해질 때 curriculum delta로 다시 검토한다. 현재는 선행 학습으로 요구하거나 chapter를
만들지 않는다.

- CeleryExecutor/KubernetesExecutor와 distributed production topology
- Kubernetes 기반 HA deployment와 scheduler performance tuning
- dynamic task mapping, complex branching/trigger-rule design
- Sensors/deferrable tasks/Triggerer를 이용한 waiting architecture
- Assets와 event-driven scheduling
- Pools, priority, large-scale concurrency/resource tuning
- custom provider, Hook, plugin, executor 개발
- provider/vendor별 integration 사용법의 깊은 학습
- multi-team/security/authorization 운영 설계

## Current Textbook Coverage

이 section은 curriculum baseline이 아니라 **현재 implementation state**다. File coverage만으로 curriculum completion을
판단하지 않는다.

| Current material | Curriculum coverage | 현재 상태 / 남은 boundary |
| --- | --- | --- |
| [`01-mental-model.md`](../textbook/01-mental-model.md) | U1 strong, U2/U7 foundation | definition/runtime identity와 cross-view evidence의 공통 mental model을 확립한다. |
| [`04-authoring-and-loading.md`](../textbook/04-authoring-and-loading.md) | U2 strong | source → import/parse → discovery → local test → scheduler-backed runtime을 분리하고 controlled parse failure와 Task boundary modification으로 평가한다. 실제 learner runtime execution은 별도 validation boundary다. |
| [`02-scheduling-and-data-intervals.md`](../textbook/02-scheduling-and-data-intervals.md) | U3 strong, U6 historical reprocessing | bare cron default와 explicit data-interval timetable을 구분하고 backfill/catchup의 time model을 관찰한다. |
| [`03-task-design-and-state.md`](../textbook/03-task-design-and-state.md) | U4 strong, U6 retry/idempotence, U5 foundation | intentional failure로 retry/terminal failure와 side-effect idempotence를 관찰하고 XCom/external data boundary의 기초를 만든다. |
| [`05-data-and-configuration-boundaries.md`](../textbook/05-data-and-configuration-boundaries.md) | U5 strong | Params/XCom/external storage/Variable/Connection/Dag code를 ownership과 lifecycle로 비교하고 resolution backend와 logical role을 분리한다. 실제 Variable/Connection resolution observation은 learner runtime validation이 필요하다. |
| [`07-recovery-and-reprocessing.md`](../textbook/07-recovery-and-reprocessing.md) | U6 strong | retry, selected TaskInstance clear/re-run, backfill, catchup을 repeated-logical-work model로 비교하고 downstream re-run과 side-effect invariant를 평가한다. |
| [`06-cumulative-integration.md`](../textbook/06-cumulative-integration.md) | U7 cumulative, U1~U6 integration | learner가 작은 workflow를 직접 설계·실행·실패·수정·재검증하고 최소 evidence로 diagnosis하는 cumulative assessment다. |

현재 content surface는 U1~U7 각각에 substantial explanation/practice/assessment path를 가진다. Fresh runtime review에서
local toolchain/discovery/test path와 U6 same-run clear/re-run path 일부를 calibration했지만,
**learner-visible evidence 전체를 검증하지 않은 상태를 curriculum completion으로 승격하지 않는다.**

## Learning Readiness Status

학습 준비는 curriculum completion과 별도다. Learner가 실습을 시작하기 전에 **환경 문제, source import 문제, metadata
setup, Dag discovery, local test, scheduler-backed runtime 문제를 서로 분리할 수 있는 진입 경로**가 필요하다.

현재 lab은 다음 verification ladder를 제공한다.

```text
L0 environment + toolchain
→ L1 metadata schema + local import/Dag discovery
→ L2 tasks test / dags test
→ L3 standalone scheduler-backed execution
→ L4 cross-view runtime observation
→ L5 controlled failure / modification / re-observation
```

- `lab/scripts/preflight.sh`는 host/filesystem, `uv`, constrained Airflow wrapper resolution까지만 확인한다. Metadata
  schema, local Dag/import discovery, scheduler-backed runtime은 이 단계에서 주장하지 않는다.
- `lab/airflow.sh`는 Apache Airflow 3.3.1, Python 3.12 기본값, 해당 release의 official constraints를 함께 사용해 fresh
  machine의 dependency drift를 줄인다. Python baseline은 필요할 때 `ADUDECK_AIRFLOW_PYTHON`으로 override할 수 있지만
  Airflow 3.3.1이 지원하는 Python 범위 안에서 사용한다.
- `db migrate`는 learner가 직접 실행해 **metadata schema가 존재함과 scheduler가 실행 중임을 분리**해서 관찰한다.
- schema 초기화 뒤 `dags list-import-errors --local`과 `dags list --local`에서 current source와 expected Dag를 확인하고,
  그 다음 `tasks list`로 task definition을 확인한다.
- `tasks test` / `dags test`는 scheduler-backed runtime 전에 task/Dag code를 local execution으로 확인하는 단계로
  사용한다.
- 같은 Dag를 이후 `standalone`에서 trigger해 local test와 실제 DagRun/TaskInstance state 존재 여부를 비교한다.

이 ladder는 learner에게 명령 순서를 외우게 하기 위한 것이 아니다. 각 단계가 **무엇을 증명하고 무엇을 아직 증명하지
못하는지** 구분하게 하는 학습 장치다. `reset.sh --all`로 disposable metadata state를 지운 경우에는 L1부터 다시 수행해
같은 progression이 반복 가능한지도 확인한다.

## Practice Scaffold Status

현재 `lab/`에는 U2와 U5를 시작할 수 있는 작은 starter와 공용 learning-preparation helper가 있다.

- `lab/dags/exercises/u2_authoring_starter.py` — parser-safe authoring/loading baseline과 controlled parse failure
  시작점
- `lab/dags/exercises/u5_boundaries_starter.py` — Param/XCom/file/Variable/Connection responsibility 비교 시작점
- `lab/dags/observable_runtime.py` — U1/U4/U6의 runtime state, retry, clear/re-run, side-effect 관찰에 재사용하는
  reference Dag
- `lab/dags/observable_schedule.py` — U3/U6의 timetable/backfill observation에 재사용하는 reference Dag
- `lab/fixtures/orders.jsonl` — deterministic business-data fixture
- `lab/scripts/preflight.sh` — environment/toolchain readiness check
- `lab/scripts/snapshot.sh` — CLI + read-only metadata + external output observation helper
- `lab/scripts/reset.sh` — lab-owned output 또는 disposable runtime state reset

U7을 위해 별도 permanent starter를 추가하지 않는다.
[`06-cumulative-integration.md`](../textbook/06-cumulative-integration.md)는 learner가 existing starter/reference Dag를
읽고 **local assessment work file을 직접 만들도록 scaffolding을 줄인다.** 이는 U7에서 독립적인 design/diagnosis 능력을
평가하기 위한 의도된 progression이다.

Starter와 helper가 존재한다는 것은 학습 준비가 되어 있다는 뜻이지 learner outcome이 자동으로 검증되었다는 뜻은 아니다.
실제 runtime execution, observation, modification, explanation을 learner-visible evidence로 확인해야 한다.

## Build Handoff

현재 build에서 U1~U7의 주요 textbook learning path는 구현되었다. Fresh Ubuntu calibration으로 L0→L2 local path와 U6의
explicit logical-date DagRun → selective `transform` clear → same-run second completion까지는 material expectation과
실제 runtime evidence가 일치함을 확인했다. 다음 우선순위는 새 chapter가 아니라
**아직 닫지 않은 learner-visible evidence**다.

1. **U2 controlled-failure validation** — learner working copy에서 parse/import failure를 만들고 복구하는 path가
   chapter의 diagnosis model과 일치하는지 확인한다.
2. **U5 runtime boundary validation** — environment-backed Variable/Connection resolution과 Param/XCom/external output의
   evidence가 intended ownership model과 일치하는지 확인한다.
3. **U6 downstream variation** — `transform`만 clear하는 baseline과 downstream까지 포함하는 variation을 side-effect
   invariant로 비교한다.
4. **U7 learner-level integration review** — cumulative assessment를 실제로 수행해 hidden scaffolding이나 prerequisite
   gap이 없는지 검토한다.
5. 발견되는 mismatch는 먼저 local material/playground gap으로 분류하고, learner prerequisite·scope·outcome·dependency를
   바꿔야 할 때만 curriculum delta로 승격한다.

새 topic을 추가하는 것은 현재 completion 조건이 아니다.

## Curriculum Delta Rule

진행 중 새로운 개념이 필요해 보여도 즉시 curriculum에 추가하지 않는다.

```text
Discovery
→ 기존 outcome에 정말 필요한가?
→ local material repair로 해결 가능한가?
→ learner prerequisite / dependency / outcome / scope 변경이 필요한가?
→ smallest curriculum delta 검토
→ accept | reject | defer | split
```

새로운 topic이 현재 Basic outcome에 필요하지 않다면 adjacent topic으로 남기거나 별도 deck 후보로 분리한다.

## Version and Authority Baseline

현재 material version baseline은 Apache Airflow **3.3.1**이다. Dag/task authoring은 `airflow.sdk`를 중심으로 사용하고,
scheduling semantics가 학습 목표일 때는 Airflow가 public interface로 문서화한 `airflow.timetables`를 명시적으로 사용할
수 있다. Internal metadata DB 관측은 학습용 read-only probe로 제한한다. Version-sensitive API, CLI, UI, scheduling
default, internal schema, clear/rerun behavior를 다룰 때는 현재 primary documentation과 실제 lab evidence를 구분해
검증한다.

Airflow 3.3.1의 clear/rerun/backfill은 Dag bundle version 선택에도 영향을 받을 수 있으므로 logical-work identity와
source version을 같은 개념으로 취급하지 않는다.

Local lab toolchain은 기본 Python 3.12와 Airflow 3.3.1 release constraints를 사용한다. 이 pin은 학습 환경 drift를 줄이는
도구이지 production dependency policy가 아니다. 실제 runtime behavior는 여전히 learner-visible execution evidence로
검증해야 한다.
