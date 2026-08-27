# Apache Airflow

Apache Airflow를 단순히 DAG 파일을 작성하는 도구가 아니라,
**시간과 의존성에 따라 반복되는 작업의 실행 상태를 관리하는 workflow orchestrator**로 이해하기 위한 deck이다.

이 deck은 Airflow 3.3.x의 core concepts를 기준으로 한다. 특정 cloud managed service나 production deployment recipe보다,
Airflow 내부에서 어떤 object와 state가 만들어지고 어떤 component가 그것을 변경하는지 이해하는 데 초점을 둔다.

## Goal

학습이 끝나면 다음을 할 수 있어야 한다.

- `Dag`, `DagRun`, `Task`, `TaskInstance`를 구분하고 하나의 workflow 실행을 state 변화로 추적한다.
- Dag Processor, scheduler, executor, worker, API Server, metadata database의 책임을 설명한다.
- `schedule`, `start_date`, data interval, catchup, backfill의 관계를 시간축 위에서 설명한다.
- TaskFlow와 dependency를 사용해 작은 batch workflow를 구성하고, task 경계와 data 전달 방식을 합리적으로 선택한다.
- 실패한 workflow를 단순 재실행하기 전에 어느 state에서 문제가 생겼는지 좁혀서 진단한다.

## Prerequisites

필수 prerequisite는 크지 않다.

- Python 함수, module, decorator의 기본 문법
- SQL과 batch data processing에 대한 기본 감각
- process, environment variable, file path 같은 실행 환경의 기초 개념

Docker, Kubernetes, distributed systems 지식은 core learning path의 prerequisite로 두지 않는다. 해당 지식은 production
deployment를 다룰 때 필요해진다.

## Scope

이 deck에서 먼저 다룬다.

1. Airflow가 해결하는 문제와 runtime mental model
2. `Dag` 정의와 실제 `DagRun`의 분리
3. scheduler와 task execution의 state flow
4. scheduling, data interval, catchup, backfill
5. TaskFlow, dependency, retry, idempotence
6. XCom과 external storage의 역할 구분
7. 작은 DAG의 local test와 state 중심 debugging

초기 scope에서 제외한다.

- CeleryExecutor/KubernetesExecutor의 production 운영 설계
- Kubernetes 기반 HA deployment
- 특정 cloud vendor의 managed Airflow
- custom provider, plugin, executor 개발
- 대규모 scheduler performance tuning

core mental model이 잡힌 뒤 필요한 항목만 별도 chapter로 확장한다.

## Learning Path

1. [Mental model: 정의와 실행을 분리해서 보기](01-mental-model.md)
2. [Scheduling: data interval을 기준으로 시간 이해하기](02-scheduling-and-data-intervals.md)
3. [Task design: 재실행 가능한 작업과 data 경계 만들기](03-task-design-and-state.md)

각 chapter의 practice는 command를 그대로 따라 치는 것보다 prediction, tracing, explanation, debugging을 우선한다.

## Version Baseline

작성 시점의 Apache Airflow stable documentation은 3.3.1이다. minor release에서 세부 API나 UI는 바뀔 수 있으므로, 이
deck은 가능한 한 version-independent한 core state model을 중심으로 설명한다.

## References

- [Apache Airflow — Core Concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/)
- [Apache Airflow — Architecture Overview](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [Apache Airflow — Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
