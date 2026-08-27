# 02. Scheduling: data interval을 시간축과 runtime에서 검증하기

Airflow scheduling에서 가장 흔한 오해는 `schedule="@daily"`를 단순히 "매일 자정에 실행"이라고만 이해하는 것이다.

Airflow의 scheduled workflow를 이해하려면 세 시간을 분리해야 한다.

```text
1. data time
   이 DagRun이 담당하는 데이터 구간

2. scheduling time
   scheduler가 이 run을 만들 수 있게 되는 시점

3. wall-clock execution time
   task process가 실제로 시작되고 끝나는 현실 시간
```

이 chapter에서는 이 관계를 먼저 시간축으로 계산하고, 실제 2분 schedule Dag를 실행해 **예측한 interval과 Airflow가 기록한
runtime state가 일치하는지 관찰**한다.

## 1. 왜 "오늘 run"이라는 표현이 위험한가

전날 주문을 집계하는 daily pipeline을 생각한다.

```text
2026-08-27 00:00 ---------------- 2026-08-28 00:00
                 data interval
```

8월 27일 하루의 데이터는 8월 27일이 끝나기 전까지 계속 들어올 수 있다. 따라서 이 구간을 완전히 처리하는 scheduled run은
interval이 끝난 뒤 실행 가능해지는 것이 자연스럽다.

```text
data interval
[08-27 00:00, 08-28 00:00)
                         |
                         | interval complete
                         v
                   scheduled run eligible
```

실제 task가 08-28 00:07에 시작되었다고 해도 이 run이 담당하는 data interval이 08-28 데이터로 바뀌는 것은 아니다.

### 핵심 distinction

```text
"언제 실행했는가?"
!=
"어느 시간 구간의 데이터를 담당하는가?"
```

이 distinction이 retry, backfill, partition 설계까지 이어진다.

## 2. schedule은 반복되는 interval을 만든다

`@daily`처럼 interval-based timetable을 단순화하면 다음과 같은 연속 구간을 생각할 수 있다.

```text
[08-25 00:00, 08-26 00:00)
[08-26 00:00, 08-27 00:00)
[08-27 00:00, 08-28 00:00)
```

`start_date`는 "그 순간 process를 시작하라"는 timer command가 아니다. timetable이 첫 scheduling interval을 계산할 때 사용하는
경계다.

따라서 daily Dag의 첫 scheduled run이 `start_date`와 같은 시각에 즉시 실행되지 않는 상황은 이상하지 않다.

## 3. logical date와 data interval

DagRun에는 실행을 식별하는 시간 정보가 있다.

학습할 때는 다음을 한 덩어리로 외우지 않는다.

```text
logical_date

data_interval_start
data_interval_end

run_after / 실제 scheduling 가능 시각

TaskInstance start/end wall-clock time
```

특히 batch data engineering에서는 data interval을 partition key를 결정하는 입력으로 사용할 수 있다.

```text
DagRun interval
[2026-08-27, 2026-08-28)

        ↓ logical data

warehouse.orders/dt=2026-08-27
```

반대로 task 안에서 `datetime.now()`를 business partition의 기준으로 사용하면 retry나 delayed execution에서 다른 날짜를
건드릴 수 있다.

## 4. 실습 대상: 2분 schedule을 사용하는 Dag

`lab/dags/observable_schedule.py`에는 다음 Dag가 있다.

```text
Dag ID: adudeck_observable_schedule
schedule: */2 * * * *
catchup: False
Task: expose_interval
```

2분 schedule은 production recommendation이 아니라 **사람이 기다리지 않고 scheduling cycle을 관찰하기 위한 실험 장치**다.

Task는 실행될 때 다음 값을 log와 JSON output에 남긴다.

```text
run_id
logical_date
data_interval_start
data_interval_end
try_number
```

그리고 20초 동안 `running` 상태를 유지해 UI, CLI, metadata DB에서 같은 TaskInstance를 찾을 시간을 확보한다.

## 5. Observable Lab A: 실행 전에 다음 interval을 예측한다

Airflow standalone이 켜져 있지 않다면 시작한다.

```bash
bash lab/airflow.sh standalone
```

별도 terminal에서 Dag가 보이는지 확인한다.

```bash
bash lab/airflow.sh dags list
```

아직 unpause하지 않는다.

먼저 Airflow가 계산하는 다음 execution을 확인하기 **전에**, 현재 UTC 시간을 보고 다음 2분 경계를 직접 적는다.

예를 들어 현재가 다음과 같다고 하자.

```text
12:05:37 UTC
```

2분 경계가 짝수 분이라고 가정하면 다음 interval과 run-after 시점을 먼저 예상한다.

```text
예상 data interval: [12:04, 12:06)
예상 run 가능 시점: 12:06 이후
```

정답을 외우는 것이 아니라 timetable을 시간축으로 그리는 연습이다.

### Airflow의 계산과 비교한다

```bash
bash lab/airflow.sh dags next-execution \
  adudeck_observable_schedule \
  -n 3 \
  --table
```

CLI는 `logical_date`, `data_interval.start`, `data_interval.end`, `run_after` 같은 scheduling 정보를 계산해 보여줄 수 있다.

