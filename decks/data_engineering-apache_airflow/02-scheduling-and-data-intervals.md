# 02. Scheduling: data interval을 기준으로 시간 이해하기

Airflow scheduling에서 가장 자주 생기는 오해는 `schedule="@daily"`를 "매일 00:00에 그날의 일을 시작한다"라고만 해석하는
것이다.

Airflow의 scheduled workflow는 보통 **처리 대상이 되는 시간 구간(data interval)**을 먼저 생각해야 한다. scheduler는 특정
interval이 끝난 뒤 그 interval을 처리하는 DagRun을 만들 수 있다.

이 mental model을 잡지 않으면 `start_date`, logical date, catchup, backfill이 각각 따로 외워야 하는 옵션처럼 보인다.

## 1. 먼저 business time과 execution time을 분리한다

매일 전날 주문 데이터를 집계한다고 하자.

```text
2026-08-27 00:00 ---------------- 2026-08-28 00:00
             data interval
```

이 interval의 데이터는 8월 27일 하루 동안 계속 들어올 수 있다. 따라서 8월 27일 전체를 처리하는 scheduled run은
일반적으로 interval이 끝난 **8월 28일 00:00 이후**에 실행 가능해진다.

중요한 점은 다음 두 시간을 구분하는 것이다.

- **data time**: 이 run이 담당하는 데이터의 시간 범위
- **wall-clock execution time**: scheduler가 실제로 run을 만들고 task가 실행되는 현실 시간

둘은 같지 않다.

실행이 queue나 retry 때문에 8월 28일 00:10에 시작되더라도 이 DagRun이 담당하는 data interval은 여전히 8월 27일 하루일 수
있다.

## 2. schedule은 반복되는 interval을 만든다

간단한 daily Dag를 보자.

```python
import pendulum
from airflow.sdk import dag, task


@dag(
    schedule="@daily",
    start_date=pendulum.datetime(2026, 8, 25, tz="UTC"),
    catchup=True,
)
def aggregate_orders():
    @task
    def aggregate():
        ...

    aggregate()


aggregate_orders()
```

개념적으로는 다음과 같은 interval들이 생긴다.

```text
[08-25 00:00, 08-26 00:00)
[08-26 00:00, 08-27 00:00)
[08-27 00:00, 08-28 00:00)
...
```

각 interval은 하나의 scheduled DagRun과 연결될 수 있다.

여기서 `start_date`는 "8월 25일 00:00에 task process를 시작하라"는 명령이 아니다. scheduling timetable이 계산할 수 있는
첫 data interval의 기준점으로 이해하는 편이 정확하다.

## 3. 왜 첫 run이 start_date보다 늦게 보이는가

`start_date=2026-08-25 00:00`, `schedule="@daily"`라면 첫 interval은 대략 다음과 같다.

```text
start_date
    |
    v
08-25 00:00 ---------------- 08-26 00:00
          first interval
                                  |
                                  v
                         interval complete
                         -> scheduled run eligible
```

따라서 첫 scheduled run은 8월 25일 00:00에 즉시 실행되는 것이 아니라, 해당 daily interval이 끝난 뒤 만들어진다.

이 동작을 모르고 보면 Airflow가 "하루 늦게 실행된다"고 느끼기 쉽다. 실제로는 **완료된 시간 구간을 처리한다**는 모델에
가깝다.

## 4. DagRun의 시간은 partition key처럼 생각할 수 있다

batch pipeline에서는 DagRun을 단순히 "실행 번호"로 보기보다 **어떤 data partition을 담당하는 실행인지 식별하는 key**로
생각하면 편하다.

예를 들어 날짜별 partition을 만드는 pipeline이 있다고 하자.

```text
DagRun interval                    output
----------------------------------------------------------------
[2026-08-25, 2026-08-26)  ->  warehouse.orders/dt=2026-08-25
[2026-08-26, 2026-08-27)  ->  warehouse.orders/dt=2026-08-26
[2026-08-27, 2026-08-28)  ->  warehouse.orders/dt=2026-08-27
```

이런 설계에서는 task가 `datetime.now()`를 기준으로 output path를 결정하면 위험하다.

