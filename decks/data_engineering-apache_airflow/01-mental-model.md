# 01. Mental model: 정의와 실행을 분리해서 보기

Airflow를 처음 배울 때 가장 흔한 혼란은 Python 코드, DAG graph, 실제 실행 기록을 하나의 대상으로 보는 데서 시작한다.

핵심은 **정의(definition)와 실행(runtime state)을 분리하는 것**이다.

Airflow의 DAG 파일은 "이 작업을 지금 실행하라"는 script가 아니다. DAG 파일은 반복해서 실행할 workflow의 구조를 선언한다. 실제 실행이 발생하면 Airflow는 그 정의를 바탕으로 별도의 runtime object와 state를 만든다.

## 1. Airflow가 해결하는 문제

다음 batch pipeline을 생각해 보자.

```text
extract_orders -> transform_orders -> load_orders
```

세 Python 함수를 순서대로 호출하는 것만 필요하다면 일반 script로도 충분하다.

Airflow가 필요한 이유는 보통 실행 자체보다 **반복 실행의 운영 상태**가 어려워지기 때문이다.

예를 들어 다음 질문에 답해야 한다.

- 매일 한 번 실행해야 하는가?
- 어제 실행은 성공했는가?
- `transform_orders`만 실패했을 때 어디부터 다시 실행해야 하는가?
- 동시에 여러 날짜의 실행이 존재해도 되는가?
- upstream task가 실패했는데 downstream task를 실행해도 되는가?
- worker가 죽었을 때 task는 어떤 상태로 남는가?

Airflow는 이런 질문을 다루는 orchestrator다. 데이터 변환 자체를 대신 수행하기보다 **어떤 작업이 언제 실행 가능한지 판단하고, 실행 결과의 state를 기록하며, 다음 작업을 진행할지 결정한다.**

## 2. 네 가지 object를 먼저 구분한다

Airflow의 기본 mental model은 다음 네 object에서 시작한다.

### Dag

`Dag`는 workflow의 **정의**다.

- 어떤 task가 존재하는가?
- task 사이 dependency는 무엇인가?
- 어떤 schedule을 사용하는가?
- concurrency나 retry 같은 기본 rule은 무엇인가?

Dag 자체는 "오늘 실행된 workflow"가 아니다. 여러 번 실행될 수 있는 구조다.

### DagRun

`DagRun`은 한 Dag의 **한 번의 실행 instance**다.

예를 들어 `daily_orders` Dag가 매일 실행된다면 다음과 같이 여러 DagRun이 존재할 수 있다.

```text
Dag: daily_orders
├── DagRun for 2026-08-25 interval
├── DagRun for 2026-08-26 interval
└── DagRun for 2026-08-27 interval
```

각 DagRun은 서로 다른 state를 가진다. 26일 run은 성공했고 27일 run은 실패할 수 있다.

### Task

`Task`는 Dag 안에 정의된 **작업 단위의 template**다.

`extract_orders`, `transform_orders`, `load_orders`가 각각 Task가 될 수 있다.

### TaskInstance

`TaskInstance`는 특정 DagRun 안에서 특정 Task가 실제로 실행되는 **runtime instance**다.

즉 다음 조합으로 생각할 수 있다.

```text
TaskInstance ≈ DagRun + Task
```

`transform_orders`라는 Task가 하나 있어도 날짜별 DagRun마다 서로 다른 TaskInstance가 생긴다.

이 구분은 debugging에서 매우 중요하다. "transform task가 실패했다"보다 정확한 표현은 "2026-08-27 DagRun의 transform_orders TaskInstance가 실패했다"다.

## 3. 정의에서 실행까지 어떤 component가 움직이는가

Airflow 3의 기본 architecture를 단순화하면 다음 흐름으로 볼 수 있다.

```text
Dag file / Dag bundle
        |
        v
+----------------+
| Dag Processor  |
+----------------+
        |
        | parse + serialize
        v
+-------------------+
| Metadata Database |
+-------------------+
        ^
        | runtime state
        |
+--------------------------------+
| Scheduler                      |
|  executor -> execution backend |
+--------------------------------+
                 |
                 v
              Worker
                 |
                 v
            user task code
```

Airflow 3에서 executor는 별도의 daemon service라기보다 **scheduler가 사용하는 execution abstraction/configuration**이다. 기본 architecture 문서에서도 executor는 scheduler의 configuration property이며 scheduler process 안에서 동작한다고 설명한다.

실제 architecture에는 API Server, Task SDK, optional triggerer 등 더 많은 component가 있지만, 처음에는 **누가 어떤 state를 읽고 바꾸는지**가 중요하다.

### Dag Processor

Dag Processor는 Dag bundle의 Dag 파일을 읽고 parsing한다.

