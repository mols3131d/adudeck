# 07. Recovery와 reprocessing: 어떤 logical work를 왜 다시 실행하는가

Airflow에서 "다시 돌린다"는 표현은 너무 넓다.

```text
retry
TaskInstance clear / re-run
backfill
catchup
```

네 mechanism 모두 반복 실행처럼 보이지만 runtime identity와 trigger가 다르다.

> **어떤 logical work를, 왜, 어느 runtime identity에서 다시 실행하려는가?**

이 질문으로 mechanism을 선택하고, 반복 실행 뒤 external state가 어떤 invariant로 수렴해야 하는지 함께 판단한다.

## 1. 네 mechanism을 한 표로 구분한다

| Mechanism | 대상 | 반복을 시작하는 주체 | 핵심 질문 |
| --- | --- | --- | --- |
| retry | 같은 logical TaskInstance의 next try | retry policy / scheduler | 아직 automatic retry가 남았는가? |
| clear / re-run | existing DagRun의 selected TaskInstance | 명시적 operator action | 이미 끝난 task를 다시 열어야 하는가? |
| backfill | 과거 logical intervals | explicit historical operation | 누락된 과거 runs를 만들어 처리해야 하는가? |
| catchup | 과거 timetable intervals | normal scheduling policy | scheduler가 과거 intervals를 자동 생성할 것인가? |

이 표를 command lookup table로 쓰지 않는다.

```text
"나는 ______ logical work를 다시 실행하려고 하므로 ______를 선택한다."
```

빈칸을 정확히 채우는 것이 목표다.

## 2. Retry와 clear/re-run은 "같은 task 재실행"이어도 원인이 다르다

Retry:

```text
same DagRun
same logical TaskInstance
try 1 failed
→ retry policy
→ try 2
```

Clear/re-run:

```text
existing DagRun
terminal TaskInstance
→ explicit clear
→ scheduler가 다시 실행 가능하게 평가
```

따라서 다음 두 문장은 다르다.

```text
failure policy가 next try를 허용했다
```

```text
operator가 terminal TaskInstance를 다시 실행 대상으로 만들었다
```

이미 terminal state가 된 task를 다시 계산하려는 문제를 retry count와 혼동하지 않는다.

## 3. Clear는 새 DagRun을 만드는 operation이 아니다

예:

```text
DagRun manual__A
prepare   success
transform success
publish   success
```

`transform`을 clear한다면 중심 identity는 같은 DagRun이다.

```text
same run
transform state reset
→ scheduler evaluates again
→ transform executes again
```

Airflow metadata state를 reset한다고 external side effect가 자동 rollback되는 것은 아니다.

```text
TaskInstance state reset
!=
warehouse rollback
!=
API request 취소
!=
file 삭제
```

이 때문에 clear/re-run에도 idempotence가 필요하다.

## 4. Downstream도 다시 실행해야 하는가

```text
prepare → transform → publish
```

`transform` output을 다시 만들었을 때:

```text
Case A
transform만 재검증하면 충분
→ transform only

Case B
새 transform output을 publish side effect까지 반영해야 함
→ transform + downstream
```

`tasks clear --downstream` 같은 option보다 중요한 것은 **dependency와 side-effect contract**다.

> upstream result가 바뀌었는데 기존 downstream success를 유지해도 final state가 여전히 일관적인가?

이 질문이 selector를 결정한다.

## 5. Backfill과 catchup은 existing TaskInstance recovery와 다르다

Backfill:

```text
historical logical intervals
→ explicit operation
→ historical DagRuns
```

Catchup:

```text
past timetable intervals
→ scheduler policy
→ historical runs may be created
```

예를 들어:

```text
8월 3일 기존 run의 transform만 재계산
→ clear/re-run 후보

8월 1~7일 runs가 아예 없고 과거 구간을 처리해야 함
→ backfill 후보

Dag를 활성화했을 때 scheduler가 과거 intervals를 따라가야 함
→ catchup policy
```

"과거 데이터를 다시 처리한다"는 한 문장만으로는 mechanism을 고를 수 없다.

## 6. 모든 repeated execution은 같은 invariant 질문으로 수렴한다

다음 retry를 생각한다.

```text
logical interval = 2026-08-27
try 1 = 2026-08-28 실행, failure
try 2 = 2026-08-30 실행, success
```

Wall-clock이 달라져도 logical work는 같다.

```python
# repeated logical work에서 위험할 수 있음
partition = datetime.now().date()
```

대신 logical date/data interval/run input에서 deterministic target을 만든다.

```text
retry
clear/re-run
backfill
```

어떤 mechanism이든 질문은 같다.

> 같은 logical input을 여러 번 실행해도 external state가 하나의 intended final state로 수렴하는가?

Append-only side effect라면 중복이 생길 수 있고, deterministic replace/upsert target이라면 수렴하기 쉽다.

## 7. Playground: task와 logical date로 대상을 좁히고 같은 run을 추적한다

먼저 `adudeck_observable_runtime`을 정상 실행한다.

```bash
bash lab/airflow.sh dags trigger \
  -c '{"failure_mode":"none"}' \
  adudeck_observable_runtime

bash lab/airflow.sh dags list-runs \
  adudeck_observable_runtime \
  -o table
```

`RUN_ID`와 `LOGICAL_DATE`를 기록하고 snapshot한다.

