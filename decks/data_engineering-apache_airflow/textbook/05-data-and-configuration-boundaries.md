# 05. Data와 configuration boundary: Params, XCom, storage, Variable, Connection

Airflow를 처음 사용하면 "task에서 필요한 값"을 하나의 범주로 생각하기 쉽다.

하지만 실제 workflow에는 서로 다른 책임의 값이 섞여 있다.

```text
이번 DagRun에서 선택한 입력
Task A가 Task B에게 넘길 작은 metadata
실제 business dataset
runtime-dependent configuration
external system endpoint / credential
version-controlled workflow policy
```

이 값들을 같은 channel에 넣으면 workflow는 실행될 수 있어도 책임 경계가 흐려진다. 이번 chapter의 목표는 **값의 크기보다 ownership과 lifecycle을 기준으로 적절한 channel을 선택하는 것**이다.

이번 chapter에서는 다음 다섯 surface를 구분한다.

```text
Params
XCom / TaskFlow return
external storage
Variable
Connection
```

그리고 한 가지를 더 추가한다.

```text
ordinary Dag code / version-controlled configuration
```

Airflow 기능이 존재한다고 모든 설정을 Airflow metadata로 옮길 필요는 없다.

## 1. 먼저 "누가 이 값을 소유하는가"를 묻는다

예를 들어 주문 pipeline에 다음 값이 필요하다고 하자.

```text
region = "apac"
input_dataset = 10 GB orders
staged_path = "s3://.../orders.parquet"
environment = "prod"
warehouse credential
minimum_row_count = 1000
```

모두 문자열이나 Python value로 표현할 수 있지만 의미는 전혀 다르다.

| 값 | 핵심 질문 |
| --- | --- |
| `region` | 이번 run마다 caller가 선택하는가? |
| 10 GB dataset | orchestration metadata인가, 실제 business data인가? |
| `staged_path` | downstream이 actual data를 찾기 위한 작은 identifier인가? |
| `environment` | 여러 run/task가 공유하는 runtime-dependent setting인가? |
| credential | external system access configuration인가? |
| `minimum_row_count` | deploy와 함께 version control로 관리할 workflow policy인가? |

channel 선택은 이 질문들의 답에서 나온다.

## 2. Params: 이번 DagRun의 입력

Airflow `Params`는 DagRun을 시작할 때 주어지는 runtime configuration을 표현할 수 있다.

```python
from airflow.sdk import Param, dag


@dag(
    schedule=None,
    params={
        "region": Param(
            "all",
            type="string",
            enum=["all", "apac", "emea"],
        )
    },
)
def pipeline():
    ...
```

이 `region`의 의미는 다음과 같다.

```text
같은 Dag definition
+
이번 run에서 선택한 region
=
이번 DagRun의 logical input configuration
```

manual trigger마다 `apac`, `emea`를 다르게 선택할 수 있다면 Param이 자연스럽다.

반대로 모든 run에서 동일하고 code review와 함께 바뀌어야 하는 constant를 굳이 Param으로 만들면 caller에게 필요 없는 선택권을 노출하게 된다.

### validation은 task runtime보다 앞선 boundary일 수 있다

Param은 JSON Schema 기반 validation을 사용할 수 있다.

허용 값이 다음뿐이라고 하자.

```text
all
apac
emea
```

caller가 `north-pole`을 넣었다면 좋은 질문은 "어느 task가 failed가 되는가?"가 아니다.

먼저 묻는다.

> 이 입력이 유효하지 않다면 DagRun을 만들어 task를 실행하는 단계까지 가야 하는가?

입력 validation과 task runtime failure를 분리해야 한다.

## 3. XCom: task 사이의 orchestration data

TaskFlow에서는 task return value가 downstream으로 전달될 수 있다.

```python
@task
def stage_orders() -> str:
    ...
    return "s3://bucket/run-123/orders.parquet"


@task
def transform(path: str):
    ...


transform(stage_orders())
```

여기서 XCom에 전달하기 좋은 것은 **actual 10 GB dataset이 아니라 dataset을 찾기 위한 작은 identifier**다.

```text
XCom
→ path / URI / table name / object key / row count / small metadata

external storage
→ actual business dataset
```

왜 이 분리가 중요한가?

