# 01. Mental model: 정의와 실행을 분리해서 관찰하기

Airflow를 처음 배울 때 가장 위험한 오해는 DAG Python 파일, 화면에 보이는 graph, 실제 실행 중인 process와 실행 기록을
하나의 대상으로 생각하는 것이다.

이 chapter의 핵심은 **definition과 runtime state를 분리한 뒤, 실제 Airflow를 실행하면서 그 구분을 눈으로 확인하는 것**이다.
설명을 읽고 끝내지 않는다. 먼저 예측하고, 같은 실행을 UI·CLI·log·metadata·output에서 찾아 연결한다.

## 1. Airflow가 필요한 이유

다음 세 함수를 순서대로 한 번 실행하는 것이 전부라면 Airflow가 필요하지 않다.

```text
extract_orders -> transform_orders -> load_orders
```

일반 Python script가 더 단순하다.

Airflow가 다루는 문제는 반복되는 실행의 **운영 상태**다.

- 어느 날짜의 workflow를 실행해야 하는가?
- 이전 단계가 성공했는가?
- 실패한 단계만 다시 실행할 수 있는가?
- 같은 workflow의 여러 실행이 동시에 존재하면 어떻게 구분하는가?
- task가 아직 실행되지 않은 이유는 dependency 때문인가, scheduler 때문인가, execution resource 때문인가?
- 재시도했을 때 같은 data를 두 번 쓰지 않는가?

따라서 Airflow를 이해할 때 첫 질문은 "이 Python 함수가 무엇을 하는가?"만이 아니다.

> **지금 어떤 runtime object가 존재하고, 그 object의 state를 누가 읽고 바꾸고 있는가?**

이 질문을 계속 유지한다.

## 2. 네 object를 먼저 구분한다

### Dag

`Dag`는 반복해서 실행할 workflow의 **정의**다.

```text
Dag: daily_orders

extract_orders -> transform_orders -> load_orders
```

Dag에는 task와 dependency, schedule 같은 구조가 들어 있다. Dag 자체는 "오늘 실행된 pipeline"이 아니다.

### DagRun

`DagRun`은 한 Dag의 **한 번의 실행 instance**다.

```text
Dag: daily_orders
├── DagRun A
├── DagRun B
└── DagRun C
```

서로 다른 DagRun은 각각 독립적인 state와 시간 정보를 가진다.

### Task

`Task`는 Dag 안에 정의된 작업의 template이다.

`transform_orders`라는 Task definition은 하나일 수 있다.

### TaskInstance

`TaskInstance`는 특정 DagRun 안에서 특정 Task가 실제로 갖는 runtime instance다.

개념적으로는 다음처럼 생각할 수 있다.

```text
TaskInstance ≈ DagRun + Task
```

DagRun이 세 개이고 각 Dag에 Task가 세 개라면 Task definition은 세 개지만 TaskInstance는 최대 아홉 개가 된다.

운영에서 "transform task가 실패했다"는 표현은 정보가 부족하다.

```text
어느 DagRun의
어느 transform_orders TaskInstance가
어느 try에서
어떤 state로 끝났는가?
```

까지 내려가야 한다.

## 3. definition에서 runtime으로 가는 경로

Airflow 3.3의 핵심 component를 학습용으로 단순화하면 다음과 같다.

```text
Dag file / Dag bundle
        |
        | parse
        v
+----------------+
| Dag Processor  |
+----------------+
        |
        | serialized definition
        v
+-------------------+
| Metadata Database |
+-------------------+
        ^        |
        |        | DagRun / TaskInstance state
        |        v
+---------------------------+
| Scheduler                 |
|  - scheduling decision    |
|  - configured Executor    |
+---------------------------+
        |
        | execute task
        v
+---------------------------+
| Task runtime / process    |
|  - user task code         |
|  - task log               |
+---------------------------+

+---------------------------+
| API Server / UI           |
|  - inspect / operate      |
+---------------------------+
        |
        +---- reads control-plane state ----+
```

실제 deployment는 더 복잡해질 수 있지만 처음에는 **각 component가 어떤 종류의 state를 소유하거나 소비하는지**에 집중한다.

### Dag Processor: definition을 runtime이 읽을 형태로 만든다

Dag 파일은 Python code다. Dag Processor는 Dag bundle의 파일을 parsing하고 serialized Dag representation을 metadata DB에
저장한다.

따라서 file이 존재한다고 해서 Dag가 Airflow에 정상 등록된 것은 아니다.

