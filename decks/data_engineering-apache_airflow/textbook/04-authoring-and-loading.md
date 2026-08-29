# 04. Dag authoring과 loading: source에서 runtime까지

Airflow에서 Python file이 존재한다고 Dag가 실행 가능한 것은 아니다. Source는 여러 boundary를 통과한다.

```text
Python file
→ import / parse
→ Dag + Task discovery
→ local test
→ scheduler-backed DagRun
→ TaskInstance execution
```

이번 chapter의 목표는 이 단계들을 하나의 "Airflow 실행"으로 뭉개지 않는 것이다.

> **어느 단계까지 성공했는지 evidence로 말할 수 있어야 다음 debugging step을 올바르게 고를 수 있다.**

## 1. `airflow.sdk`는 Dag authoring의 public boundary다

Airflow 3의 Dag authoring code는 `airflow.sdk`를 중심으로 쓴다.

```python
from airflow.sdk import dag, task
```

```python
@dag(schedule=None)
def orders_pipeline():
    @task
    def extract():
        return "orders.json"

    @task
    def transform(path: str):
        print(path)

    transform(extract())


orders_pipeline()
```

여기에는 두 종류의 Python execution이 있다.

```text
parse time
→ Dag/Task definition과 dependency를 구성

task runtime
→ 특정 TaskInstance가 task body를 실행
```

이 구분이 가장 중요하다.

## 2. Dag file은 일반 application entrypoint와 다르다

Dag Processor는 Dag source를 반복해서 parse할 수 있다. 따라서 top-level code를 "workflow가 실행될 때 한 번만 수행되는
initialization"으로 보면 안 된다.

```python
print("module parsed")

@task
def work():
    print("task executed")
```

- `module parsed`: import/parse 과정에서 실행될 수 있다.
- `task executed`: 특정 TaskInstance runtime에서 실행된다.

Top-level network call, database query, 대용량 file read가 위험한 이유도 여기서 나온다. **Definition을 만드는 code와
business side effect를 수행하는 code의 lifecycle이 다르다.**

## 3. TaskFlow invocation은 즉시 business result를 얻는 일반 함수 호출이 아니다

```python
result = extract()
transform(result)
```

Dag authoring context에서 `@task` invocation은 graph와 output/dependency relationship을 만든다. 실제 `extract` body는
TaskInstance가 실행될 때 수행된다.

Parse time에 물을 질문:

```text
어떤 Task definition이 있는가?
dependency는 무엇인가?
runtime에서 어떤 TaskInstance가 생길 수 있는가?
```

Runtime에 물을 질문:

```text
어느 DagRun의 어느 TaskInstance인가?
state는 무엇인가?
어떤 side effect가 생겼는가?
```

## 4. Evidence ladder

같은 source를 다음 표로 추적한다.

| 단계 | 확인되는 것 | 아직 확인되지 않은 것 |
| --- | --- | --- |
| file exists | source가 filesystem에 있음 | import 성공 |
| import/parse | Python/Dag definition을 만들 수 있음 | scheduler-backed run |
| discovery | Dag ID/task graph를 찾을 수 있음 | task 성공 |
| `tasks test` / `dags test` | local execution 가능 | scheduler가 실제 run을 진행했다는 증거 |
| DagRun exists | runtime execution identity 존재 | 모든 task 성공 |
| TaskInstance success | 해당 runtime work 성공 | external data correctness 전체 |

Airflow 3.3.1 CLI의 `tasks test`는 dependency check나 DB state recording 없이 task instance를 test하는 local surface다.
따라서 다음 등식은 틀리다.

```text
dags test 성공
=
production/scheduler-backed run 검증 완료
```

Local test는 강한 evidence지만 **다른 종류의 evidence**다.

## 5. Task boundary는 code style보다 runtime responsibility다

다음 graph를 생각한다.

```text
inspect_source → validate_source → build_summary
```

`validate_source`를 별도 Task로 만드는 이유는 "함수를 작게 나누기 위해서"가 아니다.

좋은 Task boundary는 적어도 하나의 독립 의미를 가져야 한다.

```text
state boundary
retry boundary
log boundary
dependency boundary
side-effect responsibility
```

독립 운영 의미가 없다면 helper function으로 남기는 편이 더 단순할 수 있다.

## 6. Playground: 한 starter로 세 boundary를 비교한다

사용할 Dag:

```text
lab/dags/exercises/u2_authoring_starter.py
Dag ID: adudeck_u2_authoring_starter
```

### Step A — 실행 전에 graph를 예측한다

Source를 읽고 적는다.

```text
Task definition 수:
dependency:
_observe()가 실행되는 시점:
실제 run에서 예상되는 TaskInstance 수:
```

