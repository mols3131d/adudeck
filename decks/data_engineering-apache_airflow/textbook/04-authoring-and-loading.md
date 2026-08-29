# 04. Dag authoring과 loading: Python file에서 runtime definition까지

Airflow에서 Dag를 작성한다는 것은 단순히 Python 함수를 묶는 일이 아니다.

이번 chapter의 목표는 **내가 작성한 Python source가 언제 Dag definition으로 해석되고, 언제 TaskInstance execution으로 넘어가는지**를 구분하는 것이다. 이 구분이 없으면 import error, Dag discovery 문제, local test failure, scheduler-backed runtime failure를 모두 "Airflow가 안 돈다"로 뭉개게 된다.

이번 chapter에서는 다음 경계를 하나의 흐름으로 연결한다.

```text
Python source file
   ↓
Python import / Dag parsing
   ↓
Dag + Task definition discovery
   ↓
local task / Dag test
   ↓
scheduler-backed DagRun
   ↓
TaskInstance execution
```

같은 source file을 다루더라도 각 단계에서 존재하는 state와 evidence가 다르다.

## 1. `airflow.sdk`는 Dag authoring의 public boundary다

Airflow 3에서 Dag author가 사용하는 핵심 authoring surface는 `airflow.sdk`다.

```python
from airflow.sdk import dag, task
```

이 import는 단순한 style choice가 아니다. Airflow 내부 scheduler/database implementation에 직접 의존하지 않고 **Dag authoring에 필요한 stable public interface**를 사용하겠다는 boundary다.

다음 Dag를 보자.

```python
from airflow.sdk import dag, task


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

여기에는 서로 다른 두 종류의 실행이 섞여 있다.

1. module이 import될 때 Dag와 Task definition을 만드는 Python execution
2. scheduler가 특정 TaskInstance를 실행할 때 task body를 수행하는 runtime execution

이 둘을 먼저 분리한다.

## 2. Dag file은 application entrypoint와 다르다

일반 Python script는 보통 다음처럼 생각한다.

```text
python app.py
→ top to bottom execution
→ process 종료
```

Dag file은 다르다. Airflow의 Dag Processor는 source를 반복해서 읽고 parse할 수 있다.

따라서 module top-level code는 "workflow가 실행될 때 한 번만 수행되는 initialization"이라고 생각하면 안 된다.

```python
print("module imported")

@task
def load_orders():
    print("task executed")
```

두 `print`의 실행 시점을 예측해 보자.

- `module imported`는 Dag file을 import/parse하는 과정에서 실행될 수 있다.
- `task executed`는 특정 TaskInstance가 실제로 실행될 때 task body 안에서 실행된다.

이 차이는 단순한 성능 팁이 아니다. top-level에서 database query, remote API call, 대용량 file read를 수행하면 Dag Processor의 반복 parsing과 결합된다.

따라서 다음 mental model을 유지한다.

```text
Dag authoring code
→ definition을 만든다

Task body
→ runtime side effect를 만든다
```

## 3. decorator를 호출하면 바로 business task가 실행되는가

TaskFlow code는 일반 Python function composition처럼 보일 수 있다.

```python
result = extract()
transform(result)
```

하지만 Dag authoring context에서 `@task`로 감싼 함수 호출은 일반 함수를 즉시 실행해 business result를 얻는 것과 다르다.

개념적으로는 다음에 가깝다.

```text
extract()
→ extract Task를 현재 Dag graph에 연결하는 invocation
→ downstream에서 참조할 task output handle 생성

transform(extract())
→ transform Task definition과 dependency/data relationship 구성
```

실제 `extract` 함수 body는 특정 TaskInstance가 실행될 때 수행된다.

그래서 Dag graph를 만드는 시점에는 다음 질문이 중요하다.

- 어떤 Task definition이 존재하는가?
- dependency edge는 어떻게 연결되는가?
- runtime에서 어떤 TaskInstance들이 생길 수 있는가?

아직 "extract가 어떤 row를 반환했는가"를 물을 단계가 아니다.

## 4. worked trace: source가 runtime object가 되기까지

다음 source를 생각하자.

```python
from airflow.sdk import dag, task


@dag(schedule=None)
def pipeline():
    @task
    def prepare():
        print("prepare body")

    @task
    def publish():
        print("publish body")

    prepare() >> publish()