Python 파일에 Dag를 정의했다고 해서 scheduler가 매번 그 Python 파일을 직접 실행하며 판단하는 식으로 생각하면 안 된다. Airflow 3에서는 Dag Processor가 definition을 parsing하고 serialized representation을 metadata database에 저장한다.

따라서 DAG file이 syntax error 때문에 parsing되지 않으면 runtime 단계로 넘어가기 전에 이미 문제가 발생한 것이다.

### Metadata Database

metadata database는 Airflow의 runtime state를 이해할 때 중심에 둬야 한다.

여기에 Dag, DagRun, TaskInstance 등 scheduler가 판단하는 데 필요한 상태가 기록된다.

중요한 mental model은 다음이다.

> Airflow는 단순히 Python process들이 서로 직접 명령을 전달하는 시스템이 아니라, 여러 component가 공유된 workflow state를 읽고 갱신하면서 진행되는 system이다.

### Scheduler

scheduler의 핵심 질문은 다음과 같다.

```text
지금 실행 가능한 TaskInstance는 무엇인가?
```

이를 판단하려면 scheduler는 적어도 다음을 확인해야 한다.

- 실행 대상 DagRun이 존재하는가?
- upstream dependency가 충족되었는가?
- TaskInstance가 이미 성공하거나 실행 중이지 않은가?
- concurrency/pool 같은 제한을 통과하는가?

조건을 통과한 TaskInstance는 configured executor를 통해 실행 대상으로 전달된다.

### Executor와 Worker

executor는 "어디에서 어떤 방식으로 task를 실행할 것인가"에 관여한다.

개념적으로 scheduler가 **무엇을 실행할지** 결정한다면 executor는 scheduler 안에서 **그 실행을 어떤 execution backend에 제출할지** 담당한다고 볼 수 있다.

실제 user code는 worker 쪽에서 실행된다. deployment 방식에 따라 worker는 같은 machine의 process일 수도 있고, 별도의 Celery worker나 Kubernetes Pod일 수도 있다.

### API Server

Airflow 3의 API Server는 UI와 REST API를 제공한다. Task SDK를 사용하는 task가 Airflow와 runtime state를 주고받는 경로에도 관여한다.

처음에는 "web UI component"로만 외우기보다, **사람과 task runtime이 Airflow control plane을 관찰하거나 상호작용하는 API surface**라고 이해하는 편이 낫다.

## 4. 하나의 DagRun을 끝까지 추적해 보자

다음 Dag를 생각하자.

```python
import pendulum
from airflow.sdk import dag, task


@dag(
    schedule="@daily",
    start_date=pendulum.datetime(2026, 8, 1, tz="UTC"),
    catchup=False,
)
def daily_orders():
    @task
    def extract_orders():
        return {"object_key": "orders/2026-08-28.json"}

    @task
    def transform_orders(source):
        return {"object_key": "orders/2026-08-28.parquet"}

    @task
    def load_orders(source):
        print(f"load {source}")

    raw = extract_orders()
    transformed = transform_orders(raw)
    load_orders(transformed)


daily_orders()
```

이 코드를 "위에서 아래로 한 번 실행되는 ETL script"로 보면 Airflow의 동작을 잘못 이해하게 된다.

실제로는 다음 단계로 나눠서 생각해야 한다.

### 단계 1: Dag definition을 만든다

Dag Processor가 파일을 parsing하면 `daily_orders` Dag와 세 Task의 dependency가 definition으로 등록된다.

```text
extract_orders -> transform_orders -> load_orders
```

이 시점에는 특정 날짜의 task execution이 성공한 것도 실패한 것도 아니다.

### 단계 2: DagRun이 만들어진다

schedule 조건을 만족하면 scheduler는 해당 Dag에 대한 DagRun을 만든다.

이 DagRun은 한 번의 workflow execution을 대표한다.

### 단계 3: TaskInstance를 평가한다

DagRun 안에서 각 Task에 대응하는 TaskInstance가 runtime state를 가진다.

처음에는 `extract_orders`의 dependency가 없으므로 실행 가능하지만 `transform_orders`와 `load_orders`는 upstream 완료를 기다려야 한다.

### 단계 4: scheduler가 실행 가능성을 판단한다

scheduler가 `extract_orders` TaskInstance를 runnable하다고 판단하면 executor를 통해 실행 backend에 제출한다.

worker가 user code를 실행하고 성공하면 해당 TaskInstance state가 성공으로 바뀐다.

### 단계 5: state 변화가 다음 task를 unlock한다

다음 scheduler cycle에서 `transform_orders`의 upstream dependency가 충족된 것을 확인할 수 있다.

따라서 `transform_orders`가 실행 가능해진다.

같은 과정이 `load_orders`까지 이어진다.

### 단계 6: DagRun이 완료된다

필요한 TaskInstance들이 terminal state에 도달하면 DagRun 자체도 성공 또는 실패 같은 결과 state를 갖게 된다.