그 다음 discovery를 확인한다.

```bash
bash lab/airflow.sh db migrate
bash lab/airflow.sh dags list --local
bash lab/airflow.sh tasks list adudeck_u2_authoring_starter
```

여기서 얻은 결론은 **local environment가 Dag definition을 발견했다**는 것까지다.

### Step B — local test와 scheduler-backed run을 비교한다

```bash
bash lab/airflow.sh tasks test \
  adudeck_u2_authoring_starter \
  inspect_source \
  2026-01-01

bash lab/airflow.sh dags test \
  adudeck_u2_authoring_starter \
  2026-01-01
```

이후 `standalone`을 시작하고 실제 run을 trigger한다.

```bash
bash lab/airflow.sh standalone
```

다른 terminal:

```bash
bash lab/airflow.sh dags trigger adudeck_u2_authoring_starter
bash lab/scripts/snapshot.sh adudeck_u2_authoring_starter
```

두 실행을 다음 축으로 비교한다.

| 질문 | local test | scheduler-backed run |
| --- | --- | --- |
| task code를 실행할 수 있는가 | 예 | 예 |
| scheduler가 runtime state를 진행하는가 | 핵심 대상 아님 | 예 |
| DagRun/TaskInstance identity를 cross-view로 추적하는가 | 제한적 | 핵심 evidence |

### Step C — parse failure를 일부러 만든다

Local working copy에 잠시 잘못된 import를 넣는다.

```python
from package_that_does_not_exist import impossible_import
```

먼저 볼 것은 task retry가 아니다.

```bash
bash lab/airflow.sh dags list-import-errors --local -o table
```

질문한다.

```text
DagRun이 생겼는가?
TaskInstance failed state가 생겼는가?
retry가 해결할 layer인가?
```

원인을 확인한 뒤 source를 정상 상태로 복구한다.

### Step D — 의미 있는 Task boundary 하나를 추가한다

Baseline:

```text
inspect_source → build_summary
```

Requirement:

```text
inspection result validation은 독립 failure/log/retry boundary가 필요하다.
```

수정:

```text
inspect_source → validate_source → build_summary
```

Task 수가 늘었다는 사실보다 **왜 독립 runtime boundary가 필요한지** 설명하고, `tasks list`와 scheduler-backed run에서
예측한 graph/state가 실제로 나타나는지 확인한다.

## 7. Validation boundary

```text
source inspection
→ code 구조만 확인

dags list --local / import errors
→ local parse/discovery evidence

tasks test / dags test
→ local execution evidence

standalone + trigger + snapshot
→ scheduler-backed DagRun/TaskInstance evidence

external output
→ business side effect evidence
```

한 단계의 성공을 다음 단계로 자동 승격하지 않는다.

## 8. 흔한 오해

### "파일이 있으면 Dag도 있다"

Import/parse/discovery를 통과해야 한다.

### "`@task` 함수를 호출했으니 business code도 실행됐다"

Dag authoring invocation과 TaskInstance execution은 다른 lifecycle이다.

### "`dags test`가 성공했으니 scheduler도 정상이다"

Local test와 scheduler-backed runtime은 다른 evidence surface다.

### "import error는 retry를 늘리면 해결된다"

Retry는 TaskInstance runtime policy다. Parse/load failure와 layer가 다르다.

### "Task는 작을수록 좋다"

Task boundary에는 독립 operational responsibility가 있어야 한다.

## 9. Practice

### A. Evidence ordering

다음을 약한 evidence → 강한 runtime evidence 순서로 배열하고 각 단계가 **아직 증명하지 못하는 것**을 하나 적는다.

```text
TaskInstance success
Dag discovery
source file exists
local dags test success
DagRun exists
```

### B. Diagnosis

```text
dags list --local에서 Dag가 안 보임
dags list-import-errors --local에서 ModuleNotFoundError
```

retry count, task log, scheduler concurrency, Python import/dependency 중 무엇부터 볼지 선택하고 이유를 설명한다.

### C. Boundary judgment

하나의 Task 안에 다음 세 step이 있다.

```text
download → validate → publish
```

`validate`를 별도 Task로 만들지 판단한다. Function length가 아니라 **state/retry/log/side-effect responsibility**를
근거로 답한다.

## Assessment checkpoint

다음을 독립적으로 할 수 있으면 통과한다.

1. `file → parse → discovery → local test → DagRun → TaskInstance`를 evidence와 함께 추적한다.
2. Parse/load failure와 task runtime failure를 구분해 첫 debugging surface를 선택한다.
3. TaskFlow definition time과 task execution time을 설명한다.
4. 새 Task boundary가 필요한지 operational responsibility로 판단한다.