Airflow metadata plane은 orchestration state를 관리한다. business data plane까지 metadata channel에 밀어 넣으면 persistence, serialization, database load, observability 책임이 섞인다.

따라서 XCom을 다음처럼 생각하면 유용하다.

> "다음 Task가 logical output을 찾거나 판단하는 데 필요한 작은 orchestration metadata"

이것이 모든 XCom value에 대한 절대적인 byte-size rule은 아니다. 핵심은 **business dataset storage 책임을 Airflow metadata에 떠넘기지 않는 것**이다.

## 4. external storage: actual business state

이번 lab에서는 object storage나 warehouse 대신 filesystem을 사용한다.

```text
lab/fixtures/orders.jsonl
lab/output/u5/...
```

filesystem을 사용하는 이유는 production architecture를 흉내 내기 위해서가 아니다. 다음 책임 분리를 눈으로 확인하기 위해서다.

```text
TaskInstance / XCom
→ orchestration state + identifier

file contents
→ actual business rows
```

TaskInstance가 `success`라고 해서 business output을 읽지 않아도 되는 것은 아니다. 반대로 file이 존재한다고 해서 Airflow가 해당 TaskInstance를 `success`로 기록했다는 뜻도 아니다.

control-plane state와 data-plane side effect는 연결되어 있지만 동일하지 않다.

## 5. Variable: shared runtime-dependent configuration

Airflow `Variable`은 runtime에서 resolve되는 key/value configuration에 사용할 수 있다.

```python
from airflow.sdk import Variable

environment = Variable.get("adudeck_environment", default="local-lab")
```

여기서 중요한 것은 "설정이면 Variable"이 아니다.

다음 둘을 비교한다.

```text
A. environment endpoint가 deployment마다 달라지고 runtime에서 주입된다
B. retry policy threshold가 Dag source와 함께 review되어야 한다
```

A는 Variable 같은 runtime configuration surface가 적합할 수 있다.

B는 ordinary version-controlled Dag code에 두는 편이 더 명확할 수 있다.

Variable을 과도하게 사용하면 source만 읽고 workflow behavior를 이해하기 어려워진다. 따라서 질문은 다음과 같다.

> 이 값은 정말 deploy/runtime context에 따라 바뀌어야 하는가, 아니면 workflow definition의 일부인가?

## 6. Connection: external-system access configuration

Connection은 external system과 통신하기 위한 endpoint와 authentication configuration을 표현한다.

개념적으로 다음과 같은 정보가 들어갈 수 있다.

```text
conn_id
conn_type
host
port
login
password / token / extra
```

이번 lab은 `adudeck_demo_api`라는 teaching-only Connection을 사용한다.

Connection을 다룰 때 가장 중요한 학습 규칙은 다음이다.

```text
credential
!=
DagRun Param
!=
XCom
!=
log output
```

credential을 `params={"password": ...}`로 넣거나 task return으로 전달하거나 debugging 편의를 위해 출력하면 책임과 security boundary가 무너진다.

lab에서도 password는 log, XCom, output file에 기록하지 않는다.

## 7. logical role과 resolution backend를 분리한다

Variable과 Connection을 배우면서 자주 생기는 오해가 있다.

> "Variable/Connection은 metadata DB row다."

그렇게 저장할 수 있지만 **논리적 역할과 실제 resolution backend는 다른 차원**이다.

같은 `Variable.get("adudeck_environment")` 호출도 deployment에 따라 값이 다음에서 resolve될 수 있다.

```text
metadata database
process environment
external secrets backend
```

Connection도 마찬가지다.

```text
logical role
Connection = external-system access configuration

resolution backend
= environment / metadata DB / secrets backend / ...
```

이번 lab의 demo Variable과 Connection은 environment-backed teaching value다. 따라서 metadata DB row listing에 보이지 않을 수 있다.

이것은 "Connection이 존재하지 않는다"는 뜻이 아니다. task runtime이 어떤 backend를 통해 값을 resolve하는지를 따로 보아야 한다.

## 8. worked example: 여섯 값을 어디에 둘 것인가

다음 요구를 설계해 보자.

```text
1. manual trigger에서 region을 선택한다.
2. 10 GB 주문 data를 처리한다.
3. stage task가 downstream에 staged object 위치를 넘긴다.
4. deployment마다 API hostname이 다르다.
5. API token이 필요하다.
6. row count가 1000 미만이면 pipeline을 실패시킨다.
```

