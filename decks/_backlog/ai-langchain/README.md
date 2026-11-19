# LangChain

Python에서 모델·메시지·도구를 연결하고 `create_agent` 기반 agent의 실행과 실패를 설명·검증하기 위한 학습 덱이다.

현재는 후속 학습을 준비하는 **backlog**다. 교본과 실행 코드는 아직 작성하지 않았다.

## 목표와 선행 지식

학습을 마치면 다음을 할 수 있어야 한다.

- 모델 입력·출력과 message history를 추적하고, 모델 응답과 tool 호출 요청을 구분한다.
- tool schema, 호출 인자, tool 결과가 agent loop를 거치는 과정을 예측·설명한다.
- `create_agent`에 모델·도구·system prompt를 연결하고 종료, 오류, 재시도 조건을 검토한다.
- middleware, 실행 context, structured output을 필요한 경우에만 선택하고 상태·데이터 경계를 설명한다.
- agent의 성공과 실패를 재현 가능한 테스트 및 trace로 검증한다.

**선행 지식:** Python 함수·타입·패키지·테스트의 기초, JSON, LLM API의 요청·응답 구조. LangGraph 경험은 필수가 아니다.

## 학습 범위와 순서

| 단계 | 핵심 질문 | 완료 확인 |
| --- | --- | --- |
| 1. 모델과 메시지 | 요청·응답에서 어떤 데이터가 전달되는가? | message 종류와 model output을 구분하고 흐름을 추적한다 |
| 2. 도구 계약 | 모델의 tool call은 실제 함수 실행과 어떻게 다른가? | tool 호출 전후의 인자·결과·오류를 예측한다 |
| 3. Agent loop | 어떤 조건에서 모델→도구→모델 반복이 진행·종료되는가? | `create_agent`의 두 개 이상의 경로를 설명한다 |
| 4. Context와 middleware | 실행 중 무엇을 전달·수정·보존해야 하는가? | middleware 전후 데이터 변화와 부작용을 검토한다 |
| 5. Structured output과 검증 | 형식과 동작의 신뢰성을 어떻게 확보하는가? | 정상·잘못된 출력·도구 오류의 반례를 테스트한다 |

**첫 제작 단위:** 단일 도구를 호출하는 agent의 message → tool call → tool result → final response를 관찰한다. 가능하면 고정된 응답 또는 테스트 double로 control flow를 먼저 확인하고, 실제 provider 호출은 별도 live 실습으로 분리한다. 처음부터 대규모 RAG pipeline이나 multi-agent system을 만들지 않는다.

## 완료 기준과 범위 밖

모델·도구·agent의 책임 경계를 설명하고, 예상한 실행 경로와 실제 실행 흔적을 비교하며, 실패를 재현·수정할 수 있으면 이 덱의 기본 목표를 충족한다.

LangGraph의 `StateGraph`·checkpoint·interrupt를 활용한 저수준 orchestration과 Deep Agents의 filesystem·subagent harness는 별도 학습 주제다. 구형 `LLMChain`/legacy `Chain` 예제를 현재 기본 경로로 다루지 않는다.

## 작성 시 확인할 사항

- 현재 지원 중인 LangChain Python API와 설치 가능한 버전을 확인한 뒤 실습 의존성을 고정한다.
- 코드·테스트를 추가할 때 먼저 작은 교본 단위로 설명, 예측, 실행, 해석, 검증을 묶어 리뷰한다.
- API key, prompt에 포함된 개인정보, provider 응답 원문을 Git에 기록하지 않는다.

## 공식 자료

- [LangChain Python 개요](https://docs.langchain.com/oss/python/langchain/overview)
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain Python Reference](https://reference.langchain.com/python/langchain/)
