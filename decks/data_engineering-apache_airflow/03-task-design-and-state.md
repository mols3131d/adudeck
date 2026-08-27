# 03. Task design: 재실행 가능한 작업과 data 경계 만들기

Airflow에서 DAG graph가 예쁘게 보인다고 해서 workflow가 운영하기 좋은 것은 아니다.

실제 안정성은 **Task를 어떤 경계로 나누고, 각 Task가 어떤 state와 side effect를 갖게 만드는가**에서 크게 결정된다.

이 chapter의 핵심 질문은 두 가지다.

1. 이 Task를 같은 DagRun에서 다시 실행해도 안전한가?
2. Task 사이에 실제 data를 어떻게 연결할 것인가?

## 1. Task는 함수 분할 단위가 아니라 운영 단위다

일반 Python code에서는 긴 함수를 readability 때문에 여러 함수로 쪼갤 수 있다.

Airflow Task를 나누는 기준은 조금 다르다. Task 경계는 runtime에서 별도의 state와 retry 경계가 된다.

다음 pipeline을 보자.

```text
extract -> transform -> load
```

각 단계를 Task로 나누면 다음이 가능해진다.

- extract만 retry
- transform failure를 별도로 관찰
- load가 성공하기 전에는 DagRun을 완료하지 않음
- 단계별 duration과 log 확인

반대로 모든 일을 하나의 Task에 넣으면 Airflow가 볼 수 있는 state도 하나뿐이다.

```text
one_big_task
  ├─ extract
  ├─ transform
  └─ load
```

`load`에서 실패해도 retry할 때 extract부터 다시 수행해야 할 수 있다.

하지만 Task를 아주 작게 쪼개는 것도 항상 좋은 것은 아니다. local Python function call이면 충분한 작업까지 모두 Task로 만들면 scheduling overhead와 graph complexity가 늘어난다.

좋은 Task 경계는 대체로 다음 특징을 가진다.

- 독립적으로 성공/실패를 판단할 의미가 있다.
- 독립 retry가 가치가 있다.
- input/output contract를 설명할 수 있다.
- 외부 system에 대한 side effect의 책임이 명확하다.

## 2. TaskInstance state는 실행 lifecycle을 나타낸다

TaskInstance는 단순히 `success`와 `failed`만 갖지 않는다.

개념적으로 자주 보게 되는 lifecycle을 단순화하면 다음과 같다.

```text
None
  |
  v
scheduled
  |
  v
queued
  |
  v
running
  | \
  |  \
  v   v
success failed
          |
          v
     up_for_retry
          |
          +----> scheduled ...
```

실제 Airflow에는 `skipped`, `upstream_failed`, `deferred`, `up_for_reschedule` 등 더 많은 state가 있다.

중요한 것은 state 이름을 전부 암기하는 것이 아니라 **어느 component와 조건 때문에 다음 state로 이동했는지 추적하는 것**이다.

예를 들어 `queued`에서 오래 머무는 문제와 `running` 후 실패하는 문제는 전혀 다른 layer를 의심해야 한다.

- `queued`에서 정체: executor/worker capacity, queue, pool 등 실행 resource 쪽을 검토
- `running -> failed`: user code, external dependency, timeout 등 실제 execution을 검토
- `upstream_failed`: 해당 Task 자체보다 upstream failure부터 검토

## 3. Retry가 존재하면 idempotence를 먼저 생각한다

Airflow Task는 실패할 수 있고 retry될 수 있다.

따라서 Task code는 가능한 한 같은 logical input으로 여러 번 실행되어도 결과가 망가지지 않는 성질이 필요하다.

이 성질을 **idempotence**라고 부른다.

완전히 수학적인 idempotence를 항상 만들 수 있는 것은 아니지만, data pipeline에서는 다음 질문이 유용하다.

> 같은 DagRun의 같은 TaskInstance가 다시 실행되면 external system에 어떤 side effect가 반복되는가?

### 위험한 예: 무조건 append

```python
def load_orders(rows):
    warehouse.insert(rows)
```

첫 시도에서 insert는 성공했지만 process가 success state를 기록하기 전에 죽었다고 하자.

retry가 다시 같은 rows를 append하면 duplicate가 생길 수 있다.

### 더 안전한 방향: logical partition을 기준으로 replace/upsert

```text
DagRun interval -> partition dt=2026-08-27

retry 1: write dt=2026-08-27
retry 2: replace/upsert dt=2026-08-27
```

구현 방식은 warehouse에 따라 달라지지만 원칙은 같다.

**wall-clock execution time이 아니라 DagRun의 logical input을 side-effect key로 사용한다.**

## 4. Task input과 output을 contract로 본다

Task 사이를 다음처럼 생각하면 설계가 쉬워진다.

```text
Task A
  input contract
  operation
  output contract
       |
       v
Task B
```

예를 들어 extract Task의 contract를 다음처럼 잡을 수 있다.