가능한 mapping은 다음과 같다.

| 요구 | surface | 이유 |
| --- | --- | --- |
| region | Param | run마다 caller가 선택하는 logical input |
| 10 GB 주문 data | external storage | actual business data |
| staged object 위치 | XCom | downstream이 data를 찾는 작은 identifier |
| deployment별 hostname | Connection 또는 runtime config | external endpoint responsibility |
| API token | Connection / secrets-backed config | credential boundary |
| minimum row count 1000 | Dag code | workflow policy로 version review 가능 |

마지막 값이 특히 중요하다. Airflow에 Variable 기능이 있다는 이유만으로 `minimum_row_count`를 Variable에 넣지 않았다.

정책 변경이 code review/deploy와 함께 일어나야 한다면 source가 더 좋은 owner일 수 있다.

## 9. Observable Lab A: baseline의 channel을 먼저 표시한다

다음 starter를 사용한다.

```text
lab/dags/exercises/u5_boundaries_starter.py
Dag ID: adudeck_u5_boundaries_starter
```

source를 읽고 실행 전에 다음 표를 채운다.

| 값 | 예상 owner/channel |
| --- | --- |
| `region` | |
| fixture 주문 rows | |
| `dataset_path` | |
| `adudeck_environment` | |
| `adudeck_demo_api` | |
| Connection password | |

그 다음 `standalone`을 시작하고 `region=apac`으로 trigger한다.

```bash
bash lab/airflow.sh dags trigger \
  -c '{"region":"apac"}' \
  adudeck_u5_boundaries_starter
```

run을 관찰한다.

```bash
bash lab/scripts/snapshot.sh adudeck_u5_boundaries_starter '<RUN_ID>'
```

확인할 evidence는 다음이다.

```text
DagRun Param value
XCom이 전달한 dataset path의 의미
lab/output/u5/의 actual business rows
Variable value
Connection의 non-secret metadata
```

이 다섯 정보를 하나의 "task input"으로 뭉개지 않는다.

## 10. Observable Lab B: input validation failure를 runtime failure와 비교한다

허용되지 않은 region을 넣기 전에 결과를 예측한다.

```bash
bash lab/airflow.sh dags trigger \
  -c '{"region":"north-pole"}' \
  adudeck_u5_boundaries_starter
```

질문한다.

- invalid input이 task body까지 들어갈 것으로 예상하는가?
- `stage_orders` TaskInstance의 business logic이 실행되어야 하는가?
- validation failure와 `transform` Python exception은 같은 layer인가?

실제 UI/CLI 결과를 보고 예측을 수정한다.

핵심은 error message를 외우는 것이 아니라 **invalid run configuration이 runtime task failure보다 앞선 validation boundary에 있을 수 있음을 구분하는 것**이다.

## 11. Observable Lab C: backend와 logical role을 분리한다

starter는 다음을 runtime에서 resolve한다.

```python
Variable.get("adudeck_environment", default="local-lab")
Connection.get("adudeck_demo_api")
```

lab wrapper가 제공하는 teaching value는 environment-backed다.

다음을 비교한다.

```text
task runtime에서는 값이 resolve됨

vs.

metadata DB / UI listing에 동일한 row가 반드시 존재함
```

두 조건이 같은지 확인한다.

그 다음 다음 문장을 완성한다.

> `adudeck_demo_api`가 Connection인 이유는 metadata DB에 저장되어서가 아니라, __________ 책임을 표현하기 때문이다.

정답의 핵심은 "external-system access configuration"이다.

## 12. Modification Lab: requirement가 바뀌면 channel을 다시 선택한다

baseline을 외운 뒤 값 이름만 보고 channel을 결정하지 않는다.

다음 변경 중 하나를 선택한다.

### 변경 A

`region`이 더 이상 manual input이 아니고 모든 deployment에서 항상 `apac`이어야 한다.

질문:

- Param을 유지할 이유가 있는가?
- source constant가 더 명확한가?

### 변경 B

`region`이 run마다 달라지지만 scheduler가 아닌 upstream application이 trigger하면서 결정한다.

질문:

- 여전히 DagRun input인가?
- ownership이 바뀌었는가, 아니면 공급자가 바뀌었을 뿐인가?