pipeline()
```

한 번의 scheduler-backed execution까지 추적하면 다음과 같다.

| 단계 | 일어나는 일 | 아직 일어나지 않은 일 | evidence |
| --- | --- | --- | --- |
| source exists | `.py` file이 filesystem에 있다 | Python import 성공 여부 | file/path |
| import/parse | module code가 실행되고 Dag definition을 구성한다 | DagRun 생성, task body 실행 | import error surface |
| Dag discovery | Airflow가 Dag ID와 task graph를 인식한다 | scheduler-backed execution | `dags list`, `tasks list` |
| local test | isolated task/Dag code를 실행해 볼 수 있다 | 실제 scheduler가 해당 run을 만들었다는 보장 | `tasks test`, `dags test` |
| DagRun creation | scheduler-backed runtime에 한 execution instance가 생긴다 | 모든 task 성공 | UI/CLI/metadata |
| TaskInstance run | 특정 Task의 runtime body가 실행된다 | downstream 성공 보장 | state/log/side effect |

이 표의 핵심은 각 단계가 이전 단계보다 더 강한 evidence를 추가하지만, 뒤 단계를 자동으로 증명하지 않는다는 점이다.

```text
file exists
!=
imports successfully
!=
Dag discovered
!=
local test succeeds
!=
DagRun exists
!=
TaskInstance succeeds
```

## 5. dependency는 code order가 아니라 runtime constraint다

다음 두 코드는 같은 graph를 만들 수 있다.

```python
first = inspect_source()
second = build_summary()
first >> second
```

```python
build_summary(inspect_source())
```

표현 방식보다 중요한 것은 graph에 남는 dependency다.

```text
inspect_source
      |
      v
build_summary
```

scheduler는 source file의 줄 순서를 따라 business 함수를 순차 호출하는 것이 아니다. DagRun 안에서 TaskInstance state와 dependency를 보고 어떤 task가 실행 가능한지 판단한다.

따라서 Task boundary를 추가할 때는 "함수를 나누면 코드가 예뻐진다"보다 다음을 묻는다.

- 이 단계는 독립적인 success/failure state가 필요한가?
- 이 단계만 retry할 가치가 있는가?
- 별도 log가 debugging search space를 줄이는가?
- 이 단계가 가지는 input/output responsibility를 설명할 수 있는가?

이 조건이 없다면 Task를 더 잘게 나누는 것이 항상 좋은 설계는 아니다.

## 6. Observable Lab A: starter를 실행하기 전에 graph를 예측한다

이번 chapter에서는 다음 starter를 사용한다.

```text
lab/dags/exercises/u2_authoring_starter.py
Dag ID: adudeck_u2_authoring_starter
```

먼저 source를 읽고 runtime을 시작하기 전에 적는다.

1. Task definition은 몇 개인가?
2. TaskInstance가 실제 run에서 몇 개 만들어질 것으로 예상하는가?
3. 어떤 dependency가 존재하는가?
4. `_observe()` 안의 code는 parse time에 실행되는가, task runtime에 실행되는가?

그 다음 local discovery를 확인한다.

```bash
bash lab/airflow.sh db migrate
bash lab/airflow.sh dags list --local
bash lab/airflow.sh tasks list adudeck_u2_authoring_starter
```

여기까지 성공했을 때 증명한 것은 **source가 현재 local Airflow environment에서 Dag definition으로 발견될 수 있다는 것**이다.

아직 scheduler-backed DagRun은 만들지 않았다.

## 7. Observable Lab B: local execution과 scheduler-backed execution을 비교한다

먼저 scheduler 없이 task를 test한다.

```bash
bash lab/airflow.sh tasks test \
  adudeck_u2_authoring_starter \
  inspect_source \
  2026-01-01
```

그리고 전체 Dag도 test한다.

```bash
bash lab/airflow.sh dags test \
  adudeck_u2_authoring_starter \
  2026-01-01
