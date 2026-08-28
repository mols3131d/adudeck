# Apache Airflow

Apache Airflow를 단순히 DAG 파일을 작성하는 도구가 아니라,
**시간과 의존성에 따라 반복되는 작업의 실행 상태를 관리하는 workflow orchestrator**로 이해하기 위한 deck이다.

이 deck은 읽기용 설명서와 따라 치는 tutorial을 분리하지 않는다. 개념을 설명한 직후 같은 개념을 실제 Airflow runtime에서
관찰하고, 관찰 결과를 다시 개념 모델로 해석하는 **실습 결합형 textbook**을 지향한다.

## Goal

학습이 끝나면 다음을 할 수 있어야 한다.

- `Dag`, `DagRun`, `Task`, `TaskInstance`를 구분하고 하나의 workflow 실행을 state 변화로 추적한다.
- Dag Processor, scheduler, executor, task runtime, API Server, metadata database의 책임을 설명한다.
- `schedule`, `start_date`, data interval, catchup, backfill의 관계를 시간축 위에서 설명하고 실제 run으로 검증한다.
- TaskFlow와 dependency를 사용해 작은 batch workflow를 구성하고 task 경계와 data 전달 방식을 합리적으로 선택한다.
- retry와 failure를 직접 발생시킨 뒤 UI, CLI, log, metadata를 함께 사용해 어느 layer에서 문제가 생겼는지 좁힌다.
- 같은 logical work가 재실행될 때 external side effect가 어떻게 달라지는지 관찰하고 idempotent한 방향으로 수정한다.

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

## Prerequisites

- Python 함수, module, decorator의 기본 문법
- SQL과 batch data processing에 대한 기본 감각
- process, environment variable, file path 같은 실행 환경의 기초 개념
- `uv` 사용 가능 환경

Docker, Kubernetes, distributed systems 지식은 core learning path의 prerequisite로 두지 않는다. production deployment를
다룰 때 필요한 지식으로 남긴다.

## Lab Runtime

lab은 Apache Airflow 3.3.1의 `standalone` mode를 사용한다. production topology를 재현하려는 환경이 아니라,
**한 컴퓨터에서 Dag Processor, scheduler, API/UI, executor/task execution과 metadata state를 관찰하기 위한 학습 환경**이다.

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

## Scope

core path에서 먼저 다룬다.

1. Airflow가 해결하는 문제와 runtime mental model
2. definition과 runtime object의 분리
3. Dag Processor → metadata → scheduler → executor/task runtime의 state flow
4. scheduling, data interval, catchup, backfill
5. TaskFlow, dependency, retry, idempotence
6. XCom과 external storage의 역할 구분
7. UI/CLI/log/metadata/output을 함께 사용하는 state 중심 debugging

초기 scope에서는 다음을 다루지 않는다.

- CeleryExecutor/KubernetesExecutor의 production 운영 설계
- Kubernetes 기반 HA deployment
- 특정 cloud vendor의 managed Airflow
- custom provider, plugin, executor 개발
- 대규모 scheduler performance tuning

core mental model과 관측 방법이 잡힌 뒤 실제 필요가 생길 때 확장한다.

## Learning Path

1. [Mental model: 정의와 실행을 분리해서 관찰하기](textbook/01-mental-model.md)
2. [Scheduling: data interval을 시간축과 runtime에서 검증하기](textbook/02-scheduling-and-data-intervals.md)
3. [Task design: failure, retry, side effect를 직접 관찰하기](textbook/03-task-design-and-state.md)

각 chapter는 설명과 실습을 별개 자료로 취급하지 않는다. 실습 결과 자체가 다음 설명의 evidence가 된다.

## Version Baseline

작성 기준은 Apache Airflow 3.3.1이다. Airflow 3에서는 standalone Dag Processor가 필수 component이고, executor는 별도
daemon이 아니라 scheduler 안에서 사용되는 execution abstraction이다. minor release에서 CLI, UI, internal metadata
schema가 바뀔 수 있으므로 public authoring surface는 `airflow.sdk`를 사용하고 internal DB 관측은 read-only로 제한한다.

## References

- [Apache Airflow — Architecture Overview](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [Apache Airflow — Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
- [Apache Airflow — CLI Reference](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
- [Apache Airflow — Logging and Monitoring](https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/index.html)
