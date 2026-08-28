# 03. Task design: failure, retry, side effect를 직접 관찰하기

Airflow에서 graph가 보기 좋다고 workflow가 운영하기 좋은 것은 아니다.

실제 reliability는
**Task를 어떤 runtime boundary로 나누고, 각 TaskInstance의 재실행이 external system에 어떤 side effect를 남기는가**에서
크게 결정된다.

이 chapter에서는 `prepare -> transform -> publish` workflow에 의도적인 failure를 넣는다. 실패를 빨리 없애는 것이 목적이
아니다. `running`, `up_for_retry`, `failed`, `upstream_failed`, `success`를 직접 관찰하고, retry와 XCom과 external
output이 서로 어떤 관계인지 설명하는 것이 목적이다.

## 1. Task는 함수 분할 단위가 아니라 운영 단위다

일반 Python code에서 함수를 나누는 이유는 readability일 수 있다.

Airflow Task boundary에는 추가 의미가 생긴다.

```text
Task boundary
= state boundary
+ retry boundary
+ log boundary
+ dependency boundary
+ side-effect responsibility boundary
```

다음 두 설계를 비교한다.

```text
A. one_big_task
   extract + transform + load

B. extract -> transform -> load
```

A에서 load가 마지막에 실패하면 전체 TaskInstance를 다시 실행해야 할 수 있다.

B에서는 load만 독립적으로 retry할 수 있다. 대신 Task 수가 늘고 scheduling/runtime overhead와 data boundary를 관리해야
한다.

따라서 "함수를 최대한 잘게 쪼갠다"가 원칙이 아니다.

좋은 Task 후보는 보통 다음 질문에 의미 있는 답을 갖는다.

- 이 단계만 성공/실패로 관찰할 가치가 있는가?
- 이 단계만 retry할 가치가 있는가?
- logical input과 output contract를 설명할 수 있는가?
- external side effect의 책임이 명확한가?

## 2. TaskInstance state는 lifecycle evidence다

TaskInstance는 단순히 success/failed boolean이 아니다.

학습용으로 단순화한 흐름은 다음과 같다.

```text
scheduled
   |
   v
queued
   |
   v
running
   | \
   |  \
   |   +--------------------+
   v                        v
success                   failed attempt
                            |
                     retries remain?
                        /       \
                      yes       no
                       |         |
                       v         v
                up_for_retry   failed
                       |
                       v
                next scheduled try
```

dependency 때문에 실행되지 못한 downstream에는 `upstream_failed` 같은 state가 나타날 수 있다.

중요한 것은 state 이름을 암기하는 것이 아니라 다음 질문을 할 수 있는가다.

> 이 state는 어느 layer의 어떤 조건 때문에 생겼고, 다음 transition을 일으키려면 무엇이 달라져야 하는가?

## 3. Retry가 존재하는 순간 side effect가 핵심이 된다

Task가 external API에 요청하거나 table을 수정한다고 하자.

첫 실행에서 side effect는 성공했지만 Airflow가 success를 확정하기 전에 worker가 죽을 수 있다.

```text
try 1
  external write SUCCESS
  process crash
  Airflow success 기록 못 함

try 2
  same external write AGAIN
```

이때 "Airflow가 두 번 실행해서 duplicate가 생겼다"고만 말하면 설계 문제를 놓친다.

Airflow는 failure recovery를 위해 retry를 제공한다. business side effect가 retry-safe해야 한다.

### Idempotent 방향

예를 들어 data interval에서 deterministic partition key를 만든다.

```text
logical input: dt=2026-08-27

try 1 -> replace/upsert dt=2026-08-27
try 2 -> replace/upsert dt=2026-08-27

final invariant
"dt=2026-08-27 partition은 source snapshot과 일치한다"
```

완벽한 수학적 idempotence가 항상 가능한 것은 아니지만, **같은 logical input의 재실행이 어떤 결과로 수렴해야 하는지**를
먼저 정의해야 한다.

## 4. 실습 Dag의 구조를 읽는다

`lab/dags/observable_runtime.py`는 다음 workflow를 만든다.

```text
prepare -> transform -> publish
```

세 Task는 실제 dataset을 XCom에 싣지 않는다.

```text
prepare
  writes -> lab/output/<run>-manifest.json
  returns -> file path

transform
  receives -> file path via XCom
  reads -> manifest file
  writes -> transformed file
  returns -> transformed file path

publish
  receives -> transformed file path via XCom
  writes -> published file
```

즉 control/data boundary를 다음처럼 나눈다.

```text
Airflow metadata / XCom
        file identifier
              |
              v
Task A -----------------> Task B
  |                         |
  | actual data             | actual data
  v                         v
        lab/output files
```

이 pattern은 production에서 object storage나 warehouse를 쓰는 구조의 축소판이다.