자신의 예측과 비교한다.

틀렸다면 바로 command를 다시 외우지 않는다. 어느 경계를 잘못 잡았는지 시간축을 수정한다.

## 6. Observable Lab B: scheduler가 실제 DagRun을 만들게 한다

Dag를 unpause한다.

```bash
bash lab/airflow.sh dags unpause adudeck_observable_schedule
```

다음 2분 경계를 기다리는 동안 UI의 Dag page를 연다.

### 관측 1: UI

새 scheduled DagRun이 나타나는지 본다.

Task `expose_interval`이 `running`인 20초 동안 다음을 기록한다.

```text
DagRun state:
TaskInstance state:
실제 wall-clock start time:
```

### 관측 2: CLI

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_schedule -o table
```

방금 생성된 `<RUN_ID>`를 골라 task state를 본다.

```bash
bash lab/airflow.sh tasks states-for-dag-run \
  adudeck_observable_schedule \
  '<RUN_ID>' \
  -o table
```

20초 안에 여러 번 실행해 `running -> success`를 직접 잡아본다.

### 관측 3: task log

UI task log 또는 standalone terminal에서 다음 marker를 찾는다.

```text
[ADUDECK_OBSERVE] scheduled interval:
```

그 안의 `data_interval_start`, `data_interval_end`를 적는다.

### 관측 4: metadata DB

```bash
python lab/inspect_metadata.py \
  --dag-id adudeck_observable_schedule \
  --run-id '<RUN_ID>'
```

`dag_run` row와 `task_instance` row의 timestamp를 구분해서 본다.

### 관측 5: external output

```bash
ls -lt lab/output/schedule-*.json | head
cat lab/output/schedule-<RUN_ID에 대응하는 파일>.json
```

파일 이름은 shell-safe하게 변환되므로 `run_id`와 정확히 같은 문자열은 아닐 수 있다. JSON body의 `run_id`로 동일한 run인지
확인한다.

## 7. 관측 결과를 하나의 시간축으로 합친다

실제 값을 이용해 다음 그림을 완성한다.

```text
data_interval_start                  data_interval_end
        |                                   |
        v                                   v
--------+-----------------------------------+-------- time
                                            |
                                            | scheduler may create run
                                            v
                                      DagRun created
                                            |
                                            v
                                      Task running
                                            |
                                            v
                                      Task success
```

그리고 네 종류의 시간을 적는다.

| 의미 | 실제 관측값 |
| --- | --- |
| logical date | |
| data interval start | |
| data interval end | |
| TaskInstance actual start | |
| TaskInstance actual end | |

`TaskInstance actual start`가 data interval start와 다르다는 것은 bug가 아니다.

## 8. execution delay가 생겨도 logical work는 바뀌지 않는다

scheduler cycle, execution capacity, task startup, retry 등으로 실제 실행은 늦어질 수 있다.

```text
data interval end
        |
        +---- scheduler delay ----+
                                  |
                                  +---- execution delay ----+
                                                          |
                                                          v
                                                    task starts
```

하지만 task가 처리해야 하는 logical data가 wall-clock delay 때문에 자동으로 바뀌어서는 안 된다.

따라서 data pipeline task는 가능한 한 다음처럼 생각한다.

```text
input partition
= runtime의 logical/data interval에서 결정

not
= task process가 우연히 시작된 현재 시각에서 결정
```

## 9. retry와 data interval의 관계

같은 TaskInstance가 retry된다고 하자.

```text
DagRun: [08-27, 08-28)

try 1
  actual execution: 08-28 00:03
  failed

try 2
  actual execution: 08-28 00:18
  success
```

두 try는 wall-clock time이 다르지만 같은 logical work를 재시도한다.

따라서 다음 코드는 위험하다.

```python
partition = datetime.now().date()
```

retry가 날짜 경계를 넘으면 같은 TaskInstance가 다른 partition을 건드릴 수 있다.

다음 chapter에서 이 문제가 idempotence와 어떻게 연결되는지 실제 failure lab으로 확인한다.

## 10. catchup은 무엇을 자동 생성할지 결정한다

오래전에 시작했어야 하는 Dag를 오늘 처음 활성화했다고 하자.

```text
start_date                                  now
    |                                        |
    v                                        v
----+----+----+----+----+----+----+----+----+
    historical scheduling intervals
```

`catchup=True`면 scheduler가 정상 schedule의 연장선에서 과거 interval의 DagRun을 생성할 수 있다.

`catchup=False`면 일반적으로 최신 scheduling point부터 운영하고 과거 interval을 자동으로 모두 따라잡지 않는다.

여기서 중요한 오해를 제거한다.

```text
catchup=False
!=
과거 데이터를 다시 처리할 수 없음
```

자동 scheduling policy와 명시적인 historical reprocessing은 다른 기능이다.

## 11. backfill은 historical range를 의도적으로 다시 계산한다

Airflow 3.3 CLI에는 explicit backfill command가 있다.

먼저 실제 run을 만들지 않는 dry run으로 scheduling 결과를 관찰한다.

```bash
bash lab/airflow.sh backfill create \
  --dag-id adudeck_observable_schedule \
  --from-date '2026-08-28T00:00:00+00:00' \
  --to-date '2026-08-28T00:04:00+00:00' \
  --max-active-runs 1 \
  --dry-run
