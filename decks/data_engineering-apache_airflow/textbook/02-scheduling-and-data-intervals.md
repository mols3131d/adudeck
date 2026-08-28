# 02. Scheduling: data interval을 시간축과 runtime에서 검증하기

Airflow scheduling을 "cron 시간이 되면 Python 파일을 실행한다"라고만 이해하면 `start_date`, logical date, data interval,
catchup, backfill이 서로 무관한 옵션처럼 보인다.

이 chapter에서는 세 종류의 시간을 분리한다.

```text
1. data time
   이 DagRun이 담당하는 데이터 구간

2. scheduling time
   scheduler가 그 run을 만들 수 있게 되는 시점

3. wall-clock execution time
   TaskInstance가 실제로 시작하고 끝나는 현실 시간
```

그리고 시간축으로 결과를 **먼저 예측한 뒤**, 실제 2분 schedule Dag를 UI, CLI, log, metadata DB, output에서 관찰한다.

Airflow 3에서는 여기서 한 가지를 먼저 고정해야 한다. Bare cron string을 `schedule="*/2 * * * *"`처럼 넘기면
`[scheduler] create_cron_data_intervals=False`가 기본이므로 `CronTriggerTimetable`이 선택된다. 이 timetable은 cron tick에
run을 trigger하는 데 초점을 두며 기본 data interval은 한 점이다. 이 chapter는 batch data interval을 학습하는 것이
목표이므로 lab Dag에서 **`CronDataIntervalTimetable`을 명시적으로 사용한다.** 따라서 아래의 연속 interval 설명을 모든
Airflow cron schedule의 기본 동작으로 일반화하지 않는다.

## 1. "언제 실행했는가"와 "어느 데이터를 담당하는가"는 다르다

전날 주문을 집계하는 daily pipeline을 생각한다.

```text
2026-08-27 00:00 ---------------- 2026-08-28 00:00
                 data interval
```

8월 27일 하루의 데이터는 구간이 끝날 때까지 계속 들어올 수 있다. 이 구간을 처리하는 scheduled run이 8월 28일 자정 이후에
실행 가능한 것은 자연스럽다.

```text
data interval
[08-27 00:00, 08-28 00:00)
                         |
                         | interval complete
                         v
                   scheduled run eligible
```

실제 task가 queue나 startup delay 때문에 `08-28 00:07`에 시작되어도 담당 data interval이 자동으로 8월 28일로 바뀌지는
않는다.

```text
execution time != data time
```

이 distinction이 retry와 partition 설계의 기반이다.

## 2. Data-interval timetable은 반복되는 interval을 만든다

`CronDataIntervalTimetable`처럼 continuous interval을 만드는 timetable을 단순화하면 다음과 같이 볼 수 있다.

```text
[08-25 00:00, 08-26 00:00)
[08-26 00:00, 08-27 00:00)
[08-27 00:00, 08-28 00:00)
```

`start_date`는 "이 timestamp에 process를 시작하라"는 명령이 아니다. timetable이 첫 scheduling interval을 계산할 때
사용하는 경계다.

따라서 첫 scheduled run이 `start_date`와 같은 순간에 즉시 실행되지 않는 것을 "하루 늦게 실행되는 bug"라고 보면 안 된다.

반대로 `CronTriggerTimetable` 같은 trigger timetable은 같은 cron 표현을 사용해도 scheduling과 data interval을 다르게
모델링한다. Airflow에서 `schedule` 표현만 보고 interval semantics를 추정하지 않고 **어떤 timetable이 실제로 선택되었는지**
확인하는 습관을 갖는다.

## 3. DagRun의 시간 정보를 분리한다

학습할 때 다음 값들을 하나의 "execution date"로 뭉개지 않는다.

```text
logical_date

data_interval_start
data_interval_end

run_after / scheduling eligibility

TaskInstance actual start_date
TaskInstance actual end_date
```

batch pipeline에서는 data interval이 logical partition의 source가 될 수 있다.

```text
DagRun interval
[2026-08-27, 2026-08-28)

        ↓

warehouse.orders/dt=2026-08-27
```

반대로 business partition을 `datetime.now()`로 만들면 delayed execution이나 retry에서 같은 logical work가 다른 날짜를
건드릴 수 있다.

## 4. 실습 Dag: 2분마다 interval을 노출한다

`lab/dags/observable_schedule.py`에는 다음 Dag가 있다.

