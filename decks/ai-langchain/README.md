# LangChain

Python에서 LangChain의 **모델·메시지·도구·agent**를 연결하고, state와 context, middleware,
structured output, 실행 증거를 단계별로 이해·검증하는 학습 덱이다. 추상적인 API 목록을 암기하기보다
실행 전 상태를 예측하고 실제 LangChain runtime의 변화와 비교한다.

**현재 상태:** active. 아래 6단계 입문 범위의 교본과 실행 실습을 구현했다.
핵심 실습은 **실제 LangChain `create_agent`를 scripted fake model과 함께 실행**하므로
외부 provider API key나 과금 없이 반복할 수 있다. fake를 사용하므로 실제 provider의 모델 판단 품질은
검증하지 않는다.

## 시작하기

**선행 지식:** Python 함수·타입·패키지·테스트 기초, JSON, LLM API 요청·응답 구조.
LangGraph와 Deep Agents를 미리 공부할 필요는 없다.

저장소 root에서 Python 3.11+ 및 `uv`가 있는 환경으로 실행한다. 현재 프로젝트가 사용하는 Python 3.14에서도
검증하도록 구성했다. 초기 실행에 패키지 다운로드가 필요할 수 있다.

```bash
bash scripts/test.sh langchain-deck
```

단원별로 직접 재현하려면 다음을 실행한다.

```bash
uv run --no-project --with langchain==1.5.2 python decks/ai-langchain/playground/01-agent-loop/first_agent.py --scenario tool
uv run --no-project --with langchain==1.5.2 python decks/ai-langchain/playground/02-state-context/state_context.py
uv run --no-project --with langchain==1.5.2 python decks/ai-langchain/playground/03-structured-output/structured_response.py --scenario repair
uv run --no-project --with langchain==1.5.2 python decks/ai-langchain/playground/01-agent-loop/trace_and_recovery.py
```

각 실습은 아래 교본의 **실행 전 예측 → 관찰 → 해석 → 반례 → 독립 문제** 순서로 진행한다.
먼저 출력을 보지 않고 메시지 타입, 호출 횟수, 상태 길이 및 실패 처리를 예상한다.

## 학습 순서와 증거

| 개념 단계 | 교본과 실행 실습 | 완료 확인 |
| --- | --- | --- |
| 1. 모델과 메시지 | [01. 메시지·도구·agent](textbook/01-messages-tools-agent/README.md) · [모델 호출](playground/01-agent-loop/first_agent.py) | model-only 경로에서 tool call과 실제 실행을 구분한다 |
| 2. 도구 계약 | 01 교본 · [tool 시나리오](playground/01-agent-loop/first_agent.py) | tool call ID와 `ToolMessage.tool_call_id`를 연결하고 실행 횟수를 검증한다 |
| 3. Agent loop | 01 교본 · [agent tests](playground/01-agent-loop/test_first_agent.py) | no-tool, tool, error 경로의 차이를 추적한다 |
| 4. State·context·middleware | [02. 상태와 수명](textbook/02-state-context/README.md) · [실습](playground/02-state-context/state_context.py) | thread별 상태 분리, run별 context, hook 전후 개수를 예측한다 |
| 5. Structured output | [03. 스키마와 검증](textbook/03-structured-output/README.md) · [실습](playground/03-structured-output/structured_response.py) | 검증 성공·수정·거부의 세 경로를 구별한다 |
| 6. 실행 추적과 검증 | [04. 관찰과 오류 경계](textbook/04-observation-verification/README.md) · [실습](playground/01-agent-loop/trace_and_recovery.py) | stream 단계와 middleware 오류 상태를 확인하고 증거의 한계를 설명한다 |

각 단계에는 교본, 설명이 있는 실행 예제, 예측·비교·디버깅 문제 및 검사 가능한 assertion이 있다.
한 단계의 예제 출력을 복사하는 것만으로는 다음 단계의 학습 결과를 충족하지 않는다.

### 도구와 Agent의 책임

모델은 요청과 응답을 생성한다. `AIMessage.tool_calls`는 Python 함수 실행의 결과가 아니라
실행 **요청**이다. `create_agent`가 도구를 실행하고, 대응하는 `ToolMessage`를 전달해
모델에 다시 질문하는 loop를 구성한다. `state["messages"]`는 실행 결과이며, 여러 invocation
간의 persistence는 checkpointer 설정과 `thread_id`에 달려 있다. `context`는 그 호출의
runtime data이고 state와 별개다.

structured output은 schema 검증을 제공할 뿐 **최종 답변의 사실성을 증명하지 않는다**.
오류 handling도 "성공으로 바꾼다"가 아니라 예외 전파, 오류 메시지 변환, 제한된 재시도 중 어떤
정책을 택하는지 설명해야 한다.

## 검증 수준과 제한

- **실행 검증 범위:** fake의 고정 응답을 입력으로 사용하는 실제 LangChain Python runtime에서
  모델 호출·도구 호출·상태 누적·middleware·structured output·stream 제어를 검사한다.
  `scripts/test.sh langchain-deck`는 각 실행 경로와 테스트를 자동으로 실행한다.
- **검증하지 않는 범위:** live provider API, 모델의 tool 선택 정확도, 생성 내용의 사실성,
  외부 도구의 네트워크 부작용, 실제 운영 환경에서의 장기 저장과 distributed trace.
  해당 항목을 fake 테스트 성공으로 대체하거나 검증됐다고 주장하지 않는다.
- **의존성:** `pyproject.toml`의 직접 의존성은 `langchain==1.5.2`. 실행 명령도 동일하게
  고정한다. 아직 전이 의존성을 고정한 lockfile은 없으므로 완전한 환경 재현성은 보장하지 않는다.
- **안전:** API key, 개인정보, prompt 원문과 민감한 provider 응답/trace를 Git에 기록하지 않는다.

## 완료 기준과 제외

이 입문 범위의 완료는 학습자가 모델·도구·agent의 책임을 설명하고, 첫 실행에서 tool call을 보고
실행 결과를 예측하며, 두 번째 호출의 상태와 다른 thread의 상태를 구별하고, schema 오류와
도구 오류의 서로 다른 경로를 **직접 재현·변형**할 수 있는지로 판단한다. 실행된 unit test는
그 확인을 위한 장치이지, 학습자가 문제를 해결했다는 뜻은 아니다.

이 덱은 LangChain Python의 현재 `create_agent` 중심 API를 다룬다.
LangGraph `StateGraph` 직접 구성·checkpoint 관리·interrupt,
Deep Agents의 filesystem/subagent harness, 대규모 RAG와 multi-agent pipeline은 별도 덱의 범위다.
과거 `LLMChain`/legacy `Chain`을 현재 기본 API처럼 가르치지 않는다.

## 공식 자료

- [LangChain Python](https://docs.langchain.com/oss/python/langchain/overview)
- [Models](https://docs.langchain.com/oss/python/langchain/models)
- [Messages](https://docs.langchain.com/oss/python/langchain/messages)
- [Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [Short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory)
- [Custom middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom)
- [Structured output](https://docs.langchain.com/oss/python/langchain/structured-output)
- [Unit testing](https://docs.langchain.com/oss/python/langchain/test/unit-testing)
- [Python API reference](https://reference.langchain.com/python/langchain/)