```

### 실행 전에 예측한다

명령을 실행하기 전에 다음을 적는다.

- 어떤 logical dates가 대상이 될 것으로 예상하는가?
- 각 run의 data interval은 무엇인가?
- `catchup=False`인데 dry-run 결과가 나올 수 있다고 예상하는가?

그 다음 실제 dry-run 결과와 비교한다.

### 실제 backfill을 실행한다

local lab에서만 다음처럼 `--dry-run`을 제거한다.

```bash
bash lab/airflow.sh backfill create \
  --dag-id adudeck_observable_schedule \
  --from-date '2026-08-28T00:00:00+00:00' \
  --to-date '2026-08-28T00:04:00+00:00' \
  --max-active-runs 1
```

`max-active-runs=1`은 correctness requirement가 아니라 **여러 historical run이 순차적으로 보이게 해서 관찰하기 쉽게 만드는 실험
조건**이다.

다시 run list를 본다.

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_schedule -o table
```

normal scheduled run과 backfill run의 `run_id`, logical date, state를 비교한다.

metadata probe와 `lab/output/schedule-*.json`도 함께 본다.

## 12. catchup과 backfill을 관측 가능한 차이로 설명한다

둘 다 과거 interval과 관련되므로 이름만 외우면 자주 섞인다.

| 질문 | catchup | backfill |
| --- | --- | --- |
| 누가 시작하는가 | 정상 scheduler policy | 사용자의 명시적 historical operation |
| 무엇을 결정하는가 | 미생성 과거 interval을 자동 생성할지 | 지정한 과거 range를 재처리할지 |
| `catchup=False`와 공존 가능한가 | 자동 catchup은 안 함 | 가능 |
| 관측 evidence | scheduled DagRun 생성 패턴 | backfill run / backfill operation |

실습에서 `catchup=False`인 Dag를 explicit backfill할 수 있다는 사실을 직접 확인하면 둘의 boundary가 훨씬 선명해진다.

## 13. Scheduling debugging 절차

"왜 이 task가 지금 실행됐지?" 또는 "왜 아직 안 돌지?"를 만나면 다음 순서로 본다.

### Step 1. timetable output을 계산한다

```bash
bash lab/airflow.sh dags next-execution adudeck_observable_schedule --table
```

### Step 2. 필요한 DagRun이 실제로 있는지 본다

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_schedule -o table
```

### Step 3. DagRun의 interval과 state를 본다

UI와 metadata probe를 사용한다.

### Step 4. TaskInstance state를 분리해서 본다

DagRun이 존재한다고 task가 즉시 실행되는 것은 아니다. dependency와 execution condition을 따로 확인한다.

### Step 5. wall-clock delay와 logical data를 다시 분리한다

늦게 실행되었다는 사실만 보고 "잘못된 날짜 run"이라고 판단하지 않는다.

## Practice

### 1. Interval prediction

현재 시각과 무관하게 다음 timetable을 그린다.

```text
schedule: */2 * * * *
```

`10:00`, `10:02`, `10:04`, `10:06` 경계를 표시하고 각 scheduled run의 data interval을 적는다.

### 2. Cross-view timestamp audit

실제 한 run을 골라 다음을 채운다.

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

### 3. Retry thought experiment

08-27 partition을 처리하는 TaskInstance가 08-29에 retry되었다.

- `datetime.now()`를 partition key로 사용하면 어떤 문제가 생기는가?
- data interval을 사용하면 어떤 invariant를 유지할 수 있는가?

### 4. Catchup vs backfill

다음 요구를 각각 어느 기능으로 모델링할지 결정하고 이유를 설명한다.

1. 새 Dag를 활성화했더니 지난 7일의 정상 schedule도 모두 처리해야 한다.
2. 지난달 3일치 transform bug를 수정했으므로 그 range만 다시 계산해야 한다.
3. 신규 table을 과거 1년치로 채워야 한다.

### 5. Evidence before explanation

실제 lab에서 예상과 다른 run이 생겼다면 바로 원인을 추측하지 않는다.

다음 evidence를 먼저 모은 뒤 설명을 작성한다.

```text
next-execution output
list-runs output
metadata dag_run row
task log interval marker
output JSON
```

## Checkpoint

다음을 자신의 말로 설명할 수 있으면 통과한다.

> Airflow schedule은 단순 wall-clock alarm이 아니다. DagRun은 logical/data interval을 갖고 scheduler는 timetable에 따라 run을
> 만든다. 실제 task 실행 시각은 늦어질 수 있지만 logical work는 유지되어야 하며, catchup과 backfill은 과거 interval을 다루는
> 서로 다른 mechanism이다.

## References

- [Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
- [Dag Run](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html)
- [CLI Reference — next-execution / backfill](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
- [FAQ — start_date and data interval](https://airflow.apache.org/docs/apache-airflow/stable/faq.html)
