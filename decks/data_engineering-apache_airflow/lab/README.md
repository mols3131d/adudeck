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

현재 scaffold는 curriculum의 **U2 Dag authoring/loading**과 **U5 data/configuration boundaries**까지만 준비한다. U7
cumulative integration은 앞 두 slice를 review한 뒤 추가한다.

## Learning preparation

Airflow 3.3.1은 Python 3.10~3.14에서 테스트되며 local development에는 SQLite를 사용할 수 있다. Airflow 자체는 POSIX
환경을 전제로 하므로 Windows에서는 WSL2나 Linux 환경을 사용한다. 이 lab은 production deployment가 아니라 local learning
환경이므로 SQLite와 `standalone`을 의도적으로 사용한다.

학습을 시작하기 전에 Deck directory에서 다음을 실행한다.

```bash
bash lab/scripts/preflight.sh
```

preflight는 다음을 확인한다.

```text
host / filesystem readiness
→ uv 사용 가능 여부
→ Airflow 3.3.1 wrapper resolution
→ local Dag discovery
→ local import-error inspection surface
```

첫 실행에서는 `uvx`가 Airflow package를 resolve해야 하므로 network access와 package cache 준비가 필요할 수 있다.

preflight 성공은 **scheduler-backed runtime이 정상이라는 증거가 아니다.** 아직 DagRun과 TaskInstance를 실제 control
plane에 생성하지 않았다. 준비 단계의 목적은 runtime 문제를 보기 전에 host/package/source 문제를 최대한 먼저 분리하는
것이다.

## Verification ladder

Airflow 학습에서는 서로 다른 검증 수준을 섞지 않는다. 다음 순서로 한 단계씩 올라간다.

```text
L0. environment + local source discovery
        ↓
L1. isolated task / Dag execution test
        ↓
L2. standalone scheduler-backed execution
        ↓
L3. cross-view runtime observation
        ↓
L4. controlled failure / modification / re-observation
```

### L0 — source가 보이는가

```bash
bash lab/scripts/preflight.sh
bash lab/airflow.sh tasks list adudeck_u2_authoring_starter
```

이 단계에서 확인하는 것은 source가 Airflow authoring surface로 해석될 수 있는지다. Task가 목록에 보인다고 실제
TaskInstance가 실행된 것은 아니다.

### L1 — scheduler 없이 task/Dag code를 실행할 수 있는가

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

### L2 — 실제 control-plane runtime을 시작한다

Deck directory에서 실행한다.

```bash
bash lab/airflow.sh standalone
```

standalone terminal을 닫지 않는다. 이후 이 terminal 자체가 component/task log observation surface가 된다.

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

`airflow.sh`는 이 deck의 disposable local state만 사용하고 Apache Airflow 3.3.1을 고정한다. U5 실습을 위해 teaching-only
Variable과 Connection default도 제공한다. 이 값은 실제 credential이 아니며 production configuration 예시가 아니다.

환경 변수로 제공하는 demo Variable과 Connection은 task runtime에서 secrets backend를 통해 resolve된다. Metadata DB row가
아니므로 Airflow UI나 `variables list` / `connections list`에 표시되지 않는다. **Variable/Connection의 논리적 역할과
그 값을 어디에서 resolve하는지는 별개의 문제**로 관찰한다.

Airflow 3에서 bare cron string은 기본적으로 `CronTriggerTimetable` semantics를 사용한다. Scheduling chapter의 reference
DAG는 연속 data interval을 학습하기 위해 `CronDataIntervalTimetable`을 명시적으로 사용한다. 따라서 해당 실습에서 보이는
`[data_interval_start, data_interval_end)`를 모든 cron Dag의 기본 동작으로 일반화하지 않는다.

### L3 — 같은 runtime object를 여러 면에서 연결한다

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

### L4 — 한 조건을 바꾸고 다시 본다

마지막에 failure mode, dependency, Param, task boundary, side effect 중 하나를 바꾼다.

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

1. `bash lab/scripts/preflight.sh`로 environment/source boundary를 확인한다.
2. `textbook/01-mental-model.md`의 definition/runtime separation을 읽는다.
3. U2 starter의 task/dependency를 읽고 `tasks list` 결과를 예측한다.
4. `tasks test`와 `dags test`로 local execution evidence를 본다.
5. `standalone`을 시작하고 같은 Dag를 실제로 trigger한다.
6. `snapshot.sh`로 scheduler-backed DagRun/TaskInstance를 관찰한다.
7. local test와 scheduler-backed execution 사이에서 **생긴 state와 생기지 않은 state**를 비교한다.

이 비교를 설명할 수 있어야 다음 failure/retry나 scheduling 실습으로 넘어간다.

## Practice loop

각 starter를 다음 순서로 사용한다.

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

- 어떤 DagRun과 TaskInstance가 생길 것으로 예상하는가?
- 어떤 state transition을 볼 것인가?
- 어떤 값이 Param, XCom, file/output, Variable, Connection 중 어디에 존재할 것인가?
- 실패시키거나 dependency를 바꾸면 무엇이 달라지고 무엇은 유지될 것인가?

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
Dag parsed / loaded
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

reset 후에는 다시 preflight/L0부터 시작할 필요는 없다. 다만 source나 package 조건을 바꿨다면 preflight를 다시 실행하고,
runtime state만 초기화했다면 L2부터 재실행해 같은 prediction이 재현되는지 확인한다.

## Validation boundary

Repository CI와 Python syntax check는 committed source의 syntax/format과 repository consistency를 확인한다. 그것만으로
Airflow가 Dag를 실제로 parse/load했다는 뜻은 아니다. `preflight`, `tasks test`, `dags test`, `standalone`, cross-view
observation도 각각 서로 다른 validation level이다.

실제 `standalone` runtime에서 Dag loading, scheduler-backed task execution, UI/CLI/metadata observation,
Connection/Variable resolution, controlled failure/recovery가 learner-visible evidence와 일치하는지는 별도의 runtime
validation이 필요하다. 한 단계가 성공했다고 더 높은 validation level을 자동으로 통과한 것으로 간주하지 않는다.