8월 27일 partition을 처리하는 task가 장애 때문에 8월 29일에 재실행되었다고 하자. `now()`를 사용하면 잘못된 8월 29일
partition을 건드릴 수 있다.

대신 task가 **DagRun의 data interval**을 기준으로 읽고 쓰도록 만들면 retry나 delayed execution에서도 같은 logical
partition을 처리할 수 있다.

이 원칙은 idempotence와도 직접 연결된다.

## 5. catchup은 과거 interval을 자동으로 따라잡을지 결정한다

새 Dag를 오늘 처음 활성화했는데 `start_date`가 한 달 전이라면, scheduler 입장에서는 이미 끝난 interval이 많이 존재한다.

`catchup=True`라면 Airflow는 아직 실행 기록이 없는 과거 interval에 대해 scheduled DagRun을 만들 수 있다.

```text
start_date                                      now
    |                                            |
    v                                            v
----|----|----|----|----|----|----|----|----|----
     ^    ^    ^    ^    ^    ^    ^    ^
     historical intervals that may need runs
```

반면 `catchup=False`는 보통 새로 활성화한 Dag가 과거 모든 interval을 자동으로 처리하지 않고 최신 scheduling point부터
운영되도록 할 때 사용한다.

`catchup=False`를 "과거 데이터를 절대 처리할 수 없다"고 이해하면 안 된다. 자동 scheduled catchup과 의도적인 historical
reprocessing은 다른 문제다.

## 6. backfill은 의도적으로 과거 구간을 다시 처리하는 작업이다

운영 중 다음 상황이 생길 수 있다.

- source bug 때문에 8월 1일부터 8월 7일까지 잘못 처리됨
- transform logic을 수정했고 특정 historical partitions를 재계산해야 함
- 새 downstream table을 과거 데이터까지 채워야 함

이때 필요한 것은 "평소 schedule이 과거 run을 자동 생성하게 둘 것인가"가 아니라
**명시한 과거 범위를 다시 실행하는 작업**이다.

이것이 backfill을 이해하는 출발점이다.

개념적으로 다음과 같다.

```text
normal scheduled runs
                    now
                     |
... 08-20 08-21 08-22 08-23 08-24

historical repair target
     [08-01 ---- 08-07]
       ^
       explicit reprocessing range
```

catchup과 backfill은 둘 다 historical interval과 관련되지만 목적이 다르다.

- catchup: scheduler가 놓친/미생성 과거 interval을 정상 schedule의 연장선에서 생성
- backfill: 사용자가 선택한 historical range를 의도적으로 재처리

## 7. retry는 같은 logical work의 재시도다

TaskInstance가 network timeout 때문에 실패했다고 하자.

```text
DagRun: interval [08-27, 08-28)
Task: load_orders

try 1 -> failed
try 2 -> success
```

retry가 발생했다고 해서 task가 담당하는 data interval이 바뀌어서는 안 된다.

따라서 retry-safe한 task는 같은 logical input에 대해 여러 번 실행되어도 결과가 깨지지 않도록 설계하는 것이 중요하다.

예를 들어 다음 패턴이 위험하다.

```python
# 개념 예시
output_table = f"orders_{datetime.now():%Y%m%d}"
```

재시도 시점이 다음 날로 넘어가면 같은 TaskInstance가 전혀 다른 table을 건드릴 수 있다.

대신 runtime context가 제공하는 interval/partition 기준 값을 사용해야 한다.

## 8. "언제 실행되나"를 계산하는 절차

schedule 관련 문제를 만났을 때 다음 순서로 계산한다.

### 1. timetable이 만드는 interval을 그린다

예를 들어 `@daily`면 먼저 자정 경계를 표시한다.

```text
00:00        00:00        00:00
  |------------|------------|
      day A         day B
```

### 2. 이번 DagRun이 어느 interval을 담당하는지 정한다

```text
[data_interval_start, data_interval_end)
```

### 3. interval이 언제 끝나는지 본다

scheduled run은 보통 자신이 담당하는 interval이 끝나야 생성될 수 있다.

