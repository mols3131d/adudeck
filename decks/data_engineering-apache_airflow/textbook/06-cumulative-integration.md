# 06. Cumulative integration: 작은 batch workflow를 evidence로 설명하기

앞 chapter들은 Airflow의 서로 다른 mechanism을 분리해서 다뤘다.

```text
Dag / Task definition과 runtime identity
schedule / data interval / wall-clock time
TaskInstance state / retry / side effect
Dag authoring / loading
Params / XCom / external data / Variable / Connection
```

하지만 실제 debugging과 설계에서는 이 개념들이 동시에 나타난다.

이번 chapter는 새로운 기능을 많이 가르치는 chapter가 아니다. **지금까지 배운 개념을 덜 구조화된 문제에 적용하고, 작은 workflow를 설계·실행·실패·재처리한 뒤 evidence로 설명하는 cumulative assessment**다.

성공 기준은 Dag가 초록색이 되는 것이 아니다.

> 무엇을 의도했고, 어떤 state를 예상했고, 실제로 무엇을 관찰했으며, 실패가 어느 layer에서 발생했고, 수정 뒤 어떤 invariant가 회복되었는지 설명할 수 있어야 한다.

## 1. 이번에는 verification ladder를 스스로 선택한다

앞에서는 command 순서를 많이 제공했다. 이번에는 필요한 evidence를 스스로 선택한다.

사용 가능한 관측면은 이미 알고 있다.

```text
source / import surface
Dag/task discovery
local tasks test / dags test
scheduler-backed DagRun / TaskInstance
UI / Grid
CLI snapshots
component/task logs
read-only metadata probe
external output
```

모든 문제에서 모든 관측면을 열 필요는 없다.

좋은 diagnosis는 evidence를 많이 모으는 것이 아니라 **현재 hypothesis를 구분할 수 있는 가장 싼 evidence부터 선택하는 것**이다.

예를 들어 Dag가 아예 discovery되지 않는다면 output file부터 찾는 것은 순서가 잘못되었다.

```text
source/import
→ discovery
→ scheduling/run
→ dependency/state
→ task runtime
→ external side effect
```

증상이 어느 boundary까지 도달했는지 좁히면서 내려간다.

## 2. Assessment scenario

작은 주문 batch workflow를 만든다.

요구사항은 다음과 같다.

```text
입력
- manual trigger에서 region을 선택한다: all / apac / emea
- business source는 lab/fixtures/orders.jsonl이다

workflow
- stage: 선택한 region의 주문을 run-specific output file에 저장한다
- validate: 최소 한 건 이상의 row가 있는지 검증한다
- publish: validated dataset을 published output으로 만든다

운영 요구
- stage / validate / publish는 독립 state와 log가 필요하다
- task 사이에는 actual rows가 아니라 dataset identifier를 전달한다
- invalid region은 task runtime까지 들어가기 전에 거부되어야 한다
- validate는 의도적으로 한 번 실패시키는 실험이 가능해야 한다
- retry 뒤 같은 logical run이 중복 append를 만들지 않도록 publish side effect를 설계한다
```

production-grade storage나 credential integration을 구현할 필요는 없다. 이번 평가의 범위는 **local Airflow 3.3.1에서 mechanism과 state를 설명하는 것**이다.

## 3. 시작점

새 framework를 만들지 않는다. 이미 있는 starter와 reference Dag를 학습 자산으로 사용한다.

다음을 비교한다.

```text
lab/dags/exercises/u2_authoring_starter.py
lab/dags/exercises/u5_boundaries_starter.py
lab/dags/observable_runtime.py
```

권장 방식은 `u2_authoring_starter.py`를 local working copy에서 별도 exercise file로 복사하고 Dag ID를 바꾼 뒤 필요한 책임만 추가하는 것이다.

예:

```text
lab/dags/exercises/u7_integration_work.py
Dag ID: adudeck_u7_integration_work
```

이 filename과 ID는 assessment work를 reference material과 구분하기 위한 local convention일 뿐 repository-wide 표준이 아니다.

## 4. Work 1: code보다 먼저 execution contract를 쓴다

구현 전에 다음 표를 채운다.

| 항목 | 내 설계 |
| --- | --- |
| DagRun input | |
| stage의 logical output | |
| validate의 failure condition | |
| task 사이 XCom value | |
| actual business data 위치 | |
| publish side-effect invariant | |
| retry에서 유지되어야 할 logical identity | |

특히 publish invariant를 먼저 적는다.

나쁜 예:

```text
publish가 실행될 때마다 file에 한 줄 append한다
```

retry가 일어나면 같은 logical work가 여러 줄을 만들 수 있다.

더 나은 방향의 예:

```text
같은 DagRun / logical input에 대해 deterministic output path를 replace한다
```

완성 code보다 **재실행 뒤 final state가 어떤 조건을 만족해야 하는지**가 먼저다.

