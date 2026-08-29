# Apache Airflow Lab

이 디렉토리는 textbook의 개념을 실제 Airflow 3.3.1 runtime에서 관찰하고 수정하기 위한 local learning environment다.

실습의 성공 기준은 command가 성공하는 것이 아니라, learner가
**무엇이 바뀔지 예측하고 같은 DagRun/TaskInstance를 여러 evidence surface에서 연결해 설명할 수 있는가**다.

## Structure

```text
lab/
├── airflow.sh
├── inspect_metadata.py
├── dags/
│   ├── observable_runtime.py
│   ├── observable_schedule.py
│   └── exercises/
│       ├── u2_authoring_starter.py
│       └── u5_boundaries_starter.py
├── fixtures/
│   └── orders.jsonl
├── scripts/
│   ├── preflight.sh
│   ├── reset.sh
│   └── snapshot.sh
└── output/                  # runtime-generated, gitignored
```

기존 `observable_*` DAG는 textbook에서 mechanism을 관찰하기 위한 reference experiment다. `dags/exercises/`의 starter
DAG는 learner가 직접 prediction, modification, failure, comparison을 수행하기 위한 시작점이다.

영구 starter는 **U2 Dag authoring/loading**과 **U5 data/configuration boundaries**에만 둔다. U6 recovery는 기존
`observable_runtime`/`observable_schedule`을 재사용한다. U7 cumulative integration은 scaffolding을 더 줄여, learner가
기존 starter/reference DAG를 읽고 local assessment work file을 직접 구성한다. 별도 U7 framework를 미리 만들지 않는다.

## Learning preparation

Airflow 3.3.1은 Python 3.10~3.14에서 테스트되며 local development에는 SQLite를 사용할 수 있다. Airflow 자체는 POSIX
환경을 전제로 하므로 Windows에서는 WSL2나 Linux 환경을 사용한다. 이 lab은 production deployment가 아니라 local learning
환경이므로 SQLite와 `standalone`을 의도적으로 사용한다.

이 lab wrapper는 기본적으로 다음 toolchain을 요청한다.

```text
Apache Airflow 3.3.1
Python 3.12
Airflow 3.3.1 release constraints for Python 3.12
```

Python baseline은 필요하면 `ADUDECK_AIRFLOW_PYTHON`으로 바꿀 수 있지만 Airflow 3.3.1이 지원하는 Python 범위 안에서
사용한다. Release constraints는 fresh machine에서 transitive dependency drift를 줄이기 위한 학습 환경 장치다.

학습을 시작하기 전에 Deck directory에서 다음을 실행한다.

```bash
bash lab/scripts/preflight.sh
```

preflight는 다음을 확인한다.

```text
host / filesystem readiness
→ uv 사용 가능 여부
→ constrained Airflow 3.3.1 wrapper resolution
→ local source import-error surface
```

첫 실행에서는 `uv`가 Python, Airflow release constraints와 package를 resolve해야 하므로 network access와 package cache
준비가 필요할 수 있다.

preflight 성공은 **metadata DB가 준비되었거나 expected Dag가 DB-aware CLI surface에 나타나거나 scheduler-backed
runtime이 정상이라는 증거가 아니다.** 준비 단계의 목적은 runtime 문제를 보기 전에 host/package/source import 문제를
최대한 먼저 분리하는 것이다.

## Verification ladder

Airflow 학습에서는 서로 다른 검증 수준을 섞지 않는다. 다음 순서로 한 단계씩 올라간다.

```text
L0. environment + local import surface
        ↓
L1. metadata schema + Dag discovery
        ↓
L2. isolated task / Dag execution test
        ↓
L3. standalone scheduler-backed execution
        ↓
L4. cross-view runtime observation
        ↓
L5. controlled failure / modification / re-observation
```

### L0 — toolchain과 local source import가 준비됐는가

```bash
bash lab/scripts/preflight.sh
```

이 단계에서는 `dags list-import-errors --local`을 사용해 serialized DB content 대신 현재 local source의 import-error
surface를 본다. 오류가 없다는 것은 source import 단계의 evidence이지 metadata schema, DagModel, DagRun, TaskInstance가
존재한다는 뜻이 아니다.

### L1 — control-plane storage를 만들고 Dag discovery를 확인한다

Airflow 공식 tutorial처럼 local metadata schema를 먼저 초기화한다.

```bash
bash lab/airflow.sh db migrate
```

그 다음 local Dag discovery를 확인한다.

```bash
bash lab/airflow.sh dags list --local
```