```text
file exists
   !=
Dag parsed successfully
   !=
DagRun exists
   !=
TaskInstance executed
```

이 네 단계를 분리해서 볼 수 있어야 한다.

### Metadata Database: control-plane state의 중심

Airflow의 여러 component는 metadata DB에 기록된 state를 바탕으로 판단한다.

대표적으로 다음을 생각할 수 있다.

- 어떤 Dag와 version이 있는가
- 어떤 DagRun이 있는가
- DagRun state는 무엇인가
- 어떤 TaskInstance가 존재하는가
- TaskInstance가 `running`, `failed`, `success` 중 무엇인가
- 몇 번째 try인가

metadata DB를 application이 직접 조작해야 한다는 뜻은 아니다. 오히려 반대다. 이 deck에서는 **Airflow 내부 상태가 정말
기록된다는 사실을 관찰하기 위해 read-only로만 들여다본다.**

### Scheduler: 다음에 무엇이 실행 가능한지 판단한다

scheduler의 중심 질문은 다음과 같다.

```text
지금 어떤 TaskInstance를 실행 대상으로 제출할 수 있는가?
```

이를 판단하려면 runtime state를 본다.

- 실행 대상 DagRun이 있는가?
- upstream dependency가 충족되었는가?
- TaskInstance가 이미 terminal state인가?
- retry 대기 중인가?
- pool/concurrency 같은 제한을 통과하는가?

Airflow 3에서 executor는 별도 daemon으로 외우지 않는다. **scheduler가 실행 가능한 task를 실제 execution backend에
제출할 때 사용하는 abstraction/configuration**이다.

### Task runtime: user code가 실제 side effect를 만든다

scheduler의 state decision과 task user code의 실행은 다른 문제다.

Task가 실행되면 실제 Python code가 API를 호출하고 file을 쓰거나 warehouse query를 수행할 수 있다. 이 side effect는 Airflow
metadata state와 구분해야 한다.

```text
control-plane state             data-plane / external side effect
---------------------------     ---------------------------------
TaskInstance = success          parquet file 생성
DagRun = failed                 warehouse partition 변경
try_number = 2                  API request 전송
```

둘은 연결되어 있지만 같은 것은 아니다.

## 4. 실습 준비: 먼저 관측 장비를 만든다

Deck directory에서 Airflow standalone을 시작한다.

```bash
bash lab/airflow.sh standalone
```

Airflow 공식 CLI의 `standalone`은 local development/testing용 all-in-one 실행 방식이다. 이 lab에서는 deployment 운영을 배우는
것이 아니라, 한 machine에서 component와 state 흐름을 관찰하기 위해 사용한다.

standalone terminal은 닫지 않는다. 이후 이 terminal은 **component/task log 관측면**이 된다.

별도 terminal을 열고 Dag가 parsing되었는지 확인한다.

```bash
bash lab/airflow.sh dags list
```

다음 두 Dag를 찾는다.

```text
adudeck_observable_runtime
adudeck_observable_schedule
```

없다면 runtime 실행부터 의심하지 않는다. 먼저 definition layer를 확인한다.

```bash
bash lab/airflow.sh dags list-import-errors -o table
```

### Checkpoint: 지금 무엇을 증명했는가

`dags list`에 보인다는 것은 대략 다음을 증명한다.

```text
Dag file 존재
      ↓
Dag Processor가 parsing 가능
      ↓
Airflow가 Dag definition을 인식
```

아직 TaskInstance가 성공했다는 증거는 하나도 없다.

## 5. Observable Lab A: 하나의 DagRun을 네 관점에서 추적한다

이번에는 `adudeck_observable_runtime`을 성공하도록 실행한다.

먼저 Dag를 unpause한다.

```bash
bash lab/airflow.sh dags unpause adudeck_observable_runtime
```

실행하기 전에 graph를 보고 prediction을 적는다.

```text
prepare -> transform -> publish
```

다음을 먼저 답한다.

1. DagRun은 몇 개 새로 생길까?
2. TaskInstance는 몇 개 생길까?
3. `prepare`가 `running`일 때 `publish`는 왜 아직 실행되지 않을까?
4. user code가 실제로 만드는 file은 Airflow metadata와 같은 것일까?

### 실행

UI `http://localhost:8080`에서 `adudeck_observable_runtime`을 열고 `failure_mode=none`으로 trigger해도 된다.

CLI를 사용한다면 다음처럼 trigger할 수 있다.

```bash
bash lab/airflow.sh dags trigger \
  -c '{"failure_mode":"none"}' \
  adudeck_observable_runtime
```