이 흐름에서 중요한 점은 **dependency graph가 직접 task를 호출하는 것이 아니라, scheduler가 runtime state를 반복해서 평가하며 다음 실행을 가능하게 만든다**는 것이다.

## 5. control flow와 data flow를 섞지 않는다

Task dependency는 기본적으로 control flow를 표현한다.

```text
A >> B
```

이 관계가 의미하는 핵심은 "A의 조건이 충족되어야 B가 실행 가능하다"는 것이다.

반면 A가 만든 큰 dataframe이나 file을 B에 전달하는 것은 data flow 문제다.

두 개념을 섞으면 다음과 같은 잘못된 설계가 나오기 쉽다.

```text
Task A가 2GB dataframe 생성
        |
        | XCom으로 전달
        v
Task B가 dataframe 사용
```

Airflow의 XCom은 task 간 작은 metadata를 전달하는 데 적합하다. 큰 data payload는 object storage, database, warehouse 같은 external system에 저장하고 Task 간에는 location이나 identifier를 넘기는 편이 일반적으로 안전하다.

예를 들어 다음과 같이 나눈다.

```text
Task A
  writes -> s3://bucket/orders/2026-08-28.parquet
  returns -> object key

Task B
  receives -> object key
  reads -> object storage
```

이렇게 하면 orchestration state와 실제 data storage responsibility가 분리된다.

## 6. 흔한 잘못된 mental model

### "DAG는 실행 중인 pipeline이다"

아니다. Dag는 반복 실행될 workflow definition이고, 실제 한 번의 실행은 DagRun이다.

### "Task가 실패했다"

운영에서는 어떤 DagRun의 어떤 TaskInstance인지까지 봐야 한다.

### "scheduler가 task code를 직접 실행한다"

scheduler의 핵심 책임은 실행 가능성을 판단하고 executor를 통해 execution backend에 제출하는 것이다. 실제 user task code 실행은 worker execution context에서 일어난다.

### "dependency arrow는 data가 이동한다는 뜻이다"

arrow의 일차적 의미는 execution dependency다. data 전달 방식은 별도로 설계해야 한다.

### "Airflow가 data processing engine이다"

Airflow는 Spark나 database engine처럼 data를 처리하는 engine이 아니다. 외부 compute나 Python code를 orchestration한다.

## 7. Debugging checkpoint

문제가 생겼을 때 다음 순서로 layer를 나누면 원인을 빨리 좁힐 수 있다.

```text
1. Definition layer
   Dag file이 정상 parsing되었는가?

2. DagRun layer
   실행해야 할 DagRun이 실제로 존재하는가?

3. Dependency layer
   해당 TaskInstance의 upstream 조건이 충족되었는가?

4. Scheduling layer
   scheduler가 runnable하다고 판단할 수 있는 상태인가?

5. Execution layer
   executor/worker가 task를 실제로 시작했는가?

6. User-code layer
   task code 자체가 성공했는가?
```

UI에서 "안 돌아간다"고 보이는 현상도 실제로는 이 여섯 layer 중 전혀 다른 곳의 문제일 수 있다.

## Practice

정답을 바로 보지 말고 state를 직접 그려 본다.

### 1. Object 구분

`daily_orders` Dag가 8월 27일과 8월 28일 두 번 실행되었고 각 DagRun에 세 Task가 있다고 하자.

다음을 각각 몇 개라고 봐야 하는가?

- Dag
- DagRun
- Task definition
- TaskInstance

### 2. State tracing

다음 dependency가 있다.

```text
A -> B -> C
```

현재 한 DagRun에서 A=`success`, B=`failed`, C=`none`이라고 하자.

- C가 아직 실행되지 않은 이유를 runtime object 기준으로 설명한다.
- B를 retry해서 성공하면 scheduler의 다음 판단에서 무엇이 달라지는지 설명한다.

### 3. Layer debugging

새 Dag 파일을 배포했는데 UI에 Dag 자체가 나타나지 않는다.

worker log부터 확인하는 것이 왜 좋은 첫 단계가 아닐 수 있는지 설명한다.

### 4. Control vs data

Task A가 5GB parquet dataset을 만들고 Task B가 이를 읽어야 한다.

- dependency는 어떻게 표현할 것인가?
- 실제 dataset은 어디에 둘 것인가?
- Task 간에 전달할 최소 metadata는 무엇인가?

## Checkpoint

다음 문장을 자신의 말로 설명할 수 있으면 이 chapter의 목표를 달성한 것이다.

> Airflow는 Dag definition을 직접 순차 실행하는 script runner가 아니라, DagRun과 TaskInstance의 state를 관리하면서 dependency를 만족한 작업을 scheduler가 실행 대상으로 결정하는 orchestrator다.

## References

- [Architecture Overview](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [Core Concepts](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/)
- [Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
