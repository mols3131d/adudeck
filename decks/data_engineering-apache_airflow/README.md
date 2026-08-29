# Apache Airflow

Apache Airflow를 단순한 DAG-file runner가 아니라
**시간과 의존성에 따라 반복되는 workflow의 runtime state를 관리하는 orchestrator**로 이해하기 위한 deck이다.

설명과 lab을 분리하지 않는다. Learner는 먼저 state를 예측하고, 실제 Airflow에서 같은 DagRun/TaskInstance를 여러
observation surface로 확인한 뒤 다시 mental model로 설명한다.

## Goal

Basic path를 마치면 작은 batch workflow에서 다음 cycle을 수행할 수 있어야 한다.

```text
workflow / logical input 정의
→ Dag / Task 작성
→ schedule / state 예측
→ 실행
→ runtime evidence 관찰
→ failure/reprocessing 판단
→ side effect를 안전하게 수정
→ 재검증
```

Production deployment 운영 자체는 범위가 아니다.

## Start here

처음에는 command 수를 늘리지 않는다.

```bash
bash lab/scripts/preflight.sh
bash lab/airflow.sh db migrate
```

그 다음 [U1 Mental model](textbook/01-mental-model.md)을 읽고 [Lab Guide](lab/README.md)의 verification ladder를 따른다.

첫 session의 핵심 distinction:

```text
source file exists
!=
Dag parses/discovers
!=
local test succeeds
!=
scheduler-backed DagRun exists
!=
TaskInstance executes
!=
external output is correct
```

## Learning path

Curriculum unit과 file 생성 번호는 같지 않다. **아래 순서를 학습 순서로 사용한다.**

| Unit | 핵심 질문 | Textbook |
| --- | --- | --- |
| U1 Runtime mental model | definition과 runtime identity는 어떻게 다른가? | [01 Mental model](textbook/01-mental-model.md) |
| U2 Authoring/loading | source는 언제 Dag/Task definition이 되는가? | [04 Authoring/loading](textbook/04-authoring-and-loading.md) |
| U3 Time model | logical date/data interval과 wall-clock은 어떻게 다른가? | [02 Scheduling](textbook/02-scheduling-and-data-intervals.md) |
| U4 Task lifecycle | dependency, failure, retry, side effect는 어떻게 연결되는가? | [03 Task design/state](textbook/03-task-design-and-state.md) |
| U5 Data/config boundary | Param, XCom, data, config, credential의 owner는 누구인가? | [05 Data/config boundaries](textbook/05-data-and-configuration-boundaries.md) |
| U6 Recovery/reprocessing | retry, clear/re-run, backfill, catchup은 언제 다른가? | [07 Recovery/reprocessing](textbook/07-recovery-and-reprocessing.md) |
| U7 Integration | 최소 evidence로 workflow를 설계·진단·수정할 수 있는가? | [06 Cumulative integration](textbook/06-cumulative-integration.md) |

상세 outcome/dependency/coverage는 [Basic Curriculum Plan](docs/curriculum.md)이 source of truth다.

## Learning contract

주요 hands-on unit은 다음 cycle을 사용한다.

```text
Target
→ Predict
→ Run
→ Observe
→ Explain
→ Change one condition
→ Re-observe
```

실습 성공 기준은 command success가 아니다.

> **어떤 runtime object/state가 바뀌었고, 그 판단을 어느 evidence로 했는지 설명할 수 있어야 한다.**

### Evidence levels

```text
source/import
→ Dag/task discovery
→ local tasks test / dags test
→ standalone scheduler-backed execution
→ UI/CLI/log/metadata correlation
→ external side effect
```

Airflow 3.3.1의 `tasks test`는 dependency check나 DB state recording 없이 task를 test하는 local surface다. Local test
성공을 scheduler-backed execution 증거로 승격하지 않는다.

## Lab

Lab은 production topology를 재현하지 않는다. 한 machine에서 control flow와 state를 관찰하기 위한 disposable
environment다.

```text
lab/
├── airflow.sh
├── dags/
├── fixtures/
├── inspect_metadata.py
├── scripts/
└── output/        # runtime-generated, gitignored
```

주요 helper:

```bash
bash lab/scripts/preflight.sh
bash lab/airflow.sh standalone
bash lab/scripts/snapshot.sh <DAG_ID> [RUN_ID]
bash lab/scripts/reset.sh
```

`inspect_metadata.py`는 학습용 read-only probe다. Airflow internal metadata schema를 application integration API로
취급하지 않는다.

## Validation boundary

Repository CI가 통과해도 learner-visible Airflow runtime을 자동으로 검증한 것은 아니다.

| Evidence | 말할 수 있는 것 |
| --- | --- |
| repository CI | committed tree의 deterministic checks |
| primary-doc review | version-sensitive command/API expectation |
| local discovery/test | source와 local execution surface |
| standalone run | actual DagRun/TaskInstance runtime evidence |
| output inspection | external business side effect |

특히 UI/CLI/metadata와 external output은 서로 다른 responsibility를 관찰한다.

## Version baseline

- Apache Airflow: **3.3.1**
- default lab Python: **3.12**
- Dag authoring: `airflow.sdk`
- local runtime: `standalone`
- metadata inspection: read-only

Airflow 3.3.1은 `airflow.sdk`를 stable Dag-authoring public interface로 제공한다. CLI, UI, scheduling default, internal
schema처럼 version-sensitive한 surface는 current primary documentation과 실제 lab evidence를 구분해 검증한다.

## Scope boundary

Basic core에서 다루지 않는다.

- distributed production executor/topology 운영
- Kubernetes HA/performance tuning
- dynamic mapping/complex branching의 깊은 설계
- deferrable/sensor architecture
- assets/event-driven scheduling
- large-scale resource tuning
- custom provider/plugin/executor 개발
- multi-team authorization/security 운영

새 topic은 current outcome에 실제로 필요할 때만 curriculum delta로 검토한다.

## References

- [Airflow 3.3.1 documentation](https://airflow.apache.org/docs/apache-airflow/3.3.1/)
- [Core concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/)
- [CLI reference](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
- [Timetables](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html)
