# Apache Airflow

Apache Airflow를 단순히 DAG 파일을 작성하는 도구가 아니라,
**시간과 의존성에 따라 반복되는 작업의 실행 상태를 관리하는 workflow orchestrator**로 이해하기 위한 deck이다.

이 deck은 읽기용 설명서와 따라 치는 tutorial을 분리하지 않는다. 개념을 설명한 직후 같은 개념을 실제 Airflow runtime에서
관찰하고, 관찰 결과를 다시 개념 모델로 해석하는 **실습 결합형 textbook**을 지향한다.

## Curriculum Baseline

이 deck의 목표 learner level은 **Basic**이다. 여기서 Basic은 Airflow의 기능 목록을 많이 아는 상태가 아니라,
작은 scheduled batch workflow를 직접 정의하고 실행한 뒤 runtime state와 evidence를 사용해 동작을 설명하고 기본적인
failure/reprocessing 문제를 진단할 수 있는 수준을 뜻한다.

### Goal

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

### Learner Prerequisites

core path는 다음만 가정한다.

- Python 함수, module, decorator의 기본 문법
- terminal에서 command를 실행하고 file path와 environment variable을 다루는 기초
- batch processing에서 "한 번의 logical work가 특정 input/partition을 담당한다"는 기본 감각

SQL 기초는 data-engineering example을 이해하는 데 도움이 되지만 core Airflow mechanism의 필수 prerequisite로 두지
않는다. Docker, Kubernetes, distributed systems 지식도 prerequisite가 아니다.

### Learning Outcomes

Basic curriculum을 마치면 다음을 할 수 있어야 한다.

1. `Dag`, `DagRun`, `Task`, `TaskInstance`를 구분하고 같은 logical execution을 UI, CLI, log, metadata에서 연결한다.
2. `airflow.sdk`와 TaskFlow를 사용해 작은 Dag를 정의하고 dependency를 표현하며, prebuilt Operator도 Task를 만드는
   authoring surface임을 구분한다. Dag parsing/loading과 task execution이 서로 다른 단계라는 것을 설명한다.
3. `schedule`, `start_date`, logical date, data interval, manual/scheduled run, catchup의 관계를 시간축에서 예측하고
   실제 DagRun으로 검증한다.
4. dependency와 TaskInstance state transition을 바탕으로 task가 왜 실행되었거나 막혔는지 설명하고, 관측·retry·side
   effect 책임을 고려해 task boundary를 판단한다.
5. runtime input, task-to-task metadata, 실제 dataset, external-system credential/configuration이 서로 다른 책임임을
   설명하고 `Params`, XCom, external storage, Connection을 적절한 boundary에 배치한다. Airflow Variable은 shared value
   surface로 인식하되 task-to-task data channel과 혼동하지 않고, credential을 Params나 XCom에 전달하지 않는다.
6. retry, TaskInstance clear/re-run, catchup, backfill을 같은 개념으로 뭉개지 않고, 같은 logical work의 반복 실행이
   external side effect를 어떻게 다루어야 하는지 idempotence 관점에서 설명하고 수정한다.
7. "Airflow가 안 돈다"는 증상을 parsing/loading, DagRun scheduling, dependency/state, task runtime, external side effect
   문제로 좁히고 최소한의 evidence로 원인을 설명한다.

### Concept Dependencies

unit은 chapter/file 경계가 아니라 learning responsibility다. 하나의 chapter가 여러 unit을 개발할 수 있고, unit 하나가
여러 learning slice에 걸쳐 구현될 수도 있다.

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

### Unit Architecture