```text
input
- data_interval_start
- data_interval_end

side effect
- object storage에 parquet file 생성

output metadata
- bucket
- object key
- row count
```

transform Task는 이 metadata를 받아 실제 object storage에서 data를 읽는다.

이 방식은 "Python object를 Task 사이에서 그대로 전달한다"보다 distributed execution 환경에 잘 맞는다.

Airflow는 여러 Task가 같은 worker나 같은 process에서 실행된다고 보장하지 않기 때문이다.

## 5. XCom은 orchestration metadata에 가깝게 사용한다

TaskFlow에서는 함수 return value를 다음 task argument로 넘기는 문법이 자연스럽다.

```python
@task
def extract():
    return {"object_key": "raw/orders/2026-08-27.parquet"}


@task
def transform(source):
    ...


raw = extract()
transform(raw)
```

코드만 보면 일반 Python function call처럼 보이지만 runtime에서 Task 간 값 전달은 XCom을 사용한다.

여기서 중요한 boundary가 있다.

XCom에는 작은 metadata를 전달하고, 큰 dataset은 external storage에 둔다.

좋은 예:

```json
{
  "bucket": "analytics-raw",
  "object_key": "orders/dt=2026-08-27/data.parquet",
  "row_count": 182341
}
```

좋지 않은 기본 방향:

```text
2GB dataframe 자체를 XCom으로 전달
```

Airflow documentation도 XCom을 작은 metadata 전달에 사용하는 형태와 큰 file을 storage service를 통해 주고받는 형태를 구분한다.

## 6. control dependency와 data dependency를 함께 설계한다

다음 TaskFlow code를 보자.

```python
raw = extract_orders()
clean = transform_orders(raw)
load_orders(clean)
```

여기에는 두 종류의 관계가 함께 있다.

### Control dependency

`extract_orders`가 성공한 뒤 `transform_orders`가 실행되어야 한다.

### Data dependency

`transform_orders`는 extract가 생성한 object location을 알아야 한다.

TaskFlow 문법은 두 관계를 자연스럽게 연결해 주지만 conceptual boundary는 유지해야 한다.

큰 data 자체는 external storage에 있고, XCom에는 그 data를 찾는 identifier가 있다는 식으로 생각한다.

```text
              control dependency
Task A ------------------------------> Task B
  |                                      |
  | write                                | read
  v                                      v
       external object storage
  ^                                      ^
  |                                      |
  +--- object key via XCom --------------+
```

## 7. 실패를 고려한 작은 ETL을 설계해 보자

요구사항이 다음과 같다고 하자.

> 하루치 주문을 API에서 가져와 object storage에 저장하고, 정제한 뒤 warehouse partition으로 load한다.

### Task 1: extract_orders

책임:

- 해당 data interval의 API data를 가져온다.
- raw object를 deterministic path에 저장한다.
- object key와 row count를 반환한다.

예시 path:

```text
raw/orders/dt=2026-08-27/orders.parquet
```

retry 시 같은 path를 overwrite할 수 있도록 설계하면 duplicate raw object가 무한히 생기는 것을 막기 쉽다.

### Task 2: transform_orders

책임:

- raw object key를 input으로 받는다.
- schema validation과 transform을 수행한다.
- curated object를 deterministic path에 저장한다.

```text
curated/orders/dt=2026-08-27/orders.parquet
```

### Task 3: load_orders

책임:

- curated object를 읽는다.
- warehouse의 `dt=2026-08-27` partition을 replace 또는 idempotent upsert한다.
- 성공 시 load result metadata를 남긴다.

이렇게 나누면 각 Task의 retry와 side effect를 따로 reasoning할 수 있다.

## 8. Retry하면 안 되는 failure도 있다

모든 실패에 retry를 많이 주는 것은 좋은 운영이 아니다.

### Retry 가치가 있는 failure

- 일시적인 network timeout
- external API의 temporary 5xx
- transient connection failure

### Retry로 해결되지 않을 가능성이 큰 failure

- schema mismatch
- 잘못된 SQL syntax
- required configuration 누락
- deterministic code bug

두 번째 종류에 retry를 20번 줘도 같은 error를 20번 반복할 가능성이 높다.

따라서 retry policy는 "실패하면 다시"가 아니라 **이 failure가 시간 경과나 재시도로 회복될 수 있는가**를 기준으로 잡아야 한다.

Airflow 3.3에는 기본 retry count뿐 아니라 pluggable retry policy도 도입되어 있지만, 처음에는 이 판단 기준을 먼저 익히는 것이 중요하다.

## 9. 상태로 debugging 범위를 좁힌다

workflow가 진행되지 않을 때 TaskInstance state를 먼저 본다.

### Case A: downstream이 `upstream_failed`

먼저 downstream code를 볼 이유가 적다.

```text
extract: success
transform: failed
load: upstream_failed
```

