# LangChain

Python에서 **모델 호출과 agent 실행을 구분**하고, LangChain `create_agent`의 메시지·도구·실행 흐름을
설명하고 검증하기 위한 학습 덱이다.

**상태:** 첫 학습 단위를 구현 중인 active deck. 커리큘럼 전체가 완성된 것은 아니다.

**지금 학습하기:** [01. 메시지와 도구 호출 교본](textbook/01-messages-tools-agent/README.md)과
[실행 실습](playground/01-agent-loop/first_agent.py)을 함께 사용한다. Python 3.11+와 `uv`가 필요하며,
API key 없이 `uv run --project decks/ai-langchain --no-lock python
decks/ai-langchain/playground/01-agent-loop/test_first_agent.py`로 첫 실습의 동작을 확인할 수 있다.
현재 직접 의존성은 `langchain==1.5.2`로 고정했고, lockfile은 아직 없으므로 전이 의존성까지
고정한 재현성은 보장하지 않는다.

## 학습 목표와 선행 지식

학습을 마치면 다음을 할 수 있어야 한다.

- 단독 chat model 호출과 agent 실행의 차이를 설명하고, `HumanMessage`, `AIMessage`, `ToolMessage`의
  역할과 데이터 흐름을 추적한다.
- tool schema와 모델이 반환한 tool call을 실제 함수 실행과 구분하고, tool call ID·인자·결과가 어떻게
  연결되는지 검증한다.
- `create_agent`의 모델 → 도구 → 모델 반복, 도구 호출 없는 종료, 반복 제한과 오류 경로를 예측한다.
- agent state, 실행 시점의 context, middleware의 책임을 구분하고 개입 전후의 변화를 설명한다.
- structured output의 schema 검증과 provider별 지원 차이를 이해하고, 정상·실패 경로를 테스트와 trace로 확인한다.

**선행 지식:** Python 함수·타입·패키지·테스트 기초, JSON, LLM API 요청·응답 구조.
LangGraph 경험은 필요하지 않으며, 직접적인 graph 구성은 이 덱에서 다루지 않는다.

## 학습 순서와 확인 방법

앞 단계의 산출물과 개념이 다음 단계의 입력이 된다. 주제를 읽는 것만으로 완료하지 않고 실행 흐름을
**예측 → 관찰 → 설명 → 검증**한다.

| 단계 | 개념과 의존 관계 | 학습 확인 |
| --- | --- | --- |
| 1. 모델과 메시지 | 모델에 전달하는 메시지, 모델의 응답, 단독 `invoke` | 입력과 `AIMessage`의 내용·metadata를 구분하고 두 요청의 흐름을 그린다 |
| 2. 도구 계약 | 메시지와 모델 응답을 이해한 뒤 tool schema, tool call, `ToolMessage` | tool call은 실행 결과가 아님을 설명하고 call ID·인자·결과 대응을 확인한다 |
| 3. Agent loop | 모델·도구 계약을 연결해 `create_agent` 실행 | 도구 없이 종료하는 경로와 한 번 도구를 호출하는 경로를 추적하고 호출 횟수를 검증한다 |
| 4. Context와 middleware | agent 실행 흐름을 알고 난 뒤 state, runtime context, hook | 입력 context와 state의 차이를 설명하고 middleware 개입 전후의 메시지·오류 처리를 비교한다 |
| 5. Structured output | 모델의 최종 출력과 검증 책임을 이해한 뒤 `response_format` | 유효·무효 schema 사례를 구분하고 `structured_response`와 실패 경로를 검사한다 |
| 6. 테스트와 관찰 | 앞 단계의 실행 경로를 재현할 수 있는 상태 | fake model 기반 unit test와 별도 live integration test의 검증 범위를 비교하고 trace를 해석한다 |

이 순서는 하나의 입문 학습 경로다. message history를 관찰하는 것과 여러 호출 사이의 영속적인
대화 상태를 보존하는 것은 다르며, 후자는 별도 persistence 구성이 필요할 수 있다.

