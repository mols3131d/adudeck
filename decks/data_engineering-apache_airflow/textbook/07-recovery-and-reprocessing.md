# 07. Recovery와 reprocessing: 같은 logical work를 왜 다시 실행하는가

Airflow에서 "다시 돌린다"는 말은 너무 모호하다.

다음 네 상황은 모두 반복 실행처럼 보이지만 같은 mechanism이 아니다.

```text
retry
TaskInstance clear / re-run
backfill
catchup
```

이들을 하나로 뭉개면 어떤 runtime identity가 유지되는지, 누가 반복 실행을 요청했는지, 어느 logical interval이 대상인지,
external side effect가 왜 다시 발생하는지를 설명할 수 없다.

이번 chapter의 목표는 command를 외우는 것이 아니라 다음 질문으로 recovery를 선택하는 것이다.

> **어떤 logical work를, 왜, 어느 runtime identity에서 다시 실행하려는가?**

그리고 어떤 mechanism을 선택하더라도 같은 logical work의 반복이 external state를 망가뜨리지 않도록 invariant를 유지한다.

## 1. 네 mechanism을 먼저 분리한다

### Retry

하나의 TaskInstance execution attempt가 실패했고 retry policy가 다음 try를 허용한다.

```text
same DagRun
same TaskInstance logical work
try 1 failed
→ retry policy
→ try 2
```

scheduler가 task의 retry policy를 바탕으로 다음 try를 진행한다.

### Clear / re-run

이미 존재하는 TaskInstance의 state를 명시적으로 clear해서 **다시 scheduling 가능한 상태로 돌린다.** Airflow 3.3.1 CLI는
`airflow tasks clear`를 "as if they never ran" 상태로 만드는 operation으로 설명한다.

```text
existing DagRun
existing TaskInstance
terminal state
→ operator/user clear
→ scheduler가 다시 실행 가능하게 평가
```

Airflow FAQ는 task instance를 clear하면 해당 DagRun이 다시 `running`으로 돌아갈 수 있다고 설명한다.

### Backfill

과거의 logical interval을 명시적으로 처리하기 위해 historical DagRun들을 만든다.

```text
historical interval A
historical interval B
historical interval C
→ explicit backfill operation
→ historical DagRuns
```

기존 TaskInstance 하나를 retry하는 문제가 아니라 **어떤 과거 logical runs를 존재하게 할 것인가**에 가깝다.

### Catchup

Dag가 활성화될 때 scheduler가 과거 scheduling interval을 자동으로 따라갈지 정하는 scheduling policy다.

```text
past timetable intervals
→ scheduler normal scheduling policy
→ catchup=True / False
```

명시적 장애 복구 command가 아니다.

## 2. identity를 기준으로 비교한다

| Mechanism | 기존 DagRun을 중심으로 하나? | 기존 TaskInstance를 다시 실행하나? | 새 historical DagRun을 만들 수 있나? | 주된 trigger |
| --- | --- | --- | --- | --- |
| retry | 예 | 같은 logical TaskInstance의 다음 try | 아니오 | task retry policy |
| clear / re-run | 예 | 예, selected TI state를 reset | 보통 목적 아님 | 명시적 operator/user action |
| backfill | historical logical intervals가 중심 | 생성된 runs의 tasks 실행 | 예 | 명시적 historical operation |
| catchup | timetable intervals가 중심 | 기존 TI 복구가 목적 아님 | scheduler가 과거 runs 생성 가능 | Dag scheduling policy |

이 표의 목적은 API를 분류하는 것이 아니다.

다음 문장을 완성할 수 있게 하는 것이다.

```text
"나는 ________ logical work를 다시 실행하려고 하므로 ________를 선택한다."
```

## 3. retry와 clear는 둘 다 같은 task를 다시 실행할 수 있지만 원인이 다르다

`transform` task에 `retries=1`이 있다고 하자.

첫 try가 실패한다.

```text
try 1
→ exception
→ retries remain
→ up_for_retry
→ try 2
```

이 과정에는 사람이 terminal state를 다시 열어 주는 operation이 필요하지 않다.

반대로 task가 이미 `success` 또는 terminal `failed`인 뒤 **명시적으로 다시 실행하고 싶다면** retry policy만 기다릴 수 없다.

```text
TaskInstance terminal state
→ clear
→ scheduler evaluation
→ task execution again
```

따라서 다음 두 문장은 다르다.

```text
"failure policy가 다음 try를 허용했다"

vs.

"operator가 기존 TaskInstance를 다시 실행 대상으로 만들었다"
```

## 4. clear는 새로운 DagRun을 만드는 operation이 아니다