다음 네 Dag를 찾는다.

```text
adudeck_observable_runtime
adudeck_observable_schedule
adudeck_u2_authoring_starter
adudeck_u5_boundaries_starter
```

U2 starter의 task definition도 확인한다.

```bash
bash lab/airflow.sh tasks list adudeck_u2_authoring_starter
```

이 단계에서 metadata DB와 Airflow schema가 존재하고 Dag/task definition을 찾을 수 있지만 scheduler는 아직 실행하지
않았다. 다음을 구분한다.

```text
metadata schema exists
!=
Dag definition is discoverable
!=
scheduler is running
!=
DagRun exists
!=
TaskInstance executed
```

### L2 — scheduler 없이 task/Dag code를 실행할 수 있는가

Airflow 공식 tutorial의 local testing path를 사용한다.

```bash
bash lab/airflow.sh tasks test \
  adudeck_u2_authoring_starter \
  inspect_source \
  2026-01-01
```

전체 Dag도 local test할 수 있다.

```bash
bash lab/airflow.sh dags test \
  adudeck_u2_authoring_starter \
  2026-01-01
```

`tasks test`와 `dags test`는 local test execution이다. 실제 scheduler-backed DagRun/TaskInstance state를 metadata DB에
남기는 실행과 동일하게 해석하지 않는다. 이 차이가 다음 단계의 학습 대상이다.

### L3 — 실제 control-plane runtime을 시작한다

Deck directory에서 실행한다.

```bash
bash lab/airflow.sh standalone
```

standalone은 이미 준비한 metadata DB를 사용하면서 scheduler, Dag Processor, API/UI 등 local runtime component를
시작한다. terminal을 닫지 않는다. 이후 이 terminal 자체가 component/task log observation surface가 된다.

별도 terminal에서 scheduler가 사용하는 environment와 같은 wrapper로 Dag를 확인한다.

```bash
bash lab/airflow.sh dags list
bash lab/airflow.sh dags list-import-errors -o table
```

U2의 controlled parse failure를 현재 source 자체에서 확인할 때는 serialized metadata 대신 local mode를 사용한다.

```bash
bash lab/airflow.sh dags list --local
bash lab/airflow.sh dags list-import-errors --local -o table
```

`airflow.sh`는 이 deck의 disposable local state만 사용한다. U5 실습을 위해 teaching-only Variable과 Connection default도
제공한다. 이 값은 실제 credential이 아니며 production configuration 예시가 아니다.

환경 변수로 제공하는 demo Variable과 Connection은 task runtime에서 secrets backend를 통해 resolve된다. Metadata DB row가
아니므로 Airflow UI나 `variables list` / `connections list`에 표시되지 않는다. **Variable/Connection의 논리적 역할과
그 값을 어디에서 resolve하는지는 별개의 문제**로 관찰한다.

Airflow 3에서 bare cron string은 기본적으로 `CronTriggerTimetable` semantics를 사용한다. Scheduling chapter의 reference
DAG는 연속 data interval을 학습하기 위해 `CronDataIntervalTimetable`을 명시적으로 사용한다. 따라서 해당 실습에서 보이는
`[data_interval_start, data_interval_end)`를 모든 cron Dag의 기본 동작으로 일반화하지 않는다.

### L4 — 같은 runtime object를 여러 면에서 연결한다

실제 Dag를 trigger한 뒤 최소한 다음을 연결한다.

```text
UI / Grid
CLI DagRun + TaskInstance state
component / task log
read-only metadata probe
external output
```

단순히 모든 화면을 여는 것이 목적이 아니다. `dag_id`, `run_id`, `task_id`, `try_number` 같은 identity를 사용해 서로 다른
surface가 **같은 logical execution**을 가리키는지 설명한다.

### L5 — 한 조건을 바꾸고 다시 본다

마지막에 failure mode, dependency, Param, task boundary, clear selector, downstream 범위, side effect 중 하나를 바꾼다.

```text
prediction
→ intervention
→ observation
→ explanation
→ invariant 확인
```

baseline과 variation을 구분하지 않으면 단순 실행 tutorial에 머무르게 된다.

## First learning session

처음부터 모든 lab을 돌리지 않는다. 첫 session의 권장 path는 다음과 같다.