```bash
bash lab/scripts/snapshot.sh \
  adudeck_observable_runtime \
  '<RUN_ID>'
```

### Prediction

```text
transform만 clear하면 새 RUN_ID가 생기는가?
prepare도 다시 실행되는가?
transform execution evidence는 어떻게 달라지는가?
external output target은 같은 logical run을 유지하는가?
```

### Narrow selector + confirmation

Airflow 3.3.1의 `tasks clear`는 task regex와 start/end date로 범위를 좁힐 수 있지만 single `run_id` selector는 제공하지
않는다. 따라서 먼저 run 목록에서 해당 `LOGICAL_DATE`가 의도한 run을 유일하게 가리키는지 확인하고, confirmation target도
검토한다.

```bash
bash lab/airflow.sh tasks clear \
  adudeck_observable_runtime \
  -s '<LOGICAL_DATE>' \
  -e '<LOGICAL_DATE>' \
  -t '^transform$'
```

같은 logical date에 다른 run이 있거나 confirmation target이 예상보다 넓다면 승인하지 않는다. 이 disposable lab에서는
새로운 unique run을 만든 뒤 다시 시도하는 편이 가장 단순하다. 대상이 정확히 기대한 범위일 때만 `-y`를 사용한다.

```bash
bash lab/airflow.sh tasks clear \
  adudeck_observable_runtime \
  -s '<LOGICAL_DATE>' \
  -e '<LOGICAL_DATE>' \
  -t '^transform$' \
  -y
```

같은 `<RUN_ID>`를 다시 snapshot한다.

확인할 것:

```text
DagRun identity
selected TaskInstance state transition
new execution log
external output
```

Command가 성공했다는 사실보다 **의도한 logical work가 다시 실행되었다는 evidence**를 찾는다.

### Variation: downstream 포함

`transform`의 새 output을 publish까지 반영해야 한다고 가정한다.

```bash
bash lab/airflow.sh tasks clear \
  adudeck_observable_runtime \
  -s '<LOGICAL_DATE>' \
  -e '<LOGICAL_DATE>' \
  -t '^transform$' \
  -d
```

Confirmation target에서 `transform`과 `publish`가 선택되는지 확인한 뒤, 왜 `prepare`는 제외해도 되는지 설명한다.

## 8. Recovery decision trace

다음 case마다 첫 후보와 이유를 고른다.

### A

```text
transform try 1이 transient failure
retries가 아직 남아 있음
```

### B

```text
어제 run은 terminal
bug fix 후 그 run의 transform/publish만 재계산
```

### C

```text
지난달 일부 logical intervals의 DagRun 자체가 없음
```

### D

```text
오래된 start_date의 Dag를 활성화할 때 scheduler가 과거 intervals를 자동 생성해야 함
```

정답은 mechanism 이름 하나로 끝나지 않는다. **logical identity와 side-effect invariant**를 같이 적는다.

## 9. Version-sensitive note

이 chapter는 Apache Airflow 3.3.1을 기준으로 한다. `tasks clear` selector/option과 clear·rerun 시 Dag bundle version
behavior는 minor version에서 달라질 수 있으므로 실제 운영 전 current CLI/release note를 확인한다.

학습 목표는 option 암기가 아니라 `existing task state reset`과 `historical run creation`을 구분하는 것이다.

## 10. 흔한 오해

### "실패했으니 일단 clear"

Retry가 아직 진행 중인지 먼저 본다.

### "clear하면 새 DagRun이 생긴다"

Selected TaskInstance state를 existing run 안에서 다시 실행 가능하게 만드는 operation이다.

### "Airflow state를 clear하면 external write도 원복된다"

Metadata state와 business side effect는 별도다.

### "과거 데이터면 backfill과 catchup은 같다"

Explicit historical operation과 scheduling policy가 다르다.

### "재실행 날짜가 바뀌었으니 partition도 오늘 날짜로 바꾼다"

같은 logical work의 identity를 wall-clock으로 오염시키면 안 된다.

## 11. Practice

### A. Mechanism selection

다음 요구를 retry / clear-re-run / backfill / catchup에 연결하고, **existing run identity를 유지하는지**도 적는다.

```text
transient task failure
terminal task의 selective recomputation
누락된 historical range
scheduler의 normal historical scheduling policy
```

### B. Selector review

`transform`만 다시 계산해야 하는데 다음 command가 제안되었다.

```bash
airflow tasks clear my_dag -d -y
```

무엇이 너무 넓은지, 어떤 evidence를 먼저 보고 selector를 좁힐지 설명한다.

### C. Side-effect invariant

`publish`가 실행할 때마다 같은 partition에 row를 append한다. Retry와 clear/re-run에서 생길 문제를 설명하고,
logical input 기반 final invariant를 다시 설계한다.

## Assessment checkpoint

다음을 독립적으로 할 수 있으면 통과한다.

1. retry / clear-re-run / backfill / catchup을 logical-work identity로 구분한다.
2. Intended TaskInstance set을 좁게 선택하고 confirmation으로 범위를 검증한 뒤 same-run evidence를 연결한다.
3. Downstream을 함께 clear할지 side-effect contract로 판단한다.
4. Repeated execution에서 wall-clock과 logical input을 구분해 idempotent target을 설계한다.