예를 들어 다음 run이 이미 끝났다고 하자.

```text
DagRun: manual__A
prepare   success
transform success
publish   success
```

`transform`만 clear하면 conceptually 다음처럼 변한다.

```text
same DagRun: manual__A
prepare   success
transform <cleared / schedulable again>
publish   success
```

scheduler가 `transform`을 다시 실행한다.

중요한 것은 **새 DagRun B를 만든 것이 아니라 기존 DagRun A의 selected TaskInstance를 다시 실행 대상으로 만들었다는 것**이다.

Airflow는 clear된 task를 다시 진행하기 위해 finished DagRun을 `running`으로 되돌릴 수 있다.

## 5. downstream을 함께 clear할지 판단해야 한다

`transform` output을 `publish`가 소비한다고 하자.

```text
prepare -> transform -> publish
```

`transform`만 다시 실행하고 `publish`는 기존 success를 유지해도 되는가?

요구에 따라 다르다.

### transform만 재검증하려는 경우

```text
clear transform only
→ transform rerun
→ publish existing state 유지
```

### transform의 새 output을 publish까지 다시 반영해야 하는 경우

```text
clear transform + downstream
→ transform rerun
→ publish rerun
```

그래서 `tasks clear`에는 downstream task까지 포함하는 option이 있다.

```text
-d / --downstream
```

command option보다 중요한 판단은 다음이다.

> upstream output을 다시 만들었을 때 이미 success인 downstream side effect도 다시 수행해야 일관성이 회복되는가?

## 6. Observable Lab A: 성공한 TaskInstance를 다시 실행해 identity를 비교한다

`adudeck_observable_runtime`을 `failure_mode=none`으로 한 번 성공시킨다.

```bash
bash lab/airflow.sh dags trigger \
  -c '{"failure_mode":"none"}' \
  adudeck_observable_runtime
```

최근 run을 찾는다.

```bash
bash lab/airflow.sh dags list-runs adudeck_observable_runtime -o table
```

다음 두 값을 기록한다.

```text
RUN_ID
LOGICAL_DATE
```

그리고 snapshot을 남긴다.

```bash
bash lab/scripts/snapshot.sh \
  adudeck_observable_runtime \
  '<RUN_ID>'
```

실행 전 다음을 예측한다.

1. `transform`을 clear하면 새 DagRun ID가 생기는가?
2. `prepare`의 state는 다시 실행 대상으로 바뀌는가?
3. `transform`의 다음 execution에서는 log/try evidence가 어떻게 달라질까?
4. run-specific transformed output path는 같은 logical run을 가리키는가?

## 7. 정확한 대상부터 확인하고 clear한다

local learning environment에서도 broad clear를 습관화하지 않는다.

Airflow 3.3.1의 `tasks clear`는 `start-date`, `end-date`, task regex 등으로 대상을 좁힐 수 있다. 이번 lab에서는 방금 기록한
logical date와 `transform` task를 함께 지정한다.

먼저 confirmation prompt가 보여 주는 대상이 예상과 맞는지 확인한다.

```bash
bash lab/airflow.sh tasks clear \
  adudeck_observable_runtime \
  -s '<LOGICAL_DATE>' \
  -e '<LOGICAL_DATE>' \
  -t '^transform$'
```

예상한 TaskInstance가 아니라면 승인하지 않고 selector를 수정한다.

대상이 맞다는 것을 확인한 뒤 local disposable lab에서만 `-y`를 붙여 다시 실행할 수 있다.

```bash
bash lab/airflow.sh tasks clear \
  adudeck_observable_runtime \
  -s '<LOGICAL_DATE>' \
  -e '<LOGICAL_DATE>' \
  -t '^transform$' \
  -y
```

`-y`는 confirmation을 건너뛰므로 production habit으로 일반화하지 않는다.

## 8. 같은 DagRun에서 state가 다시 움직이는지 관찰한다

clear 직후와 scheduler가 다시 처리한 뒤 같은 `<RUN_ID>`를 snapshot한다.

```bash
bash lab/scripts/snapshot.sh \
  adudeck_observable_runtime \
  '<RUN_ID>'
```

UI, CLI, log, metadata에서 다음을 연결한다.

```text
DagRun identity는 같은가?
transform TaskInstance identity는 같은 logical work를 가리키는가?
state가 terminal → clear/schedulable → running → success로 다시 진행하는가?
새 task execution log가 생겼는가?
external transformed output은 어떤 path에 남는가?
```

여기서 관찰해야 할 핵심은 "command가 성공했다"가 아니다.

> **기존 runtime identity를 대상으로 state를 reset했기 때문에 scheduler가 같은 logical work를 다시 수행했다.**

