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
TaskInstance state, data/side-effect boundary가 모두 잡힌 뒤에 다룬다.

## Unit Architecture

| Unit | Learning responsibility | Learner evidence |
| --- | --- | --- |
| **U1. Runtime mental model** | Airflow가 필요한 이유, Dag/Task definition과 DagRun/TaskInstance runtime identity, Dag Processor → metadata → scheduler/executor → task runtime → API/UI의 state flow | 같은 DagRun/TaskInstance를 여러 observation surface에서 식별하고 각 component가 어떤 state를 읽거나 바꾸는지 설명한다. |
| **U2. Dag authoring and loading** | `airflow.sdk`, TaskFlow, prebuilt Operator의 역할 구분, Dag/Task declaration, dependency, module parsing과 task execution의 분리, Dag loading/import error | 작은 Dag를 직접 작성하고, file 존재 → parse/load → DagRun 생성 → TaskInstance 실행이 서로 다른 단계임을 evidence로 보인다. |
| **U3. DagRun time model** | bare cron default와 explicit timetable의 차이, schedule, `start_date`, logical date, data interval, manual vs scheduled run, catchup | 먼저 실제 timetable을 식별하고 interval/run timing을 예측한 뒤 UI/CLI/metadata timestamp와 비교한다. |
| **U4. Task lifecycle and boundaries** | dependency, 기본 downstream 조건, TaskInstance state, retry-visible state, task boundary의 state/log/retry/side-effect 의미 | intentional failure에서 `running`, `up_for_retry`, `failed`, `upstream_failed`, `success`를 추적하고 task boundary를 설명한다. |
| **U5. Data and configuration boundaries** | TaskFlow/XCom, external storage, DagRun Params, Connection, Variable의 역할과 resolution backend 구분 | 큰 business data와 작은 orchestration metadata를 분리하고, run input·credential/config·task output identifier가 왜 서로 다른 channel을 써야 하는지 판단하며 credential이 task data channel로 흐르지 않게 설계한다. Environment-backed Variable/Connection이 metadata DB row와 다른 visibility를 갖는 이유도 설명한다. |
| **U6. Recovery, reprocessing, idempotence** | retry와 terminal failure, TaskInstance clear/re-run, catchup/backfill, logical input과 wall-clock time, partial side effect, idempotent modification | 같은 logical interval을 반복 실행해도 의도한 final invariant에 수렴하도록 side effect를 수정하고, retry·clear/re-run·historical reprocessing 방식을 근거와 함께 선택한다. |
| **U7. Evidence-first integration** | parsing → scheduling → dependency/state → task runtime → external output을 연결한 diagnosis와 전체 workflow 설계 | 작은 batch workflow를 작성·실행·실패·재처리하고, UI/CLI/log/metadata/output evidence로 동작과 원인을 end-to-end 설명한다. |

## Outcome Development and Assessment Coverage

| Outcome | 먼저 개발하는 unit | Basic 수준의 판단 evidence |
| --- | --- | --- |
| O1 runtime identity와 component/state flow | U1 | 같은 run/task identity를 cross-view로 trace하고 state owner를 설명한다. |
| O2 작은 Dag authoring/loading | U2 | 주어진 요구를 runnable Dag/dependency로 바꾸고 parse/load failure와 runtime failure를 구분한다. |
| O3 schedule/data interval 이해 | U3 | 실제 timetable을 먼저 식별하고 prediction과 실제 DagRun evidence가 일치하는지 설명하며 trigger/data-interval semantics를 구분한다. |
| O4 TaskInstance lifecycle/task boundary | U4 | failure/retry trace를 해석하고 task split/merge 선택을 정당화한다. |
| O5 data/configuration channel 선택 | U5 | Params/XCom/external storage/Connection/Variable 후보를 비교해 책임에 맞는 channel을 선택하고 credential boundary를 지키며 resolution backend와 logical role을 구분한다. |
| O6 recovery/reprocessing/idempotence | U6 | retry, clear/re-run, backfill 같은 반복 실행에서 invariant와 side effect를 검증하고 unsafe design을 수정한다. |
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

이 section은 curriculum baseline이 아니라 **현재 implementation state**다. Curriculum을 새로 설계했다고 기존 chapter를
즉시 분해하거나 다시 쓰지 않는다.

| Current material | Curriculum coverage | 현재 gap |
| --- | --- | --- |
| [`01-mental-model.md`](../textbook/01-mental-model.md) | U1 strong, U2 partial, U7 diagnostic foundation | learner가 작은 Dag를 직접 authoring하고 loading/import failure를 수정하는 progression이 얕다. |
| [`02-scheduling-and-data-intervals.md`](../textbook/02-scheduling-and-data-intervals.md) | U3 strong, U6 historical reprocessing partial | Airflow 3 bare cron default와 explicit data-interval timetable을 구분하도록 보강했다. retry·clear/re-run·backfill을 하나의 repeated-logical-work model에서 비교하는 cumulative judgment는 여전히 더 필요하다. |
| [`03-task-design-and-state.md`](../textbook/03-task-design-and-state.md) | U4 strong, U5 XCom/external-storage/Param partial, U6 retry/idempotence strong | Param을 experiment control로 사용하지만 Connection/Variable resolution backend와 전체 end-to-end assessment는 별도 U5/U7 slice에서 더 다룬다. |

File coverage만으로 curriculum completion을 판단하지 않는다.

## Practice Scaffold Status

현재 `lab/`에는 U2와 U5를 시작할 수 있는 scaffold가 있다.

- `lab/dags/exercises/u2_authoring_starter.py` — parser-safe authoring/loading baseline과 controlled parse failure
  시작점
- `lab/dags/exercises/u5_boundaries_starter.py` — Param/XCom/file/Variable/Connection responsibility 비교 시작점
- `lab/fixtures/orders.jsonl` — deterministic business-data fixture
- `lab/scripts/snapshot.sh` — CLI + read-only metadata + external output observation helper
- `lab/scripts/reset.sh` — lab-owned output 또는 disposable runtime state reset

이 상태는 **실습을 시작할 준비가 되었다는 의미**이지 U2/U5 learning outcome이 이미 검증되었다는 의미가 아니다. 실제
learner-visible runtime 실행, observation, modification, explanation을 review한 뒤 해당 slice를 accepted로 볼 수 있다.

U7 cumulative integration starter는 U2/U5의 실제 학습 흐름을 먼저 검토하기 전에는 추가하지 않는다.

## Build Handoff

현재 material을 보존하면서 다음 build loop에서 우선할 gap은 다음과 같다.

1. **U2 Dag authoring and loading** — learner가 작은 Dag를 직접 만들고 parse/load/import failure를 수정하는 end-to-end
   slice.
2. **U5 Data and configuration boundaries** — Params, XCom, external storage, Connection, Variable의 책임과 resolution
   backend를 비교하고 올바른 channel을 선택하는 slice.
3. **U7 Evidence-first integration** — 작은 workflow 하나를 설계·실행·실패·재처리하고 최소 evidence로 end-to-end
   diagnosis와 수정 후 재검증까지 수행하는 cumulative slice.

이 순서는 chapter 수를 늘리기 위한 계획이 아니다. 각 slice가 기존 material 안에 통합되는 편이 낫다면 새 chapter를 만들지
않는다. 다음 slice를 구현할 때는 해당 slice를 독립적으로 review한 뒤 다음 increment로 넘어간다.

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
default, internal schema를 다룰 때는 현재 primary documentation과 실제 lab evidence를 구분해 검증한다.