## 5. failure mode를 이용해 state machine을 조작한다

Dag에는 `failure_mode` Param이 있다.

```text
none
  transform이 바로 성공

once
  transform try 1은 의도적으로 실패
  retry 후 try 2는 성공

always
  transform이 모든 try에서 실패
  retries를 소진한 뒤 terminal failed
```

`transform`은 `retries=1`이므로 최대 두 try를 관찰할 수 있다.

이 failure는 bug가 아니라 **state transition을 사람이 볼 수 있게 만드는 실험 control**이다.

## 6. Observable Lab A: `up_for_retry`를 놓치지 않고 잡는다

Airflow standalone을 실행하고 Dag를 unpause한다.

```bash
bash lab/airflow.sh standalone
```

별도 terminal:

```bash
bash lab/airflow.sh dags unpause adudeck_observable_runtime
```

### 실행 전에 prediction

`failure_mode=once`라면 다음을 예측한다.

```text
prepare
  success

transform
  try 1 running
  -> intentional error
  -> up_for_retry
  -> retry delay
  -> try 2 running
  -> success

publish
  transform이 성공하기 전에는 실행 불가
  -> eventually success

DagRun
  eventually success
```

특히 다음 두 질문의 답을 적고 시작한다.

1. transform의 첫 failure 순간 DagRun은 곧바로 terminal `failed`가 될까?
2. publish는 transform의 retry 대기 중에 실행될까?

### trigger

UI에서 `failure_mode=once`를 선택해 trigger한다.

CLI에서는 다음처럼 실행할 수 있다.

```bash
bash lab/airflow.sh dags trigger \
  -c '{"failure_mode":"once"}' \
  adudeck_observable_runtime
```

최근 run에서 `<RUN_ID>`를 찾는다.

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_runtime -o table
```

## 7. `up_for_retry` 동안 네 관측면을 동시에 본다

transform 첫 시도는 8초 동안 실행된 뒤 실패하고 retry delay 15초를 둔다. 일부러 사람이 중간 state를 잡을 수 있게 한
것이다.

### UI / Grid

transform이 실패한 직후 terminal failed로 끝나는지, retry state로 이동하는지 본다.

publish가 어떤 상태인지도 같이 본다.

### CLI

몇 초 간격으로 반복한다.

```bash
bash lab/airflow.sh tasks states-for-dag-run \
  adudeck_observable_runtime \
  '<RUN_ID>' \
  -o table
```

가능하면 다음 세 snapshot을 확보한다.

```text
A. transform=running, try 1
B. transform=up_for_retry
C. transform=running 또는 success, try 2
```

Timing 때문에 하나를 놓쳤다면 다시 새 run을 trigger한다. lab에서는 실패를 재현하는 비용이 작다.

### metadata probe

```bash
python lab/inspect_metadata.py \
  --dag-id adudeck_observable_runtime \
  --run-id '<RUN_ID>'
```

`task_instance`의 `state`, `try_number`, start/end timestamp를 본다.

Airflow 3에서는 try number가 task execution 도중 임의로 증가하는 counter라고 생각하지 않는다. 새 try가 scheduling될 때
구분되는 runtime identity의 일부로 해석하는 편이 안전하다.

### task log

transform log의 marker를 찾는다.

```text
[ADUDECK_OBSERVE] transform:start
[ADUDECK_OBSERVE] transform decision: failure_mode=once, try_number=1
intentional lab failure
```

다음 try에서는 `try_number=2`와 success path를 찾는다.

## 8. failure는 같은데 TaskInstance state가 다른 이유

첫 try에서 Python exception이 발생했다.

그런데 retry가 남았다면 TaskInstance의 의미는 다음과 같다.

```text
"한 번 실패했다"
!=
"이 TaskInstance의 logical work가 terminal failure다"
```

scheduler는 retry policy와 retry delay를 반영해 다음 try를 다시 실행 가능하게 만든다.

따라서 debugging에서 traceback만 보고 terminal outcome을 단정하면 안 된다.

```text
exception evidence
+
TaskInstance current state
+
retry policy / try_number
```

를 같이 봐야 한다.

## 9. Observable Lab B: terminal failure와 `upstream_failed`

이번에는 `failure_mode=always`로 새 DagRun을 만든다.

실행 전 prediction:

```text
prepare -> success
transform try 1 -> fail -> up_for_retry
transform try 2 -> fail -> terminal failed
publish -> upstream_failed
DagRun -> failed
```

trigger:

```bash
bash lab/airflow.sh dags trigger \
  -c '{"failure_mode":"always"}' \
  adudeck_observable_runtime
```

새 `<RUN_ID>`를 찾아 UI, CLI, metadata를 다시 본다.

### 핵심 질문

`publish` code에는 bug가 없다. 그런데 왜 publish는 success가 아닌가?

답은 publish의 user code를 보기 전에 dependency state에서 찾는다.

```text
transform = failed
        |
        v
