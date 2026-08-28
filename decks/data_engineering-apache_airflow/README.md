# Apache Airflow

Apache Airflow를 단순히 DAG 파일을 작성하는 도구가 아니라,
**시간과 의존성에 따라 반복되는 작업의 실행 상태를 관리하는 workflow orchestrator**로 이해하기 위한 deck이다.

이 deck은 읽기용 설명서와 따라 치는 tutorial을 분리하지 않는다. 개념을 설명한 직후 같은 개념을 실제 Airflow runtime에서
관찰하고, 관찰 결과를 다시 개념 모델로 해석하는 **실습 결합형 textbook**을 지향한다.

## Start here

처음 시작한다면 전체 chapter를 먼저 읽지 않는다. 다음 순서로 environment와 mental model을 함께 준비한다.

1. `bash lab/scripts/preflight.sh`로 host/package/source 준비 상태를 확인한다.
2. [Mental model](textbook/01-mental-model.md)에서 Dag/Task definition과 DagRun/TaskInstance runtime state를 구분한다.
3. [Lab Guide](lab/README.md)의 verification ladder를 따라 local `tasks test`/`dags test`와 scheduler-backed
   `standalone` 실행의 차이를 관찰한다.
4. 같은 Dag를 UI, CLI, log, metadata, output에서 연결해 설명한 뒤 다음 chapter로 진행한다.

첫 학습 session의 목표는 Airflow command를 많이 실행하는 것이 아니다.

> **source가 parse되는 것, local test가 성공하는 것, scheduler-backed DagRun이 존재하는 것, TaskInstance가 실제 실행되는
> 것은 서로 다른 evidence다.**

이 구분이 잡혀야 이후 scheduling, retry, backfill, idempotence를 같은 runtime model 위에서 이해할 수 있다.

## Curriculum

목표 learner level은 **Basic**이다. 상세 goal, learner prerequisites, learning outcomes, concept dependencies, unit
architecture, assessment coverage, 현재 textbook gap과 다음 build handoff는
[Basic Curriculum Plan](docs/curriculum.md)에 정리한다.

Curriculum unit은 chapter/file 경계와 동일하지 않다. 현재 textbook을 먼저 보존하고, review된 learning slice 단위로
필요한 부분만 점진적으로 확장한다.

## Learning Path

1. [Mental model: 정의와 실행을 분리해서 관찰하기](textbook/01-mental-model.md)
2. [Scheduling: data interval과 Airflow 3 timetable semantics를 검증하기](textbook/02-scheduling-and-data-intervals.md)
3. [Task design: failure, retry, side effect를 직접 관찰하기](textbook/03-task-design-and-state.md)

각 chapter는 설명과 실습을 별개 자료로 취급하지 않는다. 실습 결과 자체가 다음 설명의 evidence가 된다.

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

실습 폴더 구조, preflight, verification ladder, U2/U5 starter DAG, fixture, snapshot/reset helper의 사용법은
[Lab Guide](lab/README.md)에 정리한다.

### Runtime Requirements

Airflow 3.3.1 공식 prerequisite 기준으로 Python 3.10~3.14가 테스트 대상이며 local development에는 SQLite를 사용할 수
있다. Airflow는 POSIX 환경을 전제로 하므로 Windows에서는 WSL2나 Linux environment를 사용한다.

이 deck에서는 다음이 필요하다.

- `uv`를 실행할 수 있는 local environment
- 여러 terminal을 열어 runtime과 observation command를 함께 볼 수 있는 환경
- `lab/` 아래에 disposable runtime state와 output을 만들 수 있는 filesystem 권한
- 첫 package resolution에 필요한 network access 또는 이미 준비된 `uv` cache

먼저 다음을 실행한다.

```bash
bash lab/scripts/preflight.sh
```

그 뒤 scheduler-backed runtime이 필요한 단계에서만 `standalone`을 시작한다.

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
schema가 바뀔 수 있으므로 Dag/task authoring은 `airflow.sdk`를 중심으로 사용하고, scheduling lab처럼 필요한 경우에는
Airflow가 public interface로 문서화한 `airflow.timetables`를 사용한다. Internal DB 관측은 read-only로 제한한다.

Airflow 3에서는 bare cron string이 기본적으로 `CronTriggerTimetable` semantics를 사용한다. 이 deck의 scheduling
chapter는 연속 data interval을 학습하기 위해 explicit `CronDataIntervalTimetable`을 사용하며, 이 선택을 Airflow 전체의
default로 일반화하지 않는다.

## References

- [Apache Airflow — Quick Start](https://airflow.apache.org/docs/apache-airflow/stable/start.html)
- [Apache Airflow — Prerequisites](https://airflow.apache.org/docs/apache-airflow/stable/installation/prerequisites.html)
- [Apache Airflow — Airflow 101](https://airflow.apache.org/docs/apache-airflow/stable/tutorial/fundamentals.html)
- [Apache Airflow — Architecture Overview](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [Apache Airflow — Core Concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/)
- [Apache Airflow — Dag Runs](https://airflow.apache.org/docs/apache-airflow/3.3.1/core-concepts/dag-run.html)
- [Apache Airflow — Timetables](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html)
- [Apache Airflow — Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
- [Apache Airflow — Params](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/params.html)
- [Apache Airflow — Connections & Hooks](https://airflow.apache.org/docs/apache-airflow/3.3.1/authoring-and-scheduling/connections.html)
- [Apache Airflow — CLI Reference](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
- [Apache Airflow — Logging and Monitoring](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/index.html)
