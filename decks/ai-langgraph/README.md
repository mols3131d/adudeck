# LangGraph

Python에서 **명시적인 state와 control flow**를 가진 workflow를 설계하고, checkpoint·resume·human-in-the-loop
실행을 관찰·검증하기 위한 학습 덱이다.

현재 작업 중인 **active** deck이다. 아래 6단계의 기초 교본·실습을 구현했으며, 각 단위의 실행·평가 결과를 통해
내용을 계속 개선한다. 별도 모델·서비스 운영은 이 범위에 포함하지 않는다.

## 목표와 선행 지식

학습 후에는 다음을 할 수 있어야 한다.

- graph state를 읽는 node와 node가 반환하는 **partial state update**를 구분하고, 다음 state를 계산한다.
- 일반·조건부 edge로 구성한 분기·반복·합류의 실행 순서와 종료 조건을 추적한다.
- state key별 기본 덮어쓰기와 reducer 기반 병합을 비교하고, 병렬 update 충돌을 진단한다.
- super-step 경계의 checkpoint, `thread_id`별 상태, 새 입력·실패 복구·interrupt resume의 차이를 설명한다.
- 재시도 또는 interrupt 이후 node 재실행이 외부 side effect에 미치는 영향을 평가한다.
- 작은 graph의 최종 결과뿐 아니라 node update, 실행 경로, 중간 state를 관찰·검증한다.

**선행 지식:** Python 함수·조건문·반복문·타입(`TypedDict` 등)·기초 테스트와 일반적인 상태 전이.
모델·tool calling은 확장 실습에 유용하지만, LangChain 사용 경험이나 API credential은 필수 전제가 아니다.

## 학습 순서

앞 단계에서 만든 state와 실행 모델을 다음 단계에서 재사용한다. 모델 연동 전에 deterministic graph의
관찰·디버깅을 익힌다.

| 단계 | 핵심 질문과 개념 | 완료 확인 |
| --- | --- | --- |
| 1. State와 node | node는 어떤 state를 읽고 어느 key의 update를 반환하는가? | 단일 node의 입력·update·결과 state를 각각 설명한다 |
| 2. Edge와 제어 흐름 | `START`·`END`, 고정·조건부 edge, 분기·반복은 실행을 어떻게 결정하는가? | 서로 다른 입력의 경로와 종료 조건을 실행 전에 예측한다 |
| 3. Reducer와 합류 | 기본 덮어쓰기와 reducer는 어떻게 다르며 병렬 갱신에 무엇이 필요한가? | 같은 key를 갱신하는 두 node의 충돌과 해결 조건을 설명한다 |
| 4. Checkpoint와 재개 | super-step에서 무엇이 저장되고 `thread_id`는 어떻게 쓰이는가? | 저장된 state를 조회하고 새 입력·오류 복구·replay를 구별한다 |
| 5. Interrupt·실패 복구 | `interrupt()`와 `Command(resume=...)`는 무엇을 재실행하는가? | 중단·승인·재개 경로와 중복 side effect 위험을 검증한다 |
| 6. 결합·검증 | 상태·제어 흐름·복구 경계를 갖는 작은 workflow를 어떻게 테스트하는가? | 정상·분기·중단·재개·실패 사례의 관찰 결과를 제시한다 |

**개념 의존 관계:** 1 → 2 → 3(병렬·합류) → 4(상태 보존) → 5(재실행 경계) → 6(종합).
병렬 실행은 reducer를 설명하기 위한 단계 3의 첫 사례이며, 첫 실습에 선행시키지 않는다.

## 첫 제작 단위: credential-free calibration

첫 단위는 [State와 조건 분기 교본](textbook/state_flow/README.md)에 구현되어 있다. 아래는 그 실습의 학습 계약이다.

- **상태:** `number: int`, `branch: str`를 가진 `TypedDict`.
- **그래프:** `START → classify → (increment 또는 double) → END`. `classify`는 홀짝에 따라
  `branch`만 update하고, 조건부 edge는 그 값을 보고 다음 node를 선택한다.
- **예측 사례:** 초기 state `{"number": 3, "branch": ""}`에서 `classify` 뒤 `branch="odd"`,
  `increment` 뒤 `number=4`. 초기 state `{"number": 4, "branch": ""}`에서는 `branch="even"`,
  `double` 뒤 `number=8`. 두 경우 모두 다른 key는 유지된다.
- **관찰:** 각 node의 반환 update, 조건부 edge가 선택한 경로, 최종 state를 예측과 대조한다.
  업데이트하지 않은 key가 보존되는지도 확인한다.