publish dependency unsatisfied
        |
        v
publish = upstream_failed
```

이것이 state가 debugging search space를 줄여 주는 방식이다.

## 10. control-plane state와 external side effect를 비교한다

terminal failure run의 output을 본다.

```bash
find lab/output -maxdepth 1 -type f -print
```

`prepare`는 이미 성공했기 때문에 manifest file은 존재할 수 있다.

반면 `transform`은 성공 path까지 가지 못했으므로 transformed output이 없고 `publish`도 실행되지 않아 published output이
없을 수 있다.

이 상태를 다음처럼 정리한다.

```text
prepare TaskInstance = success
  -> manifest side effect 존재

transform TaskInstance = failed
  -> transformed success output 없음

publish TaskInstance = upstream_failed
  -> publish user code 자체가 시작되지 않음
```

workflow failure가 항상 "아무 side effect도 없었다"는 뜻은 아니다.

이 때문에 재실행 설계에서는 **부분적으로 성공한 external state를 어떻게 다룰 것인지**가 중요하다.

## 11. XCom은 data plane 자체가 아니라 orchestration metadata로 본다

TaskFlow code는 일반 Python function call처럼 보인다.

```python
publish(transform(prepare()))
```

하지만 runtime에서 세 Task가 한 call stack으로 실행되는 것은 아니다.

각 Task는 독립적인 TaskInstance이고 return value는 downstream dependency와 XCom을 통해 연결된다.

metadata probe를 다시 실행하면 `xcom` table의 row identity와 key도 볼 수 있다.

```bash
python lab/inspect_metadata.py \
  --dag-id adudeck_observable_runtime \
  --run-id '<RUN_ID>'
```

probe는 XCom `value`를 출력하지 않는다. 이 실습에서 확인하려는 것은
**어떤 Task가 어떤 run에서 XCom record를 만들었는가**다.

실제 값은 task log와 code를 함께 해석한다.

```text
XCom
  "이 transformed output은 어디 있는가?"
  -> path / identifier

external storage
  "실제 transformed data는 무엇인가?"
  -> file contents
```

production에서는 file 대신 S3 URI, table name, object version, row count 같은 작은 metadata를 전달하는 방식으로 확장할
수 있다.

## 12. 왜 큰 DataFrame을 XCom에 넣지 않는가

다음 두 방식을 비교한다.

```text
A.
Task A return -> 2GB DataFrame -> XCom -> Task B

B.
Task A writes -> object storage
Task A return -> object key
Task B reads -> object storage
```

B는 data storage responsibility와 orchestration metadata responsibility를 분리한다.

Task가 다른 process/machine에서 실행될 수 있는 시스템에서는 이 boundary가 더 중요해진다.

또한 Airflow metadata DB를 business dataset 저장소로 오해하지 않게 된다.

## 13. Observable Modification Lab: retry-unsafe side effect를 직접 만든다

지금 `transform`은 intentional failure를 **성공 output을 쓰기 전에** 발생시킨다.

따라서 첫 실패가 business output duplicate를 만들지는 않는다.

이번에는 일부러 나쁜 코드를 만들어 본다. `transform` 안에서 failure check 전에 다음과 비슷한 append side effect를
추가한다.

```python
journal_path = OUTPUT_DIR / "transform-business-events.log"
with journal_path.open("a") as file:
    file.write(f"{snapshot['run_id']} transformed\n")
```

`failure_mode=once`로 새 run을 trigger한다.

### Prediction

- transform try 1은 append 후 실패한다.
- try 2도 같은 logical work에 대해 append한다.
- 최종 DagRun은 success일 수 있지만 business event는 두 줄 남을 수 있다.

실제로 확인한다.

```bash
cat lab/output/transform-business-events.log
```

Airflow state만 보면 최종 transform은 success다. 그러나 external side effect는 duplicate다.

이 실험은 중요한 사실을 보여준다.

> **TaskInstance success는 business side effect가 exactly-once였다는 증명이 아니다.**

실습이 끝나면 이 temporary modification을 되돌린다.

## 14. retry-safe한 invariant로 고친다

append 대신 logical run/partition에 대응하는 deterministic location을 사용한다고 하자.

```text
output/<logical-key>/transformed.json
```

그리고 같은 input으로 retry하면 같은 logical output을 overwrite하거나 upsert한다.

검증할 invariant를 먼저 문장으로 쓴다.

```text
"이 TaskInstance가 몇 번 실행되더라도 최종 transformed output은
해당 logical input의 최신 올바른 snapshot 하나를 표현한다."
```

그 다음 implementation이 invariant를 만족하는지 본다.

좋은 reliability 설계는 `retries=10` 같은 숫자부터 시작하지 않는다.

```text
failure model
   ↓