## 5. Work 2: graph와 boundary를 설계한다

목표 graph는 개념적으로 다음과 같다.

```text
stage -> validate -> publish
```

각 Task가 필요한 이유를 한 문장씩 쓴다.

다음 식으로 설명할 수 있어야 한다.

```text
stage
= source selection + external dataset materialization boundary

validate
= independent validation state / retry / log boundary

publish
= external side-effect responsibility boundary
```

"세 단계라서 Task 세 개"는 충분한 설명이 아니다.

그 다음 각 값의 channel을 표시한다.

```text
region
→ Param

staged dataset
→ external file

stage -> validate
→ staged file path via TaskFlow/XCom

validate -> publish
→ validated file path or small validation metadata
```

credential은 이번 scenario에 필요하지 않지만, 만약 external API를 추가한다면 Connection 책임으로 확장해야 한다는 점을 설명할 수 있어야 한다.

## 6. Work 3: parse/load evidence부터 만든다

scheduler를 켜기 전에 source가 definition으로 성립하는지 확인한다.

어떤 command를 쓸지는 스스로 선택하되 최소한 다음 질문에 답해야 한다.

```text
source file은 존재하는가?
local import error는 없는가?
Dag ID가 discovery되는가?
expected task graph가 보이는가?
```

여기서 failure가 나면 scheduler retry나 task output을 조사하지 않는다.

문제를 수정한 뒤 **어떤 evidence가 바뀌었는지** 기록한다.

## 7. Work 4: scheduler-backed run 전에 state를 예측한다

`region=apac`의 정상 run을 trigger하기 전에 다음을 적는다.

```text
DagRun 수:
TaskInstance 수:
예상 task order:
각 task의 final state:
생길 external output:
```

그리고 실제 run을 trigger한다.

관찰 뒤 prediction과 실제를 비교한다.

다른 intermediate state가 보였다면 "틀렸다"로 끝내지 않는다. dependency, scheduler timing, task execution time을 이용해 차이를 설명한다.

## 8. Work 5: validation retry를 관찰한다

`validate`가 첫 try에서 의도적으로 실패하고 다음 try에서 성공하도록 작은 experiment control을 만든다.

구현 방식은 자유지만 다음 조건을 만족해야 한다.

```text
try 1
→ validation failure
→ retry 가능한 state

try 2
→ 같은 logical input을 다시 검증
→ success

publish
→ validation이 성공한 뒤에만 실행
```

실행 전에 예측한다.

- 첫 Python exception 뒤 DagRun이 즉시 terminal failed가 될까?
- publish가 retry 대기 중에 실행될까?
- try 1과 try 2가 읽는 logical dataset path가 달라져야 할까?

실제 UI/CLI/log에서 evidence를 확보한다.

## 9. Work 6: idempotence를 일부러 깨뜨리고 수리한다

이번에는 publish side effect를 잠시 retry-unsafe하게 만든다.

예를 들어 같은 run에 대해 append-only journal을 남기도록 만들 수 있다.

```text
<run_id> published
```

publish task가 side effect를 만든 뒤 failure하도록 실험하면 retry에서 duplicate entry가 생길 수 있다.

이 실험의 목적은 duplicate를 만드는 것이 아니라 다음 causal chain을 설명하는 것이다.

```text
external write success
→ task completion 기록 전 failure
→ retry
→ same logical work executes again
→ non-idempotent side effect duplicated
```

그 다음 deterministic output identity 또는 replace/upsert-like behavior로 수정한다.

수정 전과 후의 invariant를 비교한다.

```text
before
same logical run을 두 번 실행하면 output이 누적될 수 있음

after
same logical run의 반복 실행이 하나의 intended final state로 수렴
```

## 10. Work 7: invalid Param과 task failure를 비교한다

`region=north-pole`처럼 schema에 없는 input을 사용한다.

먼저 예상한다.

```text
DagRun 생성 여부:
TaskInstance 생성/실행 여부:
external output 생성 여부:
```

그 다음 validation failure를 관찰한다.

이 실패를 앞의 `validate` task exception과 비교한다.

| 질문 | invalid Param | task validation failure |
| --- | --- | --- |
| failure layer | | |
| DagRun/task runtime까지 도달했는가 | | |
| retry policy가 해결 수단인가 | | |
| 주요 evidence surface | | |

## 11. Work 8: historical/reprocessing 판단

이 workflow를 특정 logical interval을 처리하는 scheduled batch라고 가정한다.

다음 상황을 비교한다.

```text
A. 한 TaskInstance의 transient failure
B. terminal failed TaskInstance를 다시 실행
C. 과거 logical interval 여러 개를 처리
D. scheduler가 과거 interval을 자동 생성
```

다음 후보를 연결한다.

```text
retry
clear / re-run
backfill
catchup
```