| Unit | Learning responsibility | Learner evidence |
| --- | --- | --- |
| **U1. Runtime mental model** | Airflow가 필요한 이유, Dag/Task definition과 DagRun/TaskInstance runtime identity, Dag Processor → metadata → scheduler/executor → task runtime → API/UI의 state flow | 같은 DagRun/TaskInstance를 여러 observation surface에서 식별하고 각 component가 어떤 state를 읽거나 바꾸는지 설명한다. |
| **U2. Dag authoring and loading** | `airflow.sdk`, TaskFlow, prebuilt Operator의 역할 구분, Dag/Task declaration, dependency, module parsing과 task execution의 분리, Dag loading/import error | 작은 Dag를 직접 작성하고, file 존재 → parse/load → DagRun 생성 → TaskInstance 실행이 서로 다른 단계임을 evidence로 보인다. |
| **U3. DagRun time model** | schedule, `start_date`, logical date, data interval, manual vs scheduled run, catchup | 실행 전에 interval/run timing을 예측하고 실제 UI/CLI/metadata timestamp와 비교한다. |
| **U4. Task lifecycle and boundaries** | dependency, 기본 downstream 조건, TaskInstance state, retry-visible state, task boundary의 state/log/retry/side-effect 의미 | intentional failure에서 `running`, `up_for_retry`, `failed`, `upstream_failed`, `success`를 추적하고 task boundary를 설명한다. |
| **U5. Data and configuration boundaries** | TaskFlow/XCom, external storage, DagRun Params, Connection, Variable의 역할 구분 | 큰 business data와 작은 orchestration metadata를 분리하고, run input·credential/config·task output identifier가 왜 서로 다른 channel을 써야 하는지 판단하며 credential이 task data channel로 흐르지 않게 설계한다. |
| **U6. Recovery, reprocessing, idempotence** | retry와 terminal failure, TaskInstance clear/re-run, catchup/backfill, logical input과 wall-clock time, partial side effect, idempotent modification | 같은 logical interval을 반복 실행해도 의도한 final invariant에 수렴하도록 side effect를 수정하고, retry·clear/re-run·historical reprocessing 방식을 근거와 함께 선택한다. |
| **U7. Evidence-first integration** | parsing → scheduling → dependency/state → task runtime → external output을 연결한 diagnosis와 전체 workflow 설계 | 작은 batch workflow를 작성·실행·실패·재처리하고, UI/CLI/log/metadata/output evidence로 동작과 원인을 end-to-end 설명한다. |

### Outcome Development and Assessment Coverage

| Outcome | 먼저 개발하는 unit | Basic 수준의 판단 evidence |
| --- | --- | --- |
| O1 runtime identity와 component/state flow | U1 | 같은 run/task identity를 cross-view로 trace하고 state owner를 설명한다. |
| O2 작은 Dag authoring/loading | U2 | 주어진 요구를 runnable Dag/dependency로 바꾸고 parse/load failure와 runtime failure를 구분한다. |
| O3 schedule/data interval 이해 | U3 | 시간축 prediction과 실제 DagRun evidence가 일치하는지 설명한다. |
| O4 TaskInstance lifecycle/task boundary | U4 | failure/retry trace를 해석하고 task split/merge 선택을 정당화한다. |
| O5 data/configuration channel 선택 | U5 | Params/XCom/external storage/Connection/Variable 후보를 비교해 책임에 맞는 channel을 선택하고 credential boundary를 지킨다. |
| O6 recovery/reprocessing/idempotence | U6 | retry, clear/re-run, backfill 같은 반복 실행에서 invariant와 side effect를 검증하고 unsafe design을 수정한다. |
| O7 evidence-first diagnosis | U7 | 여러 layer의 evidence를 최소 순서로 모아 하나의 failure를 설명하고 수정 후 재검증한다. |

U7의 cumulative work는 앞 unit의 API나 용어를 다시 말하는 quiz가 아니라, learner가
**작은 workflow의 설계 → 예측 → 실행 → 관찰 → failure/reprocessing → 수정 → 재검증**을 독립적으로 수행하는 것으로
평가한다.

### Out of Scope for Basic

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

현재 textbook은 이미 여러 unit의 calibration material을 갖고 있다. curriculum을 새로 설계했다고 기존 chapter를 즉시
분해하거나 다시 쓰지 않는다.

| Current material | Curriculum coverage | 현재 gap |
| --- | --- | --- |
| [`01-mental-model.md`](textbook/01-mental-model.md) | U1 strong, U2 partial, U7 diagnostic foundation | learner가 작은 Dag를 직접 authoring하고 loading/import failure를 수정하는 progression이 얕다. |
| [`02-scheduling-and-data-intervals.md`](textbook/02-scheduling-and-data-intervals.md) | U3 strong, U6 historical reprocessing partial | catchup/backfill evidence는 강하지만 retry·clear/re-run·backfill을 하나의 repeated-logical-work model에서 비교하는 cumulative judgment가 더 필요하다. |
| [`03-task-design-and-state.md`](textbook/03-task-design-and-state.md) | U4 strong, U5 XCom/external-storage/Param partial, U6 retry/idempotence strong | Param을 experiment control로 사용하지만 input/configuration boundary로 일반화하지 않았고 Connection/Variable/credential boundary와 전체 end-to-end assessment가 부족하다. |