```text
Dag ID: adudeck_observable_schedule
schedule: CronDataIntervalTimetable("*/2 * * * *", timezone="UTC")
start_date: 2026-01-01 UTC
catchup: False
Task: expose_interval
```

여기서 explicit timetable은 Airflow 3의 global cron default와 무관하게 실습의 interval semantics를 고정한다. 실습 중
`data_interval_start < data_interval_end`가 실제로 성립하는지 먼저 확인하고 이후 prediction을 해석한다.

2분 schedule은 production recommendation이 아니다. **사람이 오래 기다리지 않고 scheduler의 interval 계산을 관찰하기 위한
instrumentation**이다.

Task는 실행될 때 다음 정보를 task log와 `lab/output/` JSON에 남긴다.

```text
run_id
logical_date
data_interval_start
data_interval_end
try_number
```

그리고 20초 동안 `running`에 머물러 UI/CLI/metadata에서 같은 TaskInstance를 찾을 시간을 준다.

## 5. Observable Lab A: Airflow에게 묻기 전에 먼저 계산한다

standalone을 켠다.

```bash
bash lab/airflow.sh standalone
```

별도 terminal에서 Dag가 parsing되었는지 확인한다.

```bash
bash lab/airflow.sh dags list
```

아직 unpause하지 않는다.

현재 UTC 시간이 예를 들어 `12:05:37`이라고 가정해 보자. `*/2 * * * *`의 경계를 직접 그린다.

```text
12:02        12:04        12:06        12:08
  |------------|------------|------------|
```

다음 scheduled run이 어느 interval을 담당할지 먼저 적는다.

```text
prediction
logical date: 12:04
data interval: [12:04, 12:06)
run eligible: 12:06 이후
```

그 다음 Airflow의 timetable 계산을 본다.

```bash
bash lab/airflow.sh dags next-execution \
  adudeck_observable_schedule \
  -n 3 \
  --table
```

CLI는 다음 execution들의 logical date, data interval, run-after 정보를 계산해 보여줄 수 있다.

예측과 다르면 command 결과를 외우지 않는다. 어느 경계를 잘못 해석했는지 시간축을 수정한다.

## 6. Observable Lab B: scheduler가 실제 DagRun을 만들게 한다

Dag를 unpause한다.

```bash
bash lab/airflow.sh dags unpause adudeck_observable_schedule
```

다음 2분 경계에서 새 run이 생기는지 본다.

### 관측면 1 — UI / Grid

`http://localhost:8080`에서 Dag를 열고 새 scheduled DagRun과 `expose_interval` TaskInstance를 본다.

20초의 `running` window 동안 다음을 적는다.

```text
DagRun state:
TaskInstance state:
TaskInstance 실제 시작 시각:
```

### 관측면 2 — CLI

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_schedule -o table
```

방금 run의 `<RUN_ID>`를 골라 여러 번 snapshot한다.

```bash
bash lab/airflow.sh tasks states-for-dag-run \
  adudeck_observable_schedule \
  '<RUN_ID>' \
  -o table
```

가능하면 `running -> success`를 두 snapshot으로 남긴다.

### 관측면 3 — task log

UI task log 또는 standalone terminal에서 다음 marker를 찾는다.

```text
[ADUDECK_OBSERVE] scheduled interval:
```

그 안의 `logical_date`, `data_interval_start`, `data_interval_end`를 기록한다.

### 관측면 4 — metadata DB

```bash
python lab/inspect_metadata.py \
  --dag-id adudeck_observable_schedule \
  --run-id '<RUN_ID>'
```

`dag_run`의 interval 관련 timestamp와 `task_instance`의 actual start/end timestamp를 구분한다.

### 관측면 5 — external output

```bash
ls -lt lab/output/schedule-*.json | head
```

해당 run의 JSON body에서 interval을 다시 확인한다.

파일명은 shell-safe하게 변환되므로 identity를 확인할 때는 JSON 안의 `run_id`를 기준으로 한다.

## 7. 서로 다른 timestamp를 하나의 시간축에 올린다

실제 관측값으로 다음 그림을 완성한다.

```text
data_interval_start                  data_interval_end
        |                                   |
        v                                   v
--------+-----------------------------------+--------- wall clock
                                            |
                                            | run eligible
                                            v
                                      DagRun created
                                            |
                                            v
                                      Task running
                                            |
                                            v
                                      Task success