- **반례:** `classify`가 전체 state를 돌려줘야 한다고 가정하거나, 조건부 edge가 이전 `branch`
  값을 읽는다고 예측한 경우를 구별한다.

첫 단위에서는 reducer·checkpointer·interrupt를 사용하지 않는다. 이후 반복 경로를 확인하고 병렬 병합,
checkpoint, interrupt를 각각 관찰한 뒤 [종합 실습](textbook/integration/README.md)에서
하나의 workflow에 결합한다. 각 단위에서 예측 → 실행 → state 비교 → 반례 설명을 검토한다.

## 정확성 경계와 완료 기준

- node는 보통 전체 state가 아닌 **key별 update**를 반환한다. 기본적으로 그 key의 기존 값은 교체되고,
  reducer가 지정된 key는 reducer 규칙에 따라 병합된다.
- checkpointer는 super-step 경계에서 thread별 graph state를 기록한다. `thread_id`를 재사용한다고
  무조건 중단 지점부터 계속하는 것은 아니다. 새 입력, 오류 후 `None` 재개, interrupt에 대한
  `Command(resume=...)`를 구분한다.
- interrupt에서 복귀하면 **해당 node의 시작부터 다시 실행**하므로, interrupt 이전의 비멱등성
  side effect는 중복 발생할 수 있다. Checkpoint만으로 외부 작업의 exactly-once 실행이 보장되지는 않는다.
- 첫 구현은 provider 없는 Graph API 기준으로 검증한다. 외부 모델·도구가 포함된 경우에도
  deterministic step의 상태 변화와 실패 경계를 별도로 추적한다.

교본 완성은 파일 수가 아니라 학습자가 graph의 상태 전이·종료·복원 경로를 설명하고,
정상·분기·중단·재개·실패 조건을 재현 가능한 사례로 검증할 수 있는지로 판단한다.

**범위 밖:** LangChain `create_agent`의 일반적인 model/tool integration, Deep Agents의
planning·filesystem·subagent harness, LangSmith managed deployment 운영. 이들은 관련된
별도 학습 주제이며 이 덱의 선행 조건으로 강제하지 않는다.

## 시작하기

이 덱은 root Python 환경과 독립적인 `pyproject.toml`을 가진다. 저장소 root에서:

```bash
cd decks/ai-langgraph
uv sync --locked
uv run python textbook/state_flow/flow.py
uv run python textbook/loops/counter_loop.py
uv run python textbook/reducers/parallel_updates.py
uv run python textbook/checkpoints/checkpoints.py
uv run python textbook/checkpoints/replay.py
uv run python textbook/interrupts/approval.py
uv run python textbook/integration/workflow.py
uv run python -m unittest discover -s tests -v
```

`flow.py`는 node별 **update event**와 최종 state를 구분해 출력한다. 상태 전이가 예측과 다르면
[Unit 1 교본](textbook/state_flow/README.md)의 worked trace로 돌아가 원인을 추적한다.
외부 API key와 모델 서비스는 사용하지 않는다. Python 3.10+과 `uv`가 필요하다.

## 구현 현황

| 단위 | 학습 자료 | 실행 검증 |
| --- | --- | --- |
| 1. State와 분기 | [교본 + 실습](textbook/state_flow/README.md) | `tests/test_state_flow.py` |
| 2. Edge와 반복 | [교본 + 실습](textbook/loops/README.md) | `tests/test_loops.py` |
| 3. 병렬 병합·reducer | [교본 + 실습](textbook/reducers/README.md) | `tests/test_reducers.py` |
| 4. Checkpoint·thread·replay | [교본 + 실습](textbook/checkpoints/README.md) | `tests/test_checkpoints.py`, `tests/test_replay.py` |
| 5. Interrupt와 재개 | [교본 + 실습](textbook/interrupts/README.md) | `tests/test_interrupts.py` |
| 6. 결합·검증 | [종합 교본 + 실습](textbook/integration/README.md) | `tests/test_integration.py` |

**버전 기준:** 2026-11-19, LangGraph Python 1.2 계열. 지원 API는 공식 문서에서 재확인한다.

## 공식 자료

현재 지원되는 **Python LangGraph Graph API**를 기준으로 작성한다. 교본·실습을 구현할 때
관련 API와 실행 계약을 다음 공식 자료에서 다시 확인한다.

- [Graph API: state·node·edge·reducer](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [Graph API: control flow](https://docs.langchain.com/oss/python/langgraph/graph-api-control-flow)
- [Checkpointers: thread·checkpoint·resume](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- [Interrupts: resume와 node 재실행](https://docs.langchain.com/oss/python/langgraph/interrupts)
- [Test: node 및 graph 테스트](https://docs.langchain.com/oss/python/langgraph/test)