이 표는 curriculum unit 자체가 아니라 현재 textbook implementation의 coverage를 보여준다. file coverage만으로 curriculum
completion을 판단하지 않는다.

## Textbook + Lab Contract

이 deck의 주요 개념은 다음 학습 loop를 따른다.

```text
개념 모델
   ↓
실행 전에 결과 예측
   ↓
실제 Airflow에서 실행
   ↓
여러 관측면에서 같은 runtime object 확인
   ↓
예측과 관측의 차이 설명
   ↓
코드/설정 변경 후 다시 관찰
```

실습의 목적은 command를 성공시키는 것이 아니다. **Airflow가 내부에서 어떤 runtime object와 state를 만들고 바꾸는지
사람이 증거를 통해 설명할 수 있게 만드는 것**이다.

### Observability Contract

각 runtime 실습은 가능한 한 같은 실행을 네 관점에서 본다.

1. **UI / Grid** — 사람이 workflow 전체와 TaskInstance state를 시각적으로 본다.
2. **CLI snapshot** — `dags list-runs`, `tasks states-for-dag-run` 등으로 특정 시점의 state를 텍스트로 고정한다.
3. **component/task log** — scheduler가 실행 가능성을 판단하고 task code가 실제로 수행되는 흔적을 본다.
4. **metadata + side effect** — read-only metadata DB probe와 `lab/output/`을 통해 control-plane state와 실제 output을
   구분한다.

네 화면의 값이 항상 같은 형태로 보일 필요는 없다. 중요한 것은 **서로 다른 관측면이 같은 DagRun/TaskInstance를 어떻게
표현하는지 연결하는 것**이다.

metadata DB는 Airflow의 internal implementation surface다. 이 deck의 `inspect_metadata.py`는 학습용
**read-only probe**로만 사용하며 application integration API로 취급하지 않는다.

## Lab Runtime

lab은 Apache Airflow 3.3.1의 `standalone` mode를 사용한다. production topology를 재현하려는 환경이 아니라,
**한 컴퓨터에서 Dag Processor, scheduler, API/UI, executor/task execution과 metadata state를 관찰하기 위한 학습 환경**이다.

### Runtime Requirements

- `uv`를 실행할 수 있는 local environment
- 여러 terminal을 열어 runtime과 observation command를 함께 볼 수 있는 환경
- `lab/` 아래에 disposable runtime state와 output을 만들 수 있는 filesystem 권한

Deck directory에서 다음을 실행한다.

```bash
bash lab/airflow.sh standalone
```

`lab/airflow.sh`는 다음을 deck 내부에 고정한다.

- `AIRFLOW_HOME` → `lab/.airflow/`
- DAG folder → `lab/dags/`
- 실습 output → `lab/output/`
- example DAG 비활성화
- local lab에서만 authentication을 단순화

runtime state와 output은 `.gitignore` 대상이며 Git에 기록하지 않는다.

별도 terminal에서 같은 wrapper로 CLI를 사용한다.

```bash
bash lab/airflow.sh dags list
bash lab/airflow.sh dags list-runs adudeck_observable_runtime -o table
```

metadata DB는 Python 표준 라이브러리만 사용하는 probe로 읽는다.

```bash
python lab/inspect_metadata.py --dag-id adudeck_observable_runtime
```

UI는 기본 API Server port인 `http://localhost:8080`에서 확인한다.

## Version Baseline

작성 기준은 Apache Airflow 3.3.1이다. Airflow 3에서는 standalone Dag Processor가 필수 component이고, executor는 별도
daemon이 아니라 scheduler 안에서 사용되는 execution abstraction이다. minor release에서 CLI, UI, internal metadata
schema가 바뀔 수 있으므로 public authoring surface는 `airflow.sdk`를 사용하고 internal DB 관측은 read-only로 제한한다.

## References

- [Apache Airflow — Architecture Overview](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [Apache Airflow — Core Concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/)
- [Apache Airflow — Dag Runs](https://airflow.apache.org/docs/apache-airflow/3.3.1/core-concepts/dag-run.html)
- [Apache Airflow — Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
- [Apache Airflow — Params](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html)
- [Apache Airflow — Connections & Hooks](https://airflow.apache.org/docs/apache-airflow/3.3.1/authoring-and-scheduling/connections.html)
- [Apache Airflow — CLI Reference](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
- [Apache Airflow — Logging and Monitoring](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/index.html)