```

표도 직접 채운다.

| 의미 | 실제 관측값 |
| --- | --- |
| logical date | |
| data interval start | |
| data interval end | |
| DagRun start | |
| TaskInstance start | |
| TaskInstance end | |

값이 서로 다르다고 이상한 것이 아니다. **각 timestamp의 의미가 다르다.**

## 8. wall-clock delay가 logical work를 바꾸면 안 된다

scheduler cycle, execution capacity, process startup, retry 때문에 task는 늦게 시작할 수 있다.

```text
data interval end
        |
        +--- scheduling / queue delay ---+
                                         |
                                         +--- process startup ---+
                                                                  |
                                                                  v
                                                             task starts
```

하지만 logical work는 유지되어야 한다.

```text
partition key
= data interval / logical input에서 결정

not
= task가 우연히 시작된 현재 시각에서 결정
```

같은 이유로 retry가 다음 날 실행되어도 같은 TaskInstance가 담당하는 partition은 임의로 다음 날로 이동하면 안 된다.

## 9. Retry thought experiment

다음 run을 생각한다.

```text
DagRun data interval: [08-27, 08-28)

try 1
actual execution: 08-28 00:03
failed

try 2
actual execution: 08-29 09:30
success
```

두 try의 wall-clock timestamp는 크게 다르다. 하지만 둘은 같은 logical work의 재시도다.

```python
# 위험한 방향
partition = datetime.now().date()
```

이 코드는 try에 따라 다른 partition을 선택할 수 있다.

다음 chapter에서는 의도적인 retry를 발생시켜 이 문제가 side-effect idempotence와 어떻게 연결되는지 관찰한다.

## 10. catchup은 과거 interval을 자동으로 따라갈지 정한다

오래전 `start_date`를 가진 Dag를 오늘 처음 활성화했다고 하자.

```text
start_date                                  now
    |                                        |
    v                                        v
----+----+----+----+----+----+----+----+----+
        historical intervals
```

`catchup=True`라면 normal scheduling의 연장선에서 과거 interval들의 DagRun을 생성할 수 있다.

`catchup=False`라면 일반적으로 최신 scheduling point부터 진행하고 과거 interval을 모두 자동 생성하지 않는다.

중요한 것은 다음이다.

```text
catchup=False
!=
historical data를 다시 처리할 수 없음
```

자동 schedule policy와 명시적 historical operation은 별개다.

## 11. Observable Lab C: backfill을 먼저 dry-run한다

Airflow 3.3에는 explicit backfill command가 있다.

실제 run을 만들기 전에 **과거로 확실한 UTC 범위**를 dry-run한다.

```bash
bash lab/airflow.sh backfill create \
  --dag-id adudeck_observable_schedule \
  --from-date '2026-08-27T00:00:00+00:00' \
  --to-date '2026-08-27T00:04:00+00:00' \
  --max-active-runs 1 \
  --dry-run
```

현재 deck 작성 시각은 2026-08-28 KST이므로 이 범위는 이미 종료된 historical range다. 미래에 실습해도 계속 과거 범위로
남는다.

Airflow 3.3.1의 backfill date range는 inclusive다. 또한 동일 logical date의 기존 run을 다시 만들지 여부는
`--reprocess-behavior`가 결정하며 기본값은 `none`이다. 이 lab의 첫 backfill은 해당 historical range에 기존 run이 없다는
전제에서 진행하고, 이미 run이 있다면 dry-run 결과와 기존 run을 먼저 비교한다.

### 실행 전에 적을 것

- 몇 개 run이 대상일 것으로 예상하는가?
- 각 logical date와 data interval은 무엇일까?
- `catchup=False`인데 explicit backfill 결과가 존재할 수 있을까?

그 다음 dry-run output으로 검증한다.

예상 run 수가 틀려도 괜찮다. **inclusive range가 timetable의 logical dates에 어떻게 적용되는지** 결과를 보고 수정한다.

## 12. Observable Lab D: historical runs를 실제로 만든다

local lab에서만 `--dry-run`을 제거한다.

```bash
bash lab/airflow.sh backfill create \
  --dag-id adudeck_observable_schedule \
  --from-date '2026-08-27T00:00:00+00:00' \
  --to-date '2026-08-27T00:04:00+00:00' \
  --max-active-runs 1
```

`max-active-runs=1`은 correctness requirement가 아니다. 여러 historical run이 순차적으로 보이게 해서
**사람이 state를 따라가기 쉽게 만든 실험 조건**이다.

run 목록을 다시 본다.

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_schedule -o table
```

normal scheduled run과 backfill run을 비교한다.

```text
run_id
logical date
state
실행 시각
```

metadata probe와 output file도 같이 본다.