1. `bash lab/scripts/preflight.sh`로 environment/toolchain/local import boundary를 확인한다.
2. `textbook/01-mental-model.md`의 definition/runtime separation을 읽는다.
3. `db migrate`를 실행하고 **schema가 존재하는 것과 scheduler가 실행되는 것의 차이**를 적는다.
4. `dags list --local`에서 expected Dag를 찾고 U2 starter의 `tasks list` 결과를 예측·확인한다.
5. `tasks test`와 `dags test`로 local execution evidence를 본다.
6. `standalone`을 시작하고 같은 Dag를 실제로 trigger한다.
7. `snapshot.sh`로 scheduler-backed DagRun/TaskInstance를 관찰한다.
8. local test와 scheduler-backed execution 사이에서 **생긴 state와 생기지 않은 state**를 비교한다.

이 비교를 설명할 수 있어야 다음 failure/retry나 scheduling 실습으로 넘어간다.

## Practice loop

각 starter/reference experiment를 다음 순서로 사용한다.

```text
Target
→ Predict
→ Run / trigger
→ Observe
→ Interpret
→ 한 조건 수정
→ Re-observe
```

실행 전에 최소한 다음을 적는다.

- 어떤 DagRun과 TaskInstance가 생기거나 다시 scheduling될 것으로 예상하는가?
- 어떤 state transition을 볼 것인가?
- 어떤 값이 Param, XCom, file/output, Variable, Connection 중 어디에 존재할 것인가?
- 실패·dependency·clear selector를 바꾸면 무엇이 달라지고 무엇은 유지될 것인가?

## U2 — Dag authoring and loading starter

DAG:

```text
adudeck_u2_authoring_starter
```

starter는 parser-safe한 두 task와 하나의 dependency만 제공한다. 다음을 learner가 직접 수행한다.

1. trigger 전에 만들어질 TaskInstance를 예측한다.
2. 독립 state/log/retry boundary가 필요한 task 하나를 추가하고 이유를 설명한다.
3. 의도적으로 import/parse error 하나를 만들고 `dags list-import-errors --local`과 component log에서 evidence를 찾는다.
4. error를 복구한 뒤 다음 상태를 구분한다.

```text
Python file exists
!=
local import surface has no error
!=
metadata schema exists
!=
Dag definition is discoverable
!=
local tasks/dags test succeeds
!=
scheduler-backed DagRun exists
!=
TaskInstance executed by the runtime
```

실습 중 starter를 깨뜨리는 것은 허용된 controlled failure다. 원인을 evidence로 확인한 뒤 정상 parse 상태로 복구한다.

Airflow의 Dag file은 단순히 한 번 실행되는 application entrypoint가 아니다. Dag Processor가 반복해서 parse하므로
top-level code에는 network/database 호출 같은 무거운 work를 두지 않는다. U2에서는 같은 work를 top-level과 task body에
각각 놓았을 때 **언제 실행되는가**를 구분하는 것이 중요하다.

## U5 — Data and configuration boundaries starter

DAG:

```text
adudeck_u5_boundaries_starter
```

fixture는 `fixtures/orders.jsonl`에 있고 runtime output은 `output/u5/`에 생긴다.

이 starter의 baseline은 다음 책임 분리를 보여준다.

```text
DagRun Param
→ 이번 run의 입력 선택

XCom / TaskFlow return
→ 작은 dataset identifier / evidence

fixtures + output files
→ 실제 business data

Variable
→ Airflow runtime configuration key/value
  (truly runtime-dependent shared setting에 사용)

Connection
→ external-system endpoint / credential configuration
```

version control로 관리할 수 있는 고정 설정까지 Variable로 옮기지 않는다. Airflow 공식 문서도 대부분의 설정은 Dag code에
두고, Variable은 실제 runtime-dependent value에 사용하는 방향을 권한다.

이 lab의 Variable과 Connection은 environment backend에서 resolve되지만, 동일한 논리적 key/connection id가 metadata DB나
외부 secrets backend에서 resolve되는 deployment도 가능하다. Backend가 달라져도 task가 요구하는 책임 자체가 바뀌는 것은
아니다.

Connection password는 log, XCom, output에 기록하지 않는다. Learner는 requirement를 하나 바꾼 뒤 해당 값이 어느 channel에
속해야 하는지 다시 판단한다.

manual trigger 예:

```bash
bash lab/airflow.sh dags trigger \
  -c '{"region":"apac"}' \
  adudeck_u5_boundaries_starter
```

`region`은 JSON Schema 기반 Param validation을 사용한다. 허용되지 않은 값을 넣었을 때 DagRun이 만들어지는지 먼저
예측하고 UI/CLI evidence로 확인한다. Validation failure와 task runtime failure를 같은 failure로 취급하지 않는다.

