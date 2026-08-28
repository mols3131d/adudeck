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
│   ├── reset.sh
│   └── snapshot.sh
└── output/                  # runtime-generated, gitignored
```

기존 `observable_*` DAG는 textbook에서 mechanism을 관찰하기 위한 reference experiment다. `dags/exercises/`의 starter
DAG는 learner가 직접 prediction, modification, failure, comparison을 수행하기 위한 시작점이다.

현재 scaffold는 curriculum의 **U2 Dag authoring/loading**과 **U5 data/configuration boundaries**까지만 준비한다. U7
cumulative integration은 앞 두 slice를 review한 뒤 추가한다.

## Start the runtime

Deck directory에서 실행한다.

```bash
bash lab/airflow.sh standalone
```

별도 terminal에서 DAG loading 상태를 확인한다. U2의 controlled parse failure를 확인할 때는 serialized metadata가 아니라
현재 source를 직접 parse하는 local mode를 사용한다.

```bash
bash lab/airflow.sh dags list --local
bash lab/airflow.sh dags list-import-errors --local
```

`airflow.sh`는 이 deck의 disposable local state만 사용하고 Apache Airflow 3.3.1을 고정한다. U5 실습을 위해 teaching-only
Variable과 Connection default도 제공한다. 이 값은 실제 credential이 아니며 production configuration 예시가 아니다.

환경 변수로 제공하는 demo Connection은 task runtime에서 resolve되며 Airflow UI나 `connections list`에 저장된 row처럼
나타나지 않을 수 있다. 이 차이 자체를 credential/configuration storage와 task runtime lookup의 boundary로 해석한다.

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
DagRun exists
!=
TaskInstance executed
```

실습 중 starter를 깨뜨리는 것은 허용된 controlled failure다. 원인을 evidence로 확인한 뒤 정상 parse 상태로 복구한다.

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
→ installation/runtime 수준의 shared value

Connection
→ external-system endpoint / credential configuration
```

Connection password는 log, XCom, output에 기록하지 않는다. Learner는 requirement를 하나 바꾼 뒤 해당 값이 어느 channel에
속해야 하는지 다시 판단한다.

manual trigger 예:

```bash
bash lab/airflow.sh dags trigger \
  -c '{"region":"apac"}' \
  adudeck_u5_boundaries_starter
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

## Validation boundary

Repository CI와 Python syntax check는 starter가 parse 가능한 Python source라는 수준을 확인할 수 있다. 실제 Airflow
runtime에서 DAG loading, task execution, UI/CLI/metadata 관측, Connection/Variable resolution까지 성공했는지는 별도의
runtime evidence가 필요하다.