```bash
python lab/inspect_metadata.py --dag-id adudeck_observable_schedule
ls -lt lab/output/schedule-*.json | head
```

## 13. catchup과 backfill의 차이를 runtime evidence로 설명한다

| 질문 | catchup | backfill |
| --- | --- | --- |
| 누가 시작하는가 | normal scheduler policy | 명시적 historical operation |
| 무엇을 정하는가 | 과거 interval을 자동 생성할지 | 지정 range를 재처리할지 |
| `catchup=False`와 공존 가능한가 | 자동 catchup은 비활성 | explicit backfill은 가능 |
| 관측 evidence | scheduled DagRun 생성 pattern | backfill run / operation |

둘의 이름을 암기하기보다 lab에서 **catchup=False인 Dag도 explicit backfill할 수 있음**을 확인하면 boundary가 선명해진다.

## 14. Scheduling debugging 순서

"왜 지금 실행됐지?" 또는 "왜 아직 안 돌지?"를 만나면 다음 순서로 evidence를 모은다.

### Step 1 — timetable 계산

```bash
bash lab/airflow.sh dags next-execution adudeck_observable_schedule --table
```

### Step 2 — DagRun 존재 여부

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_schedule -o table
```

### Step 3 — interval과 DagRun state

UI와 metadata probe를 확인한다.

### Step 4 — TaskInstance state

DagRun이 존재한다고 Task가 즉시 실행되는 것은 아니다. dependency와 execution condition을 따로 본다.

### Step 5 — logical time과 wall-clock time 분리

늦게 실행되었다는 사실만으로 잘못된 interval이라고 단정하지 않는다.

## Practice

### 1. Interval prediction

실습 Dag의 explicit `CronDataIntervalTimetable("*/2 * * * *", timezone="UTC")`에 대해 `10:00`, `10:02`, `10:04`,
`10:06` 경계를 그리고 각 run의 interval과 run-after를 적는다. 그 다음 bare cron string을 사용하는 Airflow 3 기본
`CronTriggerTimetable`이라면 어떤 값이 달라질지도 비교한다.

### 2. Cross-view timestamp audit

실제 한 run을 골라 채운다.

```text
run_id:
logical_date:
data_interval_start:
data_interval_end:
DagRun start_date:
TaskInstance start_date:
TaskInstance end_date:
```

각 timestamp가 같은 의미가 아닌 이유를 설명한다.

### 3. Retry transfer

08-27 partition을 처리하는 TaskInstance가 08-29에 retry되었다.

- `datetime.now()`를 partition key로 쓰면 어떤 invariant가 깨지는가?
- data interval 기반 key를 쓰면 무엇을 유지할 수 있는가?

### 4. Catchup vs backfill

다음 요구를 각각 어떤 mechanism으로 모델링할지 정한다.

1. 새 Dag 활성화 시 지난 7일 normal schedule을 모두 처리한다.
2. 지난달 3일치 transform bug를 수정해 그 range만 다시 계산한다.
3. 신규 table을 historical data로 채운다.

### 5. Evidence-first diagnosis

예상과 다른 scheduled run을 발견했다. 원인을 추측하기 전에 다음 evidence를 모은다.

```text
next-execution output
list-runs output
metadata dag_run row
task log interval marker
output JSON
```

이 evidence를 하나의 시간축으로 합쳐 설명한다.

## Checkpoint

다음을 자신의 말로 설명할 수 있으면 다음 chapter로 간다.

> Airflow의 cron schedule은 하나의 semantics만 갖지 않는다. 이 chapter의 `CronDataIntervalTimetable`에서는 DagRun이
> 연속 data interval을 갖고 interval 끝 이후에 scheduling될 수 있다. Airflow 3의 bare cron default인
> `CronTriggerTimetable`은 다른 time model을 사용한다. 어떤 timetable인지 먼저 확인한 뒤 logical/data time과 실제
> wall-clock execution time을 분리해야 한다. catchup은 normal scheduling policy이고, backfill은 명시적인 historical
> reprocessing operation이다.

## References

- [Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
- [Dag Run](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html)
- [Timetables — trigger vs data interval](https://airflow.apache.org/docs/apache-airflow/stable/authoring-and-scheduling/timetable.html)
- [Configuration — create_cron_data_intervals](https://airflow.apache.org/docs/apache-airflow/3.3.1/configurations-ref.html)
- [CLI Reference — next-execution / backfill](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
- [FAQ — start_date and data interval](https://airflow.apache.org/docs/apache-airflow/stable/faq.html)
