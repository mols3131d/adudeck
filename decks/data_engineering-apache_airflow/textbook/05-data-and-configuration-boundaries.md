# 05. Data와 configuration boundary: 값의 owner를 먼저 정한다

Airflow task가 사용하는 값은 모두 "task input"이 아니다. 같은 문자열이라도 lifecycle과 책임이 다르다.

```text
이번 DagRun의 선택값
task 사이의 작은 metadata
실제 business dataset
shared runtime configuration
external-system access configuration
version-controlled workflow policy
```

이번 chapter의 목표는 API 이름을 외우는 것이 아니라 **값의 owner와 lifecycle로 channel을 선택하는 것**이다.

## 1. 여섯 surface를 한 표로 시작한다

| 값의 역할 | 기본 후보 |
| --- | --- |
| run마다 caller가 선택하는 input | Param |
| task 사이의 작은 orchestration metadata | XCom / TaskFlow return |
| 실제 business data | external storage |
| runtime/deployment에 따라 달라지는 shared config | Variable |
| external system endpoint / credential | Connection |
| code review와 함께 바뀌는 workflow policy | Dag code |

이 표는 절대 규칙이 아니다. 선택 이유를 설명하기 위한 starting point다.

## 2. Params: 이번 DagRun의 logical input

```python
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

`region`이 manual trigger마다 달라질 수 있다면 Param이 자연스럽다.

```text
same Dag definition
+
this run's region
=
this DagRun's input configuration
```

반대로 모든 run에서 같은 값이고 source review와 함께 바뀌어야 하는 policy라면 Param으로 노출할 이유가 약하다.

Param validation failure와 task runtime failure도 구분한다. Invalid input을 task body까지 보내지 않는 것이 contract라면
runtime exception을 기다릴 문제가 아니다.

## 3. XCom: business data가 아니라 orchestration data를 전달한다

```python
@task
def stage_orders() -> str:
    ...
    return "s3://bucket/run-123/orders.parquet"
```

Downstream에는 actual dataset 대신 identifier를 전달한다.

```text
XCom
→ path / URI / table / object key / row count / small metadata

external storage
→ actual business rows
```

핵심은 임의의 byte-size cutoff가 아니다.

> **Airflow metadata plane이 business dataset의 primary storage 책임까지 가져가지 않게 한다.**

TaskFlow return이 편하다는 이유만으로 큰 DataFrame이나 dataset 전체를 orchestration metadata로 밀어 넣지 않는다.

## 4. External storage: business side effect의 owner

이번 lab은 object storage 대신 filesystem을 사용한다.

```text
lab/fixtures/orders.jsonl
lab/output/u5/...
```

관찰할 boundary:

```text
TaskInstance / XCom state
!=
file contents
```

TaskInstance가 `success`여도 output의 business correctness는 별도 evidence다. 반대로 file이 존재한다고 Airflow state가
success였다고 단정할 수도 없다.

## 5. Variable과 Dag code: runtime config인가 workflow policy인가

```python
environment = Variable.get(
    "adudeck_environment",
    default="local-lab",
)
```

"설정이니까 Variable"이라고 생각하지 않는다.

```text
deployment마다 달라지는 runtime value
→ Variable 후보

workflow definition과 함께 review/deploy되어야 하는 invariant
→ Dag code 후보
```

Variable을 과도하게 쓰면 source만 읽고 behavior를 이해하기 어려워진다. **실제 variability가 있는 값만 runtime
configuration으로 빼는 편이 단순하다.**

## 6. Connection: external-system access configuration

Connection은 external system에 접근하기 위한 configuration을 표현한다.

```text
conn_id
conn_type
host / port
login / credential / extra
```

가장 중요한 boundary:

```text
credential
!=
Param
!=
XCom
!=
log
```

Credential을 run input이나 task-to-task data channel에 넣지 않는다. Debugging 편의를 위해 출력하는 것도 피한다.

## 7. Logical role과 resolution backend는 다른 차원이다

Variable이나 Connection은 metadata DB에서 resolve될 수도 있고, environment나 external secrets backend에서 resolve될 수도
있다.

```text
logical role
Connection = external-system access configuration