## 9. Observable Lab B: downstream도 함께 re-run한다

이번에는 `transform`의 output을 `publish`까지 다시 반영해야 한다고 가정한다.

같은 run을 대상으로 `-d`를 추가한다.

```bash
bash lab/airflow.sh tasks clear \
  adudeck_observable_runtime \
  -s '<LOGICAL_DATE>' \
  -e '<LOGICAL_DATE>' \
  -t '^transform$' \
  -d
```

confirmation target에서 `transform`과 `publish`가 함께 선택되는지 확인한다.

승인 후 다음을 비교한다.

```text
prepare
transform
publish
DagRun
external output
```

질문한다.

- `prepare`는 왜 다시 실행할 필요가 없었는가?
- `publish`는 왜 이번에는 다시 실행했는가?
- 같은 `run_id`를 사용한 deterministic output path가 repeated execution에서 어떤 invariant를 만드는가?

## 10. clear/re-run과 side effect invariant

TaskInstance state를 clear한다고 external system의 side effect가 자동으로 rollback되는 것은 아니다.

```text
Airflow metadata state reset
!=
warehouse row 삭제
!=
API request 취소
!=
이미 생성한 object rollback
```

따라서 clear/re-run은 retry와 똑같은 질문을 다시 만든다.

> 같은 logical input을 다시 실행했을 때 external state가 어떤 final invariant로 수렴하는가?

예를 들어 publish가 deterministic run/partition key를 replace한다면 반복 실행 뒤에도 하나의 intended output으로 수렴할 수
있다.

반대로 append-only side effect라면 clear/re-run만으로 duplicate가 생길 수 있다.

## 11. wall-clock time으로 새 logical work를 만들지 않는다

clear는 나중에 수행될 수 있다.

```text
original execution: 2026-08-27
clear / re-run:     2026-08-30
```

하지만 같은 TaskInstance가 담당하는 logical input을 현재 wall-clock으로 바꾸면 안 된다.

```python
# retry / clear / backfill에서 위험할 수 있는 방향
partition = datetime.now().date()
```

같은 DagRun의 logical date/data interval 또는 명시된 logical input에서 deterministic target을 만들어야 한다.

이 invariant는 retry뿐 아니라 clear/re-run, backfill에서도 공통이다.

## 12. Backfill: 같은 DagRun을 다시 여는 것이 아니라 과거 runs를 만든다

Scheduling chapter에서 explicit backfill을 이미 관찰했다.

```text
historical timetable intervals
→ backfill create
→ historical DagRuns
```

clear와 비교한다.

```text
clear
existing run/task state를 다시 실행 대상으로 만듦

backfill
historical logical interval에 필요한 DagRuns를 명시적으로 생성/처리
```

따라서 "8월 1일~7일 partition이 애초에 처리되지 않았다"와 "8월 3일 DagRun의 transform만 다시 실행하고 싶다"는 서로 다른
문제다.

## 13. Catchup: recovery command가 아니라 scheduler policy다

`catchup=True`는 오래된 `start_date`부터 과거 interval을 scheduler가 따라갈 수 있게 한다.

이것은 terminal TaskInstance를 수동으로 복구하는 clear나, 명시적 historical operation인 backfill과 목적이 다르다.

```text
catchup
"normal scheduler가 과거 timetable intervals를 생성할까?"

backfill
"내가 이 historical range를 명시적으로 처리할까?"

clear
"이미 존재하는 run의 selected task state를 다시 열까?"

retry
"현재 TaskInstance failure policy가 다음 try를 허용할까?"
```

## 14. recovery decision trace

다음 증상을 순서대로 판단한다.

### Case A

```text
transform try 1이 transient API error로 실패했다.
retries=1이고 아직 retry가 남아 있다.
```

첫 후보: retry policy가 이미 같은 logical TaskInstance의 다음 try를 제공하는지 관찰한다.

### Case B

```text
어제 DagRun은 끝났지만 transform implementation bug를 고쳤고
그 run의 transform/publish만 다시 계산해야 한다.
```

첫 후보: exact existing run/task를 대상으로 clear/re-run이 적합한지 판단한다.

### Case C

```text
지난달 10일간의 scheduled intervals가 존재하지 않는다.
해당 historical data를 명시적으로 처리해야 한다.
```

첫 후보: backfill 대상 range와 기존 run 충돌을 확인한다.

### Case D

```text
새 Dag를 활성화할 때 start_date 이후 과거 interval을
normal scheduler가 자동으로 생성해야 한다.
```

첫 후보: catchup scheduling policy를 검토한다.

## 15. code version도 별도 판단 축이다