### 변경 C

`environment` 값이 실제로는 workflow invariant이며 deployment마다 달라지지 않는다.

질문:

- Variable이 계속 필요한가?
- source로 이동하면 어떤 observability가 좋아지는가?

### 변경 D

stage task가 10 GB dataset 자체를 return하도록 바꾸자는 제안이 들어왔다.

질문:

- XCom의 orchestration responsibility와 external storage responsibility가 어떻게 섞이는가?
- path/URI만 전달할 때와 비교해 어떤 coupling이 생기는가?

수정 후 다시 run하고 output/evidence를 비교한다.

## 13. 흔한 잘못된 mental model

### "작은 값이면 XCom, 큰 값이면 file"

크기는 실무적으로 중요하지만 첫 기준은 responsibility다. actual business dataset과 orchestration metadata를 구분한다.

### "설정은 전부 Variable"

version-controlled workflow policy는 source가 더 좋은 owner일 수 있다.

### "Connection은 secret 문자열 저장소"

Connection은 external-system access configuration이라는 logical object다. secret은 그 일부일 수 있고 backend는 별도 문제다.

### "environment-backed Connection은 진짜 Connection이 아니다"

logical role과 resolution backend를 혼동한 것이다.

### "Param과 Variable은 둘 다 runtime value라서 같다"

Param은 특정 DagRun의 input이라는 성격이 강하고, Variable은 여러 runtime에서 공유되는 runtime-dependent configuration에 가깝다.

### "credential도 task 사이에 전달하면 편하다"

편의보다 ownership과 exposure boundary가 우선이다. secret을 Param/XCom/log/output으로 흘리지 않는다.

## 14. Practice

### A. Classify

다음 값을 가장 자연스러운 owner에 배치하고 이유를 한 문장씩 적는다.

```text
manual backfill target region
warehouse table name that changes per deployment
warehouse password
2 GB transformed dataframe
transformed object URI
fraud threshold that code review와 함께 변경됨
```

후보:

```text
Param
XCom
external storage
Variable
Connection
Dag code
```

하나의 정답만 가능한 경우도 있고 요구에 따라 달라지는 경우도 있다. 필요한 assumption을 명시한다.

### B. Repair

다음 design의 문제를 찾는다.

```text
extract task
→ 500 MB JSON을 return
→ downstream TaskFlow argument로 전달

API token
→ Dag Param으로 manual trigger 시 입력

minimum_valid_rows
→ Variable.get("minimum_valid_rows")
```

각 항목에서 responsibility가 왜 어긋나는지 설명하고 더 나은 owner를 제안한다.

### C. Backend reasoning

`Connection.get("warehouse")`는 성공하지만 `connections list`에서 원하는 row가 보이지 않는다.

즉시 "Airflow metadata가 고장났다"고 결론 내리기 전에 확인할 수 있는 resolution backend를 적는다.

## Assessment checkpoint

이번 chapter는 다음 과제를 독립적으로 수행할 수 있을 때 통과한다.

### Boundary redesign

작은 batch workflow 요구가 주어진다.

```text
- caller가 run마다 market을 선택한다.
- source dataset은 수 GB다.
- extract와 load는 서로 다른 Task다.
- deployment마다 external API endpoint가 다르다.
- API credential이 필요하다.
- validation threshold는 repository review와 함께 변경한다.
```

learner는 다음을 제출한다.

1. 각 value의 owner/channel mapping
2. Task 사이에서 실제로 전달되는 값의 shape
3. credential이 지나가면 안 되는 surface
4. logical role과 resolution backend의 분리 설명
5. requirement 하나가 바뀌었을 때 mapping을 다시 판단한 결과

평가 기준:

- Params, XCom, external data, Variable, Connection을 이름이 아니라 responsibility로 구분했는가?
- actual business data와 orchestration metadata를 분리했는가?
- runtime configuration과 version-controlled policy를 구분했는가?
- credential exposure boundary를 지켰는가?
- backend가 바뀌어도 logical role이 유지될 수 있음을 설명했는가?

이 기준을 만족하면 U5의 핵심 outcome인 **run input, task metadata, business data, runtime config, external-system access config를 책임에 맞게 배치하는 능력**을 갖춘 것으로 본다.
