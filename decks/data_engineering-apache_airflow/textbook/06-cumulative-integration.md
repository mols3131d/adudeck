# 06. Cumulative integration: 최소 evidence로 작은 workflow를 설명한다

이 chapter는 새로운 Airflow 기능을 추가하지 않는다. U1~U6에서 배운 개념을 **덜 구조화된 한 문제에 통합**하는
cumulative assessment다.

성공 기준은 Dag가 초록색이 되는 것이 아니다.

> **의도 → prediction → runtime evidence → failure classification → change → re-validation**을 자신의 workflow로 설명한다.

## 1. 모든 evidence를 모으지 말고 cheapest discriminating evidence를 고른다

지금까지 사용한 surface:

```text
source / import
Dag/task discovery
local tasks test / dags test
scheduler-backed DagRun / TaskInstance
UI / CLI
task/component log
read-only metadata
external output
```

Debugging 순서는 보통 더 단순하다.

```text
source/import
→ discovery
→ run/scheduling
→ dependency/state
→ task runtime
→ external side effect
```

현재 hypothesis를 구분할 수 없는 evidence를 습관적으로 모두 수집하지 않는다.

## 2. Assessment scenario

작은 주문 batch workflow를 만든다.

```text
input
- manual trigger에서 region 선택: all / apac / emea
- source: lab/fixtures/orders.jsonl

workflow
stage → validate → publish

requirements
- 세 step은 독립 state/log가 필요한 Task
- task 사이에는 dataset 자체가 아니라 identifier 전달
- invalid region은 task business logic 전에 거부
- validate는 한 번 실패 후 retry되는 실험 가능
- repeated execution에도 publish output이 duplicate로 누적되지 않음
```

Production storage나 distributed deployment는 범위 밖이다. Local Airflow 3.3.1에서 **runtime mechanism을 설명할 수 있는가**를
평가한다.

## 3. 구현 전에 execution contract를 쓴다

다음 표를 먼저 채운다.

| 항목 | 내 설계 |
| --- | --- |
| DagRun input | |
| stage logical output | |
| task 사이 XCom value | |
| actual business data 위치 | |
| validate failure condition | |
| publish side-effect invariant | |
| retry/re-run에서 유지할 logical identity | |

특히 invariant를 code보다 먼저 정한다.

```text
나쁜 방향
매 실행마다 append

더 나은 방향
same logical run/input → deterministic target → replace/upsert-like final state
```

정답 구현이 하나라는 뜻이 아니다. **Repeated execution 뒤 무엇이 true여야 하는지** 먼저 말할 수 있어야 한다.

## 4. Graph와 value ownership을 설계한다

```text
stage → validate → publish
```

각 Task의 이유를 한 문장씩 쓴다.

```text
stage
→ source selection + dataset materialization responsibility

validate
→ independent failure/retry/log boundary

publish
→ final external side-effect responsibility
```

Value channel도 표시한다.

```text
region
→ Param

staged rows
→ external file

stage → validate
→ file path through XCom/TaskFlow

validate → publish
→ validated identifier / small metadata
```

Task count나 API 사용 자체가 평가 대상이 아니다. **boundary가 requirement와 맞는가**가 평가 대상이다.

## 5. Evidence는 boundary 순서로 만든다

### A. Parse/discovery

Scheduler를 보기 전에 확인한다.

```text
source가 import되는가?
Dag ID가 발견되는가?
expected task graph가 보이는가?
```

실패하면 retry나 external output을 조사하지 않는다.

### B. Normal run prediction

`region=apac` trigger 전에 적는다.

```text
예상 DagRun:
TaskInstance 수:
task order:
final states:
external output:
```

실행 후 prediction과 실제 evidence를 비교한다.

### C. Retry experiment

`validate`의 첫 try를 의도적으로 실패시키고 다음 try에서 성공하게 한다.

예측:

```text
첫 exception 뒤 DagRun이 바로 terminal인가?
publish가 retry 대기 중 실행되는가?
try 1/2가 같은 logical dataset을 읽는가?
```

UI/CLI/log 중 **필요한 surface만** 골라 state transition을 설명한다.

### D. Side-effect repair