Airflow 3.3.1에는 cleared/rerun/backfilled task가 original Dag bundle version과 latest version 중 어느 쪽을 사용할지 제어하는
`rerun_with_latest_version` 설정이 있다. 기본/fallback은 operation에 따라 다를 수 있다.

이번 Basic chapter에서는 bundle version policy 자체를 깊게 다루지 않는다. 대신 다음 경계를 기억한다.

```text
"같은 logical work를 다시 실행한다"
!=
"반드시 동일한 source code version으로 실행한다"
```

bug fix 뒤 historical work를 다시 처리하는 운영에서는 **logical identity와 code version을 별도로 확인해야 한다.** Local lab의
관찰도 실제 log/source evidence를 기준으로 해석하고 source version을 추측하지 않는다.

## 16. 흔한 잘못된 mental model

### "retry와 clear는 둘 다 다시 실행하니 같다"

retry는 current TaskInstance retry policy의 다음 try이고, clear는 이미 존재하는 task state를 명시적으로 reset하는 operation이다.

### "clear하면 새 DagRun이 생긴다"

기존 DagRun의 selected TaskInstance를 다시 실행 가능하게 만드는 것이 핵심이다.

### "Task를 clear하면 external side effect도 원상복구된다"

Airflow metadata state와 external state는 별도다.

### "과거 data를 처리하려면 catchup=True로 바꾸면 된다"

명시적 historical processing은 backfill과 구분해서 판단한다.

### "clear 후에는 `datetime.now()`로 새 partition을 써도 된다"

같은 logical work의 re-run이라면 logical input identity를 유지해야 한다.

### "bug fix 후 clear하면 항상 새 code가 사용된다"

Airflow 3.3.1의 rerun bundle-version behavior는 설정/Dag policy에 따라 달라질 수 있으므로 실제 version policy를 확인한다.

## 17. Practice

### A. Classify

다음 요구에 가장 가까운 mechanism을 고르고 이유를 설명한다.

1. current run의 first attempt가 transient failure, retry가 남아 있음
2. terminal success였던 특정 task를 bug fix 후 다시 실행
3. 작년 12월 일별 intervals를 명시적으로 처리
4. 새 Dag activation 때 start_date 이후 missed schedule을 normal scheduler가 생성

후보:

```text
retry
clear / re-run
backfill
catchup
```

### B. Downstream judgment

```text
extract -> transform -> load
```

`transform` bug를 고친 뒤 clear하려 한다.

- `transform`만 clear하는 경우
- `transform` + downstream을 clear하는 경우

각각 어떤 business invariant를 전제로 하는지 설명한다.

### C. Side-effect repair

`publish`가 실행할 때마다 다음 file에 append한다.

```text
published-events.log
```

같은 DagRun을 clear/re-run하면 duplicate line이 생긴다. 같은 logical run에 대해 final state가 하나로 수렴하도록 output identity와
write strategy를 수정하는 방향을 설계한다.

### D. Diagnosis

clear를 실행했는데 기대한 task가 아니라 여러 날짜의 task가 선택되었다.

즉시 `-y`를 붙여 진행하지 않고 어떤 selector를 더 좁혀야 할지 설명한다.

## Assessment checkpoint

이번 chapter는 다음 과제를 독립적으로 수행할 수 있을 때 통과한다.

### 1. Recovery map

retry, clear/re-run, backfill, catchup을 다음 축에서 비교한다.

```text
누가 반복 실행을 시작하는가
기존 DagRun/TaskInstance identity가 어떻게 다뤄지는가
어떤 logical interval이 대상인가
external side effect가 왜 다시 발생할 수 있는가
```

### 2. Controlled re-run

local lab의 한 completed DagRun에서 selected TaskInstance를 정확히 좁혀 clear하고, 같은 run identity에서 state가 다시 진행되는
것을 UI/CLI/log/metadata/output evidence로 설명한다. 그 다음 downstream까지 포함하는 variation을 수행하거나, 포함하지 않아야
하는 이유를 business invariant로 정당화한다.

평가 기준:

- retry와 explicit clear의 control owner를 구분했는가?
- clear가 existing run/task state에 작용한다는 것을 evidence로 설명했는가?
- backfill/catchup을 clear와 혼동하지 않았는가?
- repeated execution에서 logical input을 wall-clock time과 분리했는가?
- external side effect가 metadata clear로 rollback되지 않음을 이해했는가?
- task selector와 downstream 범위를 무작정 넓히지 않았는가?

이 기준을 만족하면 U6의 핵심 outcome인 **반복 실행 mechanism을 logical work와 state identity에 맞게 선택하고, re-run에서도
side-effect invariant를 유지하는 능력**을 갖춘 것으로 본다.