```

여기서 다음을 기록한다.

```text
local task/Dag code가 실행되었는가?
어떤 log/evidence가 생겼는가?
실제 scheduler-backed DagRun을 만들었다고 말할 수 있는가?
```

이제 `standalone`을 시작한다.

```bash
bash lab/airflow.sh standalone
```

별도 terminal에서 Dag를 trigger한다.

```bash
bash lab/airflow.sh dags trigger adudeck_u2_authoring_starter
```

최근 run을 찾고 snapshot한다.

```bash
bash lab/scripts/snapshot.sh adudeck_u2_authoring_starter
```

local test와 scheduler-backed run을 비교한다.

| 질문 | local `tasks test` / `dags test` | scheduler-backed trigger |
| --- | --- | --- |
| task code를 실행할 수 있는가 | 가능 | 가능 |
| scheduler가 run을 선택·진행하는가 | 핵심 대상 아님 | 예 |
| 실제 DagRun/TaskInstance control-plane state를 관찰하는가 | 같은 의미로 간주하지 않음 | 예 |
| UI/CLI/metadata에서 같은 runtime identity를 연결하는가 | 제한적 | 핵심 evidence |

## 8. Controlled failure: parse/load failure를 일부러 만든다

runtime failure만 경험하면 "Python file이 있으면 일단 Dag는 등록된다"는 잘못된 mental model이 남기 쉽다.

starter를 local working copy에서 잠시 다음처럼 깨뜨린다.

```python
from package_that_does_not_exist import impossible_import
```

아직 scheduler-backed task를 trigger하려 하지 않는다. 먼저 local import surface를 본다.

```bash
bash lab/airflow.sh dags list-import-errors --local -o table
```

질문한다.

- failure는 DagRun 안에서 발생했는가?
- TaskInstance `failed` state가 생겼는가?
- scheduler retry 설정으로 이 문제를 해결할 수 있는가?

답은 모두 같은 방향을 가리킨다. **이 문제는 runtime task failure가 아니라 Dag definition을 만들기 전의 import/load boundary 문제**다.

문제를 확인한 뒤 해당 import를 제거하고 다시 확인한다.

```bash
bash lab/airflow.sh dags list --local
bash lab/airflow.sh dags list-import-errors --local -o table
```

controlled failure는 반드시 정상 parse 상태로 복구하고 다음 단계로 넘어간다.

## 9. modification: 의미 있는 Task boundary를 하나 추가한다

starter의 baseline은 다음과 같다.

```text
inspect_source -> build_summary
```

여기에 task 하나를 추가한다. 단, 단순히 `middle_task`를 넣는 것이 목표가 아니다.

다음 요구를 사용한다.

> source inspection 결과를 검증하는 단계가 별도 failure/retry/log boundary를 가져야 한다.

예를 들어 graph를 다음처럼 만든다.

```text
inspect_source -> validate_source -> build_summary
```

수정 전에 먼저 적는다.

- 왜 validation은 독립 Task여야 하는가?
- validation failure가 발생하면 `build_summary`는 어떤 상태가 될 것으로 예상하는가?
- 이 단계를 일반 Python helper 함수로만 두었을 때와 Task로 둘 때 operational evidence가 어떻게 달라지는가?

그 다음 `tasks list`와 scheduler-backed run에서 실제 graph/state를 확인한다.

단순히 task count가 2에서 3으로 늘어난 것을 성공 기준으로 삼지 않는다. **새 boundary가 독립 state/log/retry 책임을 가진다는 설명**이 핵심이다.

## 10. 흔한 잘못된 mental model

### "파일이 있으니 Dag도 있다"

filesystem에 Python file이 있는 것과 Airflow가 parse 가능한 Dag definition을 발견한 것은 다르다.

### "`@task` 함수 호출은 parse할 때 business code를 실행한다"

Dag authoring 중에는 Task graph와 output/dependency relationship을 구성한다. task body의 runtime execution은 특정 TaskInstance에서 일어난다.

### "`dags test`가 성공했으니 scheduler도 정상이다"

local test는 매우 유용하지만 scheduler-backed control-plane state와 동일한 evidence가 아니다.

### "import error도 retry를 늘리면 된다"

retry는 TaskInstance runtime policy다. Dag definition 자체를 만들지 못하는 import/load failure와 layer가 다르다.

### "Task는 작을수록 좋다"

Task는 state/retry/log/side-effect boundary다. 독립 운영 의미가 없는 분할은 graph와 runtime overhead만 늘릴 수 있다.

## 11. Practice

### A. Trace

다음 사건을 올바른 순서로 배열하고, 각 단계에서 얻을 수 있는 evidence를 하나씩 적는다.

```text
TaskInstance success
Dag file import
DagRun creation
filesystem에 file 저장
Dag discovery
```

### B. Diagnose

`dags list --local`에서 Dag가 보이지 않고 `dags list-import-errors --local`에는 `ModuleNotFoundError`가 있다.

다음 중 어떤 것부터 조사할지 순서를 정하고 이유를 설명한다.

- retry count
- task log
- Python import/dependency
- scheduler concurrency
- downstream dependency

### C. Compare

`tasks test`는 성공하지만 scheduler-backed trigger 뒤 expected DagRun을 찾을 수 없다.

"task code는 실행 가능하다"와 "scheduler-backed runtime이 정상이다" 사이에서 어떤 evidence가 추가로 필요한지 적는다.

### D. Design

다음 pipeline에서 Task boundary를 어디에 둘지 판단한다.

```text
read local config
→ extract 10 GB dataset
→ validate row count
→ load warehouse partition
```

모든 화살표를 Task로 만들 필요는 없다. 독립 state/retry/log/side-effect responsibility를 기준으로 선택하고 정당화한다.

## Assessment checkpoint

이번 chapter는 다음 두 과제를 별도 도움 없이 수행할 수 있을 때 통과한다.

### 1. Execution map

새로운 Dag source를 하나 받고 다음 boundary를 직접 표시한다.

```text
source existence
→ import/parse
→ Dag/task discovery
→ local execution test
→ DagRun
→ TaskInstance runtime
```

각 boundary에서 "무엇을 증명했는가"와 "아직 무엇을 증명하지 못했는가"를 한 문장씩 설명한다.

### 2. Authoring repair

starter에 다음 두 변경을 수행한다.

1. temporary parse/load failure를 하나 만들고 local evidence로 원인을 찾은 뒤 복구한다.
2. operational 의미가 있는 Task boundary 하나를 추가하고 scheduler-backed run에서 state/dependency evidence를 확인한다.

평가 기준은 command 수가 아니다.

- failure layer를 정확히 분류했는가?
- 새 Task boundary의 책임을 설명했는가?
- local test와 scheduler-backed evidence를 혼동하지 않았는가?
- 수정 뒤 Dag discovery와 runtime state를 다시 검증했는가?

이 기준을 만족하면 U2의 핵심 outcome인 **작은 Dag를 authoring하고 loading/runtime failure를 서로 다른 layer로 진단하는 능력**을 갖춘 것으로 본다.