### 4. 실제 execution delay를 별도로 본다

scheduler cycle, queue, pool, worker capacity, retry 때문에 실제 시작 시각은 더 늦을 수 있다.

즉 다음 식으로 생각한다.

```text
logical data interval
        +
scheduling eligibility
        +
execution delay
        =
observed wall-clock run time
```

## 9. Worked example: "왜 28일에 27일 데이터를 처리하지?"

요구사항이 다음과 같다고 하자.

> 매일 전날 확정된 주문을 집계해서 날짜 partition에 저장한다.

Dag schedule은 `@daily`다.

8월 27일 데이터를 처리하는 run을 추적해 보자.

### Step 1. 대상 interval

```text
[2026-08-27 00:00, 2026-08-28 00:00)
```

### Step 2. output partition

```text
dt=2026-08-27
```

### Step 3. run이 실행 가능해지는 시점

8월 28일 00:00 이후다. 그 전에는 8월 27일 interval이 끝나지 않았다.

### Step 4. worker가 실제 시작한 시각

예를 들어 8월 28일 00:07일 수 있다.

### Step 5. task가 사용해야 하는 날짜

`2026-08-28`이라는 wall-clock 날짜가 아니라 DagRun이 담당하는 interval에서 계산한 `2026-08-27`이어야 한다.

이렇게 해야 같은 run을 8월 29일에 retry하거나 다시 실행해도 여전히 `dt=2026-08-27`을 처리한다.

## 10. 흔한 오해

### "start_date는 process 시작 시간이다"

아니다. scheduled interval 계산의 기준점으로 이해해야 한다.

### "@daily는 오늘 00:00에 오늘 데이터를 처리한다"

scheduled data interval 관점에서는 보통 하나의 interval이 끝난 뒤 그 interval의 run이 생성된다.

### "catchup=False면 historical data를 처리할 수 없다"

아니다. 자동 catchup을 하지 않는 것과 명시적 backfill/reprocessing은 별개다.

### "retry하면 현재 시간 기준으로 다시 계산하면 된다"

그렇게 하면 같은 logical run이 retry 시점에 따라 다른 partition을 처리할 수 있다.

## Practice

### 1. Interval 계산

다음 Dag가 있다.

```python
@dag(
    schedule="@daily",
    start_date=pendulum.datetime(2026, 8, 10, tz="UTC"),
    catchup=True,
)
```

첫 세 개의 daily data interval을 직접 적고, 각각 언제 scheduled run이 생성 가능해지는지 표시한다.

### 2. Wall clock과 data time

8월 20일 interval을 처리하는 TaskInstance가 8월 23일에 retry되었다.

- input partition은 어떤 날짜여야 하는가?
- `datetime.now()`를 partition key로 쓰면 어떤 bug가 생길 수 있는가?

### 3. Catchup 판단

다음 두 상황에서 `catchup=True/False` 중 어떤 쪽을 우선 검토할지 이유와 함께 설명한다.

1. 오늘 새로 배포한 monitoring Dag이며 과거 실행은 의미가 없다.
2. 날짜별 warehouse partition을 생성하는 Dag이며 `start_date` 이후 모든 날짜가 빠짐없이 필요하다.

### 4. Backfill 설계

8월 1~7일 transform logic에 bug가 있었다.

단순히 최신 DagRun을 다시 실행하는 것으로 충분하지 않은 이유를 설명하고, 어떤 historical range를 어떤 partition key와
연결해야 하는지 적는다.

### 5. 설명하기

다음 질문에 그림 없이 답해 본다.

> Airflow daily job이 왜 "하루 늦게 돈다"고 보일 수 있는가?

답변에는 최소한 `data interval`, `interval end`, `execution time` 세 개념이 들어가야 한다.

## Checkpoint

다음을 자신의 말로 설명할 수 있으면 다음 chapter로 넘어간다.

> scheduled DagRun의 시간은 task가 실제로 시작된 wall-clock 시각보다, 그 run이 담당하는 data interval을 먼저 기준으로
> 해석해야 한다.

## References

- [Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
- [Dag Runs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dag-run.html)
- [Backfill](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/backfill.html)