## U6 — Recovery and reprocessing

별도 U6 Dag를 만들지 않는다. 다음 두 reference Dag를 재사용한다.

```text
adudeck_observable_runtime
adudeck_observable_schedule
```

`observable_runtime`에서는 retry와 completed TaskInstance의 selected clear/re-run을 비교한다. Airflow 3.3.1 manual trigger는
`--logical-date`를 생략하면 logical date가 `None`일 수 있으므로, clear 실험은 재현 가능한 identity를 먼저 명시한다.

```bash
RUN_ID='adudeck_recovery_2026_08_27'
LOGICAL_DATE='2026-08-27T00:00:00+00:00'

bash lab/airflow.sh dags trigger \
  -r "$RUN_ID" \
  -l "$LOGICAL_DATE" \
  -c '{"failure_mode":"none"}' \
  adudeck_observable_runtime
```

Run이 성공한 뒤 run 목록과 snapshot에서 지정한 `RUN_ID`와 `LOGICAL_DATE`가 실제 evidence와 일치하는지 확인한다. 그 다음
broad operation을 바로 승인하지 않고 logical date와 task selector로 target을 좁힌다.

```bash
bash lab/airflow.sh tasks clear \
  adudeck_observable_runtime \
  -s "$LOGICAL_DATE" \
  -e "$LOGICAL_DATE" \
  -t '^transform$'
```

같은 logical date에 다른 run이 있거나 confirmation target이 예상보다 넓으면 승인하지 않는다. 대상이 맞을 때만 disposable
local lab에서 `-y`를 사용할 수 있다. `-d` variation은 downstream side effect도 다시 수행해야 하는지를 business
invariant로 판단하기 위한 실험이다.

`observable_schedule`에서는 scheduling chapter의 catchup/backfill evidence를 재사용한다. U6의 핵심은 command가 아니라
**retry / clear-re-run / backfill / catchup이 어떤 logical work를 왜 다시 실행하는지 구분하는 것**이다.

## U7 — Cumulative integration

U7에는 permanent starter를 두지 않는다.
[`../textbook/06-cumulative-integration.md`](../textbook/06-cumulative-integration.md)의 assessment contract에 따라
learner가 `dags/exercises/` 아래 local work file을 직접 만들거나 별도 disposable copy에서 작업한다.

이 단계에서는 helper가 답을 대신 만들지 않는다. learner가 다음을 스스로 연결해야 한다.

```text
source / parse-load
→ DagRun / TaskInstance
→ schedule / logical input
→ data/config ownership
→ failure / recovery
→ external side-effect invariant
→ 최소 evidence diagnosis
```

## Observe one run

Dag 전체 run 목록:

```bash
bash lab/scripts/snapshot.sh adudeck_u5_boundaries_starter
```

특정 run을 선택한 뒤:

```bash
bash lab/scripts/snapshot.sh \
  adudeck_u5_boundaries_starter \
  '<RUN_ID>'
```

helper는 CLI state, read-only metadata probe, external output file 목록을 한 곳에서 보여준다. 결과를 대신 해석하지는
않는다.

## Reset

external output만 초기화:

```bash
bash lab/scripts/reset.sh
```

metadata DB까지 포함한 disposable local runtime을 완전히 초기화하려면 먼저 `standalone` process를 종료한 뒤 명시적으로
실행한다.

```bash
bash lab/scripts/reset.sh --all
```

`--all`은 `lab/.airflow/`와 `lab/output/`만 삭제한다. fixture, DAG source, textbook은 건드리지 않는다.

`--all` 후에는 metadata schema도 사라지므로 L1의 `db migrate`부터 다시 시작한다. Source/package 조건까지 바뀌었다면
preflight/L0도 다시 수행한다.

## Validation boundary

Repository CI와 Python syntax check는 committed source의 syntax/format과 repository consistency를 확인한다. 그것만으로
Airflow가 Dag를 실제로 parse/load했다는 뜻은 아니다. `preflight`, `db migrate`, `dags list --local`, `tasks test`,
`dags test`, `standalone`, cross-view observation도 각각 서로 다른 validation level이다.

실제 `standalone` runtime에서 Dag loading, scheduler-backed task execution, UI/CLI/metadata observation,
Connection/Variable resolution, selected TaskInstance clear/re-run, controlled failure/recovery가 learner-visible
evidence와 일치하는지는 별도의 runtime validation이 필요하다. 한 단계가 성공했다고 더 높은 validation level을 자동으로
통과한 것으로 간주하지 않는다.