## 구현된 첫 제작 단위: 한 번의 도구 호출

첫 교본·실습은 **단일 순수 함수 도구를 호출하는 작은 agent**를 다룬다. 먼저 모델·도구의
입출력을 고정해 control flow를 관찰하고, provider 호출은 별도의 선택적 실습으로 분리한다.

1. **예측:** 사용자 메시지 이후 `AIMessage.tool_calls`가 생성되더라도 도구 함수가 아직 실행된 것은
   아님을 설명한다. tool call의 이름·인자·ID를 예상한다.
2. **관찰:** `create_agent`로 도구를 실행해 `ToolMessage.tool_call_id`와 원래 tool call ID가 일치하고,
   결과가 다음 모델 입력으로 전달되는지 확인한다.
3. **대조:** 도구가 필요 없는 요청은 모델 응답으로 종료되는 경로와 비교한다.
4. **반례:** 잘못된 tool 인자 또는 도구 실행 오류를 재현한다. 기본 오류 동작과 middleware를 추가한
   처리·재시도 정책을 혼동하지 않고, 무한 반복 방지를 위한 호출 제한도 확인한다.
5. **검증:** 도구 실행 횟수, message 순서, 종료 조건, 기대한 최종 응답을 assertion으로 확인하고
   예측과 실제 결과가 달랐던 이유를 설명한다.

오프라인 테스트에서는 공식 unit testing 문서의 `GenericFakeChatModel` 같은 scripted fake를
우선 검토한다. 이 fake는 기본적으로 `bind_tools`를 구현하지 않으므로, `create_agent`와
결합할 때는 공식 예제처럼 테스트용 adapter가 필요하다. 실제 provider 호출에서는 인증·비용·응답
비결정성을 별도로 다루며, deterministic test의 통과를 live 환경 검증으로 간주하지 않는다.

## 완료 기준과 범위

기본 완료 조건은 모델·도구·agent의 책임 경계를 스스로 설명하고, 서로 다른 실행 경로를 예측한 뒤
실제 메시지와 테스트 결과로 확인하며, 도구 오류와 출력 검증 실패의 원인을 구분하는 것이다.

- **포함:** LangChain Python의 model/message/tool 표준 인터페이스, `create_agent`, 필요한 범위의
  middleware·context·structured output, unit/integration test와 trace 해석.
- **제외:** LangGraph `StateGraph`·checkpoint·interrupt를 직접 구성하는 orchestration,
  Deep Agents의 filesystem·subagent harness, 대규모 RAG와 multi-agent pipeline.
  과거의 `LLMChain`/legacy `Chain` 예제는 현재의 기본 학습 경로로 사용하지 않는다.

## 버전과 후속 구현 확인

현재 기준은 **2026-11-19에 확인한 LangChain Python 공식 문서의 `create_agent` 중심 API**다.
추가 코드를 작성할 때는 당시 지원 버전과 provider 통합 패키지를 다시 확인하고, 필요한 의존성을
이 deck의 `pyproject.toml`에 명시한다. 모델의 tool calling·structured output 지원은 provider와 모델에
따라 다를 수 있으므로 동일한 동작을 가정하지 않는다.

API key, prompt의 개인정보, provider 응답 원문 또는 민감한 trace를 Git에 기록하지 않는다.
실습 코드는 처음부터 큰 pipeline 대신 설명·예측·실행·해석·검증이 한 단위가 되도록 만든다.

## 공식 자료

- [LangChain Python 개요](https://docs.langchain.com/oss/python/langchain/overview)
- [Models](https://docs.langchain.com/oss/python/langchain/models)
- [Messages](https://docs.langchain.com/oss/python/langchain/messages)
- [Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [Middleware](https://docs.langchain.com/oss/python/langchain/middleware/overview)
- [Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [Unit testing](https://docs.langchain.com/oss/python/langchain/test/unit-testing)
- [LangChain Python Reference](https://reference.langchain.com/python/langchain/)