lab task는 일부러 몇 초 동안 실행되도록 되어 있다. 바로 끝내기 위한 delay가 아니라 **state를 사람이 관찰할 시간을 확보하기
위한 instrumentation**이다.

## 6. 관측면 1: UI / Grid

UI에서 새 DagRun을 열고 task state가 변하는 과정을 본다.

관찰하려는 것은 단순히 "초록색이 되었다"가 아니다.

```text
prepare
  running -> success

transform
  dependency wait -> running -> success

publish
  dependency wait -> running -> success
```

질문한다.

- `transform` Task definition은 처음부터 존재했는데 왜 바로 실행되지 않았는가?
- `publish`의 user code가 실행되기 전에 Airflow에는 publish TaskInstance가 존재할 수 있는가?
- 각 색은 definition의 속성인가, 특정 DagRun의 runtime state인가?

UI는 workflow 전체의 관계를 보는 데 강하지만, 정확한 문자열 state와 identifier를 고정해서 비교하기에는 CLI가 더 편하다.

## 7. 관측면 2: CLI state snapshot

최근 run 목록을 본다.

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_runtime -o table
```

여기서 방금 실행한 `run_id`를 복사한다.

예를 들어 `<RUN_ID>`라고 하자.

```bash
bash lab/airflow.sh tasks states-for-dag-run \
  adudeck_observable_runtime \
  '<RUN_ID>' \
  -o table
```

Task가 실행 중인 동안 여러 번 실행하면 snapshot이 달라진다.

```text
시점 A
prepare    running
transform  none / scheduled 계열
publish    none / scheduled 계열

시점 B
prepare    success
transform  running
publish    none / scheduled 계열

시점 C
prepare    success
transform  success
publish    success
```

실제 표시되는 intermediate state는 timing에 따라 다를 수 있다. 중요한 것은 **같은 TaskInstance가 시간에 따라 state transition을
겪는다는 것**이다.

## 8. 관측면 3: task/component log

standalone을 실행한 terminal과 UI의 task log에서 다음 marker를 찾는다.

```text
[ADUDECK_OBSERVE]
```

lab DAG는 task가 실행되는 순간 다음 runtime identifier를 출력한다.

```text
dag_id
run_id
task_id
try_number
logical_date
data_interval_start
data_interval_end
```

이 log에서 중요한 사실은 TaskFlow Python 함수가 단순한 일반 함수 호출처럼 실행되는 것이 아니라는 점이다.

Dag file을 parsing할 때 `prepare()`의 business logic이 바로 실행된 것이 아니다. scheduler가 특정 TaskInstance를 실행 가능하다고
판단한 뒤 task runtime에서 함수 body가 실행되었다.

### Parsing time과 task execution time 구분

다음 코드를 비교한다.

```python
print("module top level")

@task
def work():
    print("inside task")
```

두 print는 같은 의미가 아니다.

- module top-level code: Dag parsing 과정에서 실행될 수 있다.
- `inside task`: TaskInstance execution에서 실행된다.

Airflow DAG authoring에서는 이 차이가 매우 중요하다.

## 9. 관측면 4: metadata DB를 read-only로 본다

동일한 run을 metadata DB에서도 찾는다.

```bash
python lab/inspect_metadata.py \
  --dag-id adudeck_observable_runtime \
  --run-id '<RUN_ID>'
```

probe는 local standalone이 사용하는 SQLite metadata database의 `dag_run`, `task_instance` table에서 현재 version에 존재하는
주요 column만 골라 출력한다.

찾아볼 값은 다음과 같다.

```text
dag_run
- dag_id
- run_id
- state
- logical_date
- start/end 관련 timestamp

task_instance
- task_id
- state
- try_number
- start_date / end_date
```

여기서 metadata DB를 수정하지 않는다.

### UI, CLI, DB가 같은 object를 가리키는지 검증한다

다음 key를 맞춰 본다.

```text
DagRun identity
= dag_id + run_id

TaskInstance identity를 이해하는 핵심
= DagRun identity + task_id (+ map index가 필요한 경우)
```

UI의 run, CLI의 run, DB row가 이 identifier로 연결되는지 확인한다.

## 10. 실제 side effect는 별도로 본다

lab task는 `lab/output/` 아래에 JSON file을 만든다.

```bash
find lab/output -maxdepth 1 -type f -print
```

방금 run에 대응하는 file을 열어 본다.

```bash
cat lab/output/<파일명>
```

대략 세 stage가 보인다.

```text
manifest
transformed
published
```

여기서 중요한 distinction이 생긴다.

```text
Airflow metadata DB
    "publish TaskInstance가 success다"