Publish를 잠시 retry-unsafe하게 만들고 duplicate가 가능한 causal chain을 확인한다.

```text
write success
→ task completion 전 failure
→ retry
→ same logical work
→ duplicate side effect
```

그 뒤 deterministic target으로 수정하고 final invariant를 다시 검증한다.

### E. Invalid Param comparison

`region=north-pole`을 넣어 input validation failure와 `validate` task exception을 비교한다.

| 질문 | invalid Param | task failure |
| --- | --- | --- |
| failure boundary | | |
| task body까지 도달 | | |
| retry가 해결 수단인가 | | |
| first evidence | | |

## 6. Recovery judgment까지 연결한다

같은 workflow에서 다음 상황을 분류한다.

```text
A. current TaskInstance의 transient failure
B. terminal existing task를 bug fix 후 selective recomputation
C. 누락된 historical logical intervals
D. scheduler가 past intervals를 normal policy로 생성
```

후보:

```text
retry
clear / re-run
backfill
catchup
```

Mechanism 이름만 쓰지 않는다.

```text
대상 logical work
existing/new DagRun identity
반복 실행 이유
side-effect invariant
```

네 항목을 같이 적는다.

## 7. Diagnosis challenge

다음 symptom마다 **첫 evidence 하나**와 다음 단계로 넘어갈 조건을 적는다.

### Case A

```text
dags list --local에서 Dag가 보이지 않는다.
```

### Case B

```text
Dag는 보이지만 기대한 run이 진행되지 않는다.
```

### Case C

```text
stage=success
validate=failed
publish=upstream_failed
```

### Case D

```text
모든 TaskInstance=success
published output row count는 예상과 다름
```

좋은 답은 "UI, CLI, log, DB를 전부 본다"가 아니다.

```text
hypothesis
→ cheapest evidence
→ finding
→ next action
```

형태로 search space를 줄인다.

## 8. 최종 제출물

Code 외에 다음 네 evidence artifact만 남긴다.

### 1. Execution map

```text
source
→ parse/discovery
→ DagRun
→ TaskInstance transitions
→ external output
```

실제 `dag_id`, `run_id`, `task_id`를 사용한다.

### 2. Ownership map

```text
Param
XCom
external data
runtime/access configuration이 필요할 경우의 owner
source-controlled policy
```

### 3. Failure + recovery trace

의도적 failure 하나를 골라 다음을 연결한다.

```text
symptom
→ state/evidence
→ retry 또는 recovery mechanism
→ same logical work 여부
```

### 4. Side-effect invariant

수정 전/후 repeated execution에서 final state가 어떻게 달라지는지 실제 output으로 검증한다.

## 9. Rubric

| Outcome | 통과 evidence | 미통과 신호 |
| --- | --- | --- |
| runtime model | Dag/Task와 DagRun/TI identity를 구분 | 모두 "실행"으로 뭉갬 |
| authoring/loading | parse failure와 task failure를 다른 surface에서 진단 | retry로 import error를 해결하려 함 |
| time/recovery | logical time과 wall-clock, retry/clear/backfill/catchup 구분 | `now()`로 re-run partition 결정 |
| task lifecycle | exception + retry policy + current state를 함께 해석 | 첫 exception=terminal failure |
| data/config | Param/XCom/data/config/credential responsibility 구분 | 모든 값을 하나의 channel로 전달 |
| diagnosis | cheapest discriminating evidence부터 선택 | 모든 surface를 무조건 수집 |
| side effect | repeated logical work의 invariant를 검증 | green state만으로 correctness 주장 |

모든 항목을 완벽한 prose로 작성할 필요는 없다. **판단 근거와 evidence가 재현 가능하면 된다.**

## 10. Final checkpoint

다음을 도움 없이 수행하면 Basic cumulative path를 통과한다.

```text
작은 workflow 설계
→ boundary와 state prediction
→ parse/discovery 확인
→ scheduler-backed execution
→ intentional failure
→ minimal evidence diagnosis
→ recovery/reprocessing 판단
→ side-effect repair
→ re-validation
```

완료 판정은 file existence나 command success가 아니라 **설명 가능한 competence**를 기준으로 한다.