side-effect invariant
   ↓
retry-safe implementation
   ↓
retry policy
```

순서가 더 중요하다.

## 15. 모든 failure를 retry하면 안 된다

retry가 회복 가능성을 높이는 failure가 있다.

```text
network timeout
external service temporary 5xx
short-lived connection failure
```

시간이 지나도 같은 input에서 똑같이 실패할 가능성이 높은 경우도 있다.

```text
SQL syntax error
schema mismatch
missing required configuration
deterministic code bug
```

따라서 retry policy를 읽을 때 질문한다.

> 이 failure의 원인이 시간이 지나거나 새 execution attempt를 얻으면 달라질 수 있는가?

그렇지 않다면 retry는 recovery가 아니라 error repetition이 될 수 있다.

## 16. State-based debugging matrix

| 관측 state | 먼저 의심할 범위 | 아직 우선순위가 낮은 것 |
| --- | --- | --- |
| Dag가 목록에 없음 | parse/import/Dag Processor | task business logic |
| Task가 `queued`에 오래 있음 | execution capacity, pool, executor path | task 내부 마지막 SQL |
| Task가 `up_for_retry` | exception + retry policy + side-effect safety | Dag 전체 재작성 |
| Task가 `failed` | terminal task failure evidence | downstream code부터 보기 |
| downstream `upstream_failed` | upstream terminal state | downstream function bug부터 보기 |
| Task `success`, output 이상 | external side effect/invariant | scheduler가 실행 안 했다고 가정 |

state는 UI decoration이 아니라 **다음 investigation의 검색 공간을 줄이는 index**다.

## 17. Task boundary checklist

새 Task를 설계할 때 다음 질문에 답한다.

1. logical input은 무엇인가?
2. external side effect는 무엇인가?
3. output contract는 data 자체인가, identifier/metadata인가?
4. 같은 logical input으로 retry하면 안전한가?
5. 이 단계만 독립 retry할 가치가 있는가?
6. 이 단계만 독립적으로 성공/실패 관찰할 가치가 있는가?
7. upstream failure가 downstream에 어떤 state로 전파되어야 하는가?
8. success state 외에 어떤 external evidence로 결과를 검증할 것인가?

답이 불명확하면 Python code부터 쓰기 전에 boundary를 다시 그린다.

## Practice

### 1. Retry timeline reconstruction

`failure_mode=once` run 하나를 골라 다음 timeline을 실제 timestamp와 try number로 채운다.

```text
prepare success
      |
      v
transform try 1 start
      |
      v
transform try 1 error
      |
      v
up_for_retry
      |
      v
transform try 2 start
      |
      v
transform success
      |
      v
publish success
```

Evidence source도 각 줄 옆에 적는다: UI / CLI / metadata / log / output.

### 2. Terminal failure diagnosis

`failure_mode=always` run에서 publish가 `upstream_failed`인 이유를 publish code를 인용하지 않고 설명한다.

### 3. XCom vs external storage

다음을 XCom metadata와 external storage 중 어디에 둘지 결정한다.

- object key 문자열
- row count 정수
- 4GB parquet bytes
- warehouse table name
- 500MB pandas DataFrame
- validation result `{passed: true, invalid_rows: 3}`

### 4. Idempotence repair

다음 load를 retry-safe하게 만들기 위한 invariant와 구현 전략을 각각 적는다.

```text
INSERT INTO orders SELECT ...
```

가능한 전략 예시는 partition overwrite, deterministic key 기반 MERGE/upsert, staging + atomic replace 등이지만 어느 것을
선택할지는 storage semantics에 따라 달라진다.

### 5. Cross-layer contradiction

다음 관측을 받았다.

```text
TaskInstance state = success
warehouse rows = expected보다 2배
```

왜 scheduler failure만 의심하면 안 되는지 설명하고, 어떤 side-effect evidence를 추가로 모을지 적는다.

## Checkpoint

다음을 설명할 수 있으면 core foundation을 통과한 것이다.

> Airflow reliability는 retry 횟수를 늘리는 데서 생기지 않는다. Task를 의미 있는 runtime/state boundary로 나누고, 같은
> logical input의 재실행이 external side effect를 망가뜨리지 않도록 invariant를 설계해야 한다. UI의 state, TaskInstance
> try, XCom metadata, task log, 실제 output을 함께 봐야 그 invariant가 지켜졌는지 판단할 수 있다.

## References

- [Tasks](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/tasks.html)
- [XComs](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/xcoms.html)
- [Architecture Overview — Workloads and Control Flow](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/overview.html)
- [CLI Reference — task states](https://airflow.apache.org/docs/apache-airflow/stable/cli-and-env-variables-ref.html)