API/command 이름을 외우는 것이 목표가 아니다. 각 mechanism이 **어떤 logical work를 왜 반복하는지**를 설명한다.

그리고 어떤 방식이든 external side effect invariant가 유지되어야 하는 이유를 적는다.

## 12. Diagnosis challenge

다음 증상 네 개를 받았다고 하자.

### Case A

```text
dags list --local에서 Dag가 보이지 않는다.
```

### Case B

```text
Dag는 보이지만 trigger한 run이 실행되지 않는다.
```

### Case C

```text
stage=success, validate=failed, publish=upstream_failed
```

### Case D

```text
모든 TaskInstance=success인데 published business output이 expected row count와 다르다.
```

각 case에서 가장 먼저 확인할 evidence를 하나 선택하고, 다음으로 이동할 조건을 적는다.

좋은 답은 "UI, CLI, log, DB를 전부 본다"가 아니다.

예:

```text
Case A
first: local import/discovery surface
because: DagRun 이전 layer가 성립했는지 먼저 확인해야 함
next: import가 정상인데 discovery되지 않을 때 Dag definition/export 조건 확인
```

## 13. 최종 제출물

이번 assessment의 제출물은 code만이 아니다.

다음 다섯 항목을 남긴다.

### 1. Execution map

```text
source
→ parse/load
→ DagRun
→ TaskInstance state transitions
→ external side effect
```

자신의 실제 Dag ID/run ID/task ID를 사용해 설명한다.

### 2. Value ownership map

```text
Param
XCom
external data
runtime config / Connection이 필요해질 경우의 owner
version-controlled policy
```

### 3. Failure trace

의도적인 retry 또는 terminal failure 하나를 골라 state transition과 log evidence를 연결한다.

### 4. Side-effect invariant

retry/re-run 전후에 어떤 property가 유지되어야 하는지 쓰고 실제 output으로 검증한다.

### 5. Diagnosis note

발생한 문제 하나를 다음 형태로 정리한다.

```text
symptom
→ first hypothesis
→ cheapest discriminating evidence
→ finding
→ change
→ re-validation evidence
```

## 14. Rubric

각 항목은 "command를 실행했는가"가 아니라 explanation과 evidence로 판단한다.

### Runtime model

통과:
- Dag/Task definition과 DagRun/TaskInstance를 구분한다.
- 같은 runtime identity를 두 개 이상의 observation surface에서 연결한다.

미통과:
- file, Dag, run, task execution을 하나의 "실행"으로 설명한다.

### Authoring/loading

통과:
- parse/load failure와 task runtime failure를 구분한다.
- source existence, local discovery, local test, scheduler-backed run의 evidence strength를 구분한다.

미통과:
- `dags test` 성공만으로 scheduler-backed runtime을 증명했다고 주장한다.

### Time/reprocessing

통과:
- logical work와 wall-clock execution을 분리한다.
- retry, re-run, backfill, catchup을 목적에 따라 구분한다.

미통과:
- 재실행 시 `now()`를 기준으로 다른 partition을 선택해도 된다고 본다.

### Task lifecycle

통과:
- exception, retry policy, current TaskInstance state를 함께 해석한다.
- downstream `upstream_failed`를 dependency evidence로 설명한다.

미통과:
- 첫 exception을 terminal DagRun failure와 동일시한다.

### Data/config boundary

통과:
- Param, XCom, business data, runtime config, Connection, source policy를 responsibility로 구분한다.
- credential을 task data channel이나 log로 보내지 않는다.

미통과:
- "작은 값/큰 값"만으로 channel을 결정한다.

### Reliability

통과:
- repeated logical work에 대해 side-effect invariant를 정의한다.
- retry-unsafe behavior를 evidence로 확인하고 수렴하는 design으로 수정한다.

미통과:
- retry count를 늘리는 것 자체를 reliability solution으로 본다.

### Evidence-first diagnosis

통과:
- failure layer를 좁힐 수 있는 최소 evidence부터 선택한다.
- 수정 뒤 같은 boundary를 다시 검증한다.

미통과:
- 관련 없는 surface를 무작정 모두 확인하거나, 최종 success만 확인하고 원인 설명을 생략한다.

## Final checkpoint

다음 질문에 실제 assessment run을 근거로 답할 수 있으면 Basic core foundation을 통과한 것이다.

> 이 workflow의 Python source가 Dag definition이 되고, 특정 DagRun 안에서 TaskInstance들이 어떤 state를 거쳐 실행되며, 이번 logical input이 어떤 data를 담당하고, task 사이에는 어떤 metadata가 이동하고, external side effect가 retry/reprocessing에서도 어떤 invariant로 안전해야 하는지 설명하라. 문제가 생겼을 때 어느 layer부터 어떤 evidence로 좁힐지도 함께 설명하라.

이 답을 command 이름을 나열하지 않고 **state, ownership, time, dependency, side effect의 관계**로 설명할 수 있어야 한다.