resolution backend
environment / metadata DB / secrets backend / ...
```

따라서 "UI 목록에 row가 없으니 Connection이 아니다"라는 결론은 틀릴 수 있다.

이번 lab의 teaching Variable/Connection은 environment-backed다.
**어디에 저장되었는지와 어떤 책임의 값인지는 별도 질문**이다.

## 8. Worked mapping

다음 요구를 분류한다.

```text
1. trigger할 때 region을 고른다.
2. 10 GB 주문 data를 처리한다.
3. stage task가 downstream에 staged 위치를 넘긴다.
4. deployment마다 external API host가 다르다.
5. API token이 필요하다.
6. row count 1000 미만이면 pipeline을 실패시킨다.
```

| 요구 | owner/channel | 이유 |
| --- | --- | --- |
| region | Param | run마다 선택하는 logical input |
| 10 GB rows | external storage | actual business data |
| staged location | XCom | downstream이 data를 찾는 identifier |
| API host | Connection/runtime config | external endpoint |
| API token | Connection/secrets-backed config | credential |
| min row count | Dag code | workflow policy로 version review |

마지막 항목이 중요하다. Airflow에 Variable 기능이 있다는 이유만으로 모든 constant를 metadata/config surface로 옮기지
않는다.

## 9. Playground: 같은 run에서 owner를 직접 연결한다

사용할 Dag:

```text
lab/dags/exercises/u5_boundaries_starter.py
Dag ID: adudeck_u5_boundaries_starter
```

실행 전에 표를 채운다.

| 값 | 예상 owner |
| --- | --- |
| `region` | |
| fixture rows | |
| `dataset_path` | |
| `adudeck_environment` | |
| `adudeck_demo_api` | |
| Connection password | |

`standalone`을 시작한 뒤 `region=apac`으로 trigger한다.

```bash
bash lab/airflow.sh dags trigger \
  -c '{"region":"apac"}' \
  adudeck_u5_boundaries_starter
```

```bash
bash lab/scripts/snapshot.sh \
  adudeck_u5_boundaries_starter \
  '<RUN_ID>'
```

하나의 "task input"으로 보지 말고 다음 evidence를 연결한다.

```text
DagRun Param
XCom dataset identifier
external output rows
Variable value
Connection의 non-secret metadata
```

## 10. 두 variation만 수행한다

### Variation A — invalid Param

```bash
bash lab/airflow.sh dags trigger \
  -c '{"region":"north-pole"}' \
  adudeck_u5_boundaries_starter
```

예측한다.

```text
task body까지 도달하는가?
TaskInstance retry가 해결할 문제인가?
external output이 생겨야 하는가?
```

Input validation과 task runtime failure를 구분한다.

### Variation B — requirement change

다음 중 하나를 고른다.

```text
region이 이제 모든 deployment에서 항상 apac이다.
environment가 실제로는 source-controlled invariant다.
stage task가 dataset 전체를 return하도록 바꾸자는 제안이 있다.
```

기존 channel을 그대로 유지하지 말고 **owner가 바뀌었는지** 다시 판단한다.

## 11. Validation boundary

| Evidence | 검증하는 것 |
| --- | --- |
| source inspection | intended ownership |
| Param trigger/validation | run-input contract |
| snapshot/XCom evidence | orchestration metadata flow |
| output file | business data side effect |
| Variable/Connection resolution | runtime config/access config가 resolve됨 |

특히 environment-backed Variable/Connection이 resolve된다는 evidence와 metadata DB row가 존재한다는 evidence를 같은
것으로 취급하지 않는다.

## 12. 흔한 오해

### "값이 작으면 XCom, 크면 file"

크기보다 responsibility가 먼저다. Actual dataset storage와 orchestration metadata를 분리한다.

### "설정은 전부 Variable"

Source-controlled workflow policy는 Dag code가 더 명확할 수 있다.

### "Connection은 metadata DB row"

Connection은 logical access configuration이고 backend는 별도 차원이다.

### "credential도 Param으로 받으면 유연하다"

Run input과 secret/access configuration의 책임이 섞인다.

### "Task success면 output도 business-correct"

Control-plane state와 external data correctness는 별도 evidence다.

## 13. Practice

### A. Channel selection

다음 값을 owner/channel에 배치하고 이유를 한 문장씩 적는다.

```text
run별 country
warehouse table name
2 TB parquet dataset
warehouse credential
fraud threshold fixed in code review
deployment별 API endpoint
```

한 값에 여러 선택지가 가능하다면 **어떤 requirement가 선택을 바꾸는지** 적는다.

### B. Boundary repair

다음 design의 문제를 찾고 최소 수정한다.

```text
Param: api_token
Task return/XCom: 전체 DataFrame
Variable: 모든 business threshold
```

### C. Debugging

Task runtime에서 Connection은 resolve되지만 UI의 connection list에는 보이지 않는다. 어떤 hypothesis를 먼저 세울지
`logical role`과 `resolution backend`를 사용해 설명한다.

## Assessment checkpoint

다음을 독립적으로 할 수 있으면 통과한다.

1. Param / XCom / external storage / Variable / Connection / Dag code를 ownership과 lifecycle로 구분한다.
2. Credential이 task data channel로 흐르지 않게 설계한다.
3. Logical role과 resolution backend를 분리한다.
4. Requirement가 바뀌면 기존 channel을 외우지 않고 owner를 다시 판단한다.