lab/output
    "publish가 실제 file side effect를 남겼다"
```

TaskInstance state는 external system의 data 자체가 아니다. Airflow가 orchestration을 위해 관리하는 control-plane evidence다.

실제 production에서는 이 output이 S3 object, warehouse partition, API side effect 등이 될 수 있다.

## 11. 하나의 execution을 끝까지 다시 그린다

관찰한 evidence를 이용해 다음 빈칸을 채운다.

```text
1. Dag Processor
   observable_runtime.py를 ________ 한다.

2. Metadata DB
   Dag definition과 runtime ________ 를 저장한다.

3. Trigger
   새로운 ________ 이 생성된다.

4. Scheduler
   prepare TaskInstance의 dependency를 평가하고 ________ 가능하다고 판단한다.

5. Executor / task runtime
   prepare의 user code가 실제로 실행되고 ________ file을 만든다.

6. State update
   prepare가 success가 되면 scheduler가 ________ 의 dependency를 다시 평가한다.

7. UI / CLI / metadata probe
   서로 다른 관측면에서 같은 ________ 와 ________ 를 확인한다.
```

명령어를 기억하는 것보다 이 흐름을 설명할 수 있는지가 중요하다.

## 12. 실패를 찾을 때 layer부터 구분한다

"DAG가 안 돈다"는 현상을 다음 순서로 쪼갠다.

```text
1. Definition layer
   Dag가 parsing되었는가?

2. DagRun layer
   실행해야 할 DagRun이 존재하는가?

3. Dependency layer
   TaskInstance의 upstream 조건이 충족되었는가?

4. Scheduling layer
   scheduler가 task를 runnable하다고 판단할 수 있는가?

5. Execution layer
   task runtime이 실제 user code를 시작했는가?

6. Side-effect layer
   user code가 external output을 의도대로 만들었는가?
```

각 layer에는 다른 evidence가 있다.

| Layer | 먼저 볼 evidence |
| --- | --- |
| Definition | `dags list`, import errors, Dag Processor log |
| DagRun | UI run list, `dags list-runs`, `dag_run` metadata |
| Dependency | Grid, TaskInstance state |
| Scheduling | scheduler log, TaskInstance intermediate state |
| Execution | task log, try number, process/runtime error |
| Side effect | output file, database/object storage/API 결과 |

## Practice

### 1. Object counting

하나의 Dag에 Task가 세 개 있다. 같은 Dag가 두 번 실행되었다.

다음을 구분해서 답한다.

- Dag definition 수
- DagRun 수
- Task definition 수
- TaskInstance 수

### 2. Evidence classification

다음 evidence가 주로 어떤 layer를 설명하는지 분류한다.

- `dags list-import-errors`
- Grid의 `transform=running`
- `task_instance.try_number=2`
- `lab/output/...-published.json`
- task log의 Python traceback

### 3. Cross-view consistency

실제 한 run을 골라 다음 표를 직접 만든다.

| 항목 | UI | CLI | metadata probe | task log/output |
| --- | --- | --- | --- | --- |
| dag_id | | | | |
| run_id | | | | |
| transform state | | | | |
| try_number | | | | |
| 실제 output 존재 여부 | | | | |

표의 모든 cell이 같은 값을 가져야 하는 것은 아니다. 왜 어떤 관측면에는 값이 없거나 다른 표현을 쓰는지 설명한다.

### 4. Transfer

자신이 운영하는 batch pipeline 하나를 떠올린다.

Airflow를 사용하지 않더라도 다음을 나눠 적는다.

```text
workflow definition:
execution instance:
unit of work definition:
unit of work runtime instance:
control-plane state:
external side effect:
```

## Checkpoint

다음을 자신의 말로 설명할 수 있으면 다음 chapter로 간다.

> DAG Python 파일이 존재하는 것, Dag가 parsing되는 것, DagRun이 생성되는 것, TaskInstance가 실행되는 것, external output이
> 생기는 것은 서로 다른 사건이다. Airflow를 debugging할 때는 이 사건들을 하나로 뭉개지 않고 각 layer의 evidence를 확인한다.

## References

- [Architecture Overview](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [Scheduler](https://airflow.apache.org/docs/apache-airflow/stable/concepts/scheduler.html)
- [Dag Serialization](https://airflow.apache.org/docs/apache-airflow/stable/dag-serialization.html)
- [CLI Reference](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