`load`가 실행되지 않은 원인은 `load` code failure가 아니라 upstream condition이다.

### Case B: task가 `up_for_retry`

현재 실패가 terminal failure가 아니다.

확인할 것은 다음과 같다.

- 어떤 exception이 발생했는가?
- retry 대상이 맞는 failure인가?
- retry delay 후 같은 side effect를 반복해도 안전한가?

### Case C: task가 오래 `queued`

user function이 아직 시작하지 않았을 수 있다.

확인 범위는 worker capacity, executor queue, pool/concurrency 등 execution infrastructure 쪽이다.

### Case D: task가 `running` 후 `failed`

이제 실제 task log와 external system response가 핵심 증거다.

이처럼 state는 단순한 UI badge가 아니라 **debugging search space를 줄이는 signal**이다.

## 10. Task를 나눌 때 사용할 checklist

새 workflow를 만들 때 각 Task 후보에 다음을 묻는다.

1. 이 작업의 logical input은 무엇인가?
2. external side effect는 무엇인가?
3. output은 data 자체인가, data location을 가리키는 metadata인가?
4. 같은 input으로 retry하면 안전한가?
5. 실패했을 때 이 단계만 다시 실행할 가치가 있는가?
6. 이 단계의 성공/실패를 독립적으로 관찰할 가치가 있는가?
7. upstream/downstream dependency가 business requirement를 실제로 표현하는가?

답이 불명확하면 Python code부터 작성하기보다 Task boundary를 다시 생각하는 편이 낫다.

## 11. Worked example: duplicate가 생기는 load 고치기

현재 load Task가 다음 방식이라고 하자.

```text
1. transform 결과를 읽는다.
2. warehouse table에 INSERT한다.
3. success 처리 전에 worker가 죽을 수 있다.
4. retry하면 같은 rows를 다시 INSERT한다.
```

문제는 Airflow retry 자체가 아니다. Task side effect가 retry-safe하지 않다는 데 있다.

수정 전략을 단계별로 생각한다.

### Step 1. logical key를 정한다

DagRun의 data interval에서 partition key를 만든다.

```text
dt=2026-08-27
```

### Step 2. load semantics를 명시한다

예:

```text
"이 Task가 성공하면 dt=2026-08-27 partition은 source snapshot과 동일해야 한다."
```

이 문장이 invariant가 된다.

### Step 3. implementation을 invariant에 맞춘다

warehouse capability에 따라 다음 중 하나를 선택할 수 있다.

- partition overwrite
- staging table + atomic swap
- deterministic key 기반 MERGE/upsert

### Step 4. retry를 다시 평가한다

이제 같은 TaskInstance를 여러 번 실행해도 최종 partition이 같은 logical state로 수렴하는지 확인한다.

이것이 단순히 `retries=3`을 추가하는 것보다 중요한 reliability 설계다.

## Practice

### 1. Task boundary 비교

다음 두 설계를 비교한다.

```text
A. one_task: extract + transform + load

B. extract -> transform -> load
```

다음 관점에서 각각 장단점을 설명한다.

- retry cost
- observability
- data transfer
- scheduling overhead
- failure isolation

### 2. Idempotence debugging

load Task가 retry될 때 duplicate row가 생긴다.

Airflow 설정만 바꾸는 해결책과 Task side-effect semantics를 바꾸는 해결책을 구분하고, 왜 후자가 더 근본적인지 설명한다.

### 3. XCom 판단

다음 값 중 XCom으로 전달하기 적합한 것과 external storage에 두는 것이 적합한 것을 나눈다.

- S3 object key 문자열
- row count 정수
- 4GB parquet file bytes
- warehouse table name
- 500MB pandas DataFrame
- validation result `{passed: true, invalid_rows: 3}`

### 4. State-based diagnosis

다음 세 상황에서 가장 먼저 볼 layer를 적는다.

1. Task가 `queued`에서 40분 동안 움직이지 않는다.
2. Task가 `running` 직후 Python exception으로 실패한다.
3. downstream Task가 `upstream_failed`다.

### 5. Transfer

자신이 운영한다고 가정한 data pipeline 하나를 골라 다음 형식으로 세 Task를 설계한다.

```text
Task name:
Logical input:
External side effect:
Output metadata:
Retry-safe invariant:
Downstream dependency:
```

## Checkpoint

다음을 설명할 수 있으면 core foundation을 한 번 통과한 것이다.

> Airflow의 reliability는 retry 횟수를 늘리는 데서 생기는 것이 아니라, Task를 독립적인 runtime state와 side-effect boundary로 설계하고 같은 logical input의 재실행이 안전하도록 만드는 데서 시작한다.

## References

- [Architecture Overview — Workloads and Control Flow](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [Tasks](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html)
- [XComs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html)
- [Airflow 3.3 Release Notes](https://airflow.apache.org/docs/apache-airflow/stable/release_notes.html)
