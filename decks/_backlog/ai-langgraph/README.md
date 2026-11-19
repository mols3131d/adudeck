# LangGraph

Python에서 **명시적인 state와 control flow**를 가진 장기 실행 workflow를 설계하고, checkpoint·resume·human-in-the-loop 동작을 관찰·검증하기 위한 학습 덱이다.

현재는 후속 학습을 준비하는 **backlog**다. 교본과 실행 코드는 아직 작성하지 않았다.

## 목표와 선행 지식

학습을 마치면 다음을 할 수 있어야 한다.

- graph state, node, edge, reducer가 실행 중 어떤 값을 읽고 갱신하는지 추적한다.
- 조건 분기·반복·합류에서 다음 node와 state update를 예측하고 잘못된 흐름을 찾아낸다.
- checkpoint, thread별 상태, interrupt 이후 resume를 구분하고 재실행 시의 부작용을 검토한다.
- deterministic step과 모델·도구 호출 step을 조합하며 실패·재시도·중복 실행 경계를 설명한다.
- 작은 graph를 테스트해 최종 결과뿐 아니라 중간 state transition을 검증한다.

**선행 지식:** Python 함수·타입(`TypedDict` 등)·테스트, 일반적인 상태 전이와 분기. 모델·tool calling의 기본 지식은 있으면 유익하지만 LangChain 패키지 학습 자체가 필수 전제는 아니다.

## 학습 범위와 순서

| 단계 | 핵심 질문 | 완료 확인 |
| --- | --- | --- |
| 1. State와 node | node가 받는 state와 반환하는 update는 무엇인가? | 단일 node의 before/after state를 예측한다 |
| 2. Edge와 제어 흐름 | 분기·반복의 실행 순서는 무엇이 결정하는가? | 두 경로의 state 변화와 종료 조건을 추적한다 |
| 3. Reducer와 state 병합 | 여러 update가 충돌하면 어떻게 해석되는가? | 누적·덮어쓰기 결과와 오류 가능성을 비교한다 |
| 4. Checkpoint와 재개 | 어느 시점의 상태가 저장·복원되는가? | thread와 checkpoint를 구분하고 resume을 검증한다 |
| 5. Interrupt·실패 복구 | 승인·재시도·중복 실행은 무엇을 바꾸는가? | 의도적 중단과 side effect의 안전 조건을 설명한다 |
| 6. 결합·검증 | 언제 graph가 단순 agent loop보다 필요한가? | 작은 stateful workflow를 구현·테스트한다 |

**첫 제작 단위:** provider 없이 두세 개의 deterministic node와 조건 분기를 가진 `StateGraph`를 작성해 입력→node update→최종 state를 예측하고 관찰한다. Persistence와 interrupt는 그 state 모델이 확립된 후 추가한다.

## 완료 기준과 범위 밖

graph의 상태 전이·종료·복원 경로를 실행 전에 설명하고, 정상·중단·재개·실패 조건을 검증 가능한 사례로 남긴다.

LangChain의 일반적인 model/tool integration과 `create_agent` 사용법, Deep Agents의 planning·filesystem·subagent harness, LangSmith의 managed deployment 운영 전체는 각 별도 주제다.

## 작성 시 확인할 사항

- 현재 지원 중인 LangGraph Graph API와 persistence·interrupt 계약을 공식 자료에서 확인한다.
- 실행 검증은 credential-free deterministic graph에서 시작하고, 모델 연동은 별도 실습으로 확장한다.
- checkpoint가 있어도 외부 side effect의 exactly-once 실행을 자동 보장한다고 가정하지 않는다.
- 교본은 작게 시작하며 설명→예측→실행→state 비교→반례를 한 단위로 검토한다.

## 공식 자료

- [LangGraph Python 개요](https://docs.langchain.com/oss/python/langgraph/overview)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)
- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
