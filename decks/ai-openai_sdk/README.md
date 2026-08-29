# OpenAI Python SDK

OpenAI Python SDK를 단순한 `responses.create()` 호출법이 아니라
**Python application과 OpenAI API 사이의 typed request/response boundary**로 이해하기 위한 deck이다.

Model 이론이나 prompt pattern catalog는 다루지 않는다. 대신 application code에서 다음을 추적한다.

```text
Python state
→ SDK call arguments
→ HTTP/API boundary
→ typed Response
→ application state / decision
```

## Goal

이 deck을 마치면 다음을 할 수 있어야 한다.

- `OpenAI` client와 endpoint call의 책임을 구분한다.
- Response object, output items, resource/request identifiers를 해석한다.
- multi-turn context를 manual history, `previous_response_id`, Conversation 중 요구에 맞게 소유한다.
- transport/API/application failure와 SDK retry/timeout을 분리한다.
- Structured Outputs를 schema contract로 사용하고 response state와 business validation을 구분한다.
- Function Calling에서 model proposal과 application-owned execution을 분리한다.
- 이후 streaming/async와 application integration boundary를 같은 mental model로 확장한다.

## Prerequisites

- Python 함수, class, exception, list/dict
- JSON과 Python value의 기본 대응
- environment variable과 package 실행 기초
- HTTP request/response의 기본 개념

Pydantic, retry, async는 prerequisite로 요구하지 않고 필요한 unit에서 도입한다.

## Learning path

| Unit | 핵심 질문 | Material |
| --- | --- | --- |
| 1. Client → Request → Response | Python value는 언제 network request가 되고 무엇이 돌아오는가? | [Textbook](textbook/01-client-request-response.md) · [Playground](playground/request_response.py) |
| 2. Conversation state | 다음 turn의 context를 누가 소유하는가? | [Textbook](textbook/02-conversation-state.md) · [Playground](playground/conversation_state.py) |
| 3. Failure boundaries | 한 Python call 안에서 몇 HTTP attempt가 일어날 수 있는가? | [Textbook](textbook/03-failure-boundaries.md) · [Playground](playground/failure_boundaries.py) |
| 4. Structured Outputs | 언제 model output을 typed application data로 받아들여도 되는가? | [Textbook](textbook/04-structured-outputs.md) · [Playground](playground/structured_output.py) |
| 5. Function Calling | 누가 tool을 제안하고 누가 실제 code를 실행하는가? | [Textbook](textbook/05-function-calling.md) · [Playground](playground/function_calling.py) |
| 6. Streaming + async | intermediate event와 final state, sync와 async를 어떻게 구분하는가? | planned |
| 7. Integration | SDK boundary를 application code에서 어떻게 작고 testable하게 유지하는가? | planned |

Unit 1~5는 현재 구현되어 있다. Unit 6~7이 구현되기 전에는 전체 deck completion을 선언하지 않는다.

## Learning contract

각 implemented unit은 가능한 한 같은 cycle을 따른다.

```text
mental model
→ worked state/control-flow trace
→ prediction
→ playground observation
→ one meaningful variation
→ explanation / assessment
```

Playground의 목표는 output을 얻는 것이 아니라 **state owner와 boundary를 관찰하는 것**이다.

### Evidence levels

```text
Preview
→ local application state / call plan

Synthetic local HTTP
→ SDK behavior under controlled response

Live API
→ actual SDK/API request-response behavior

Application/business validation
→ domain rule correctness
```

한 level의 evidence를 더 높은 level로 자동 승격하지 않는다.

예를 들어:

- `--preview`는 wire-level HTTP request를 증명하지 않는다.
- localhost synthetic 429는 실제 OpenAI rate-limit condition을 증명하지 않는다.
- schema-valid result는 business truth를 증명하지 않는다.
- function-call proposal은 local tool execution이 이미 일어났다는 뜻이 아니다.

이 distinction이 deck의 신뢰도 기준이다.

## Running playgrounds

API key 없이 local state를 볼 수 있는 unit은 `--preview`를 먼저 사용한다.

```bash
python playground/request_response.py --preview
python playground/conversation_state.py --mode manual --preview
python playground/failure_boundaries.py --preview
python playground/structured_output.py --preview
python playground/function_calling.py --preview
```

Live API가 필요한 experiment는 credential을 source에 기록하지 않고 environment로 제공한다.

```bash
export OPENAI_API_KEY='...'
uv run playground/request_response.py
```

Model access가 다르면 source를 수정하지 말고 `OPENAI_MODEL` 또는 해당 playground option을 사용한다.

API call에는 비용과 quota가 적용될 수 있다.

## Version baseline

작성/검토 기준일: **2026-08-29**

- OpenAI Python SDK: v3.x baseline
- Python: 3.10+
- primary model interaction surface: Responses API
- playground model은 configuration으로 override 가능

Version-sensitive public API, generated type, model identifier는 바뀔 수 있다. Major SDK upgrade에서는 syntax만 수정하지
말고 각 chapter의 state/control-flow model과 playground evidence가 여전히 유효한지 다시 검토한다.

## Scope boundary

Core path:

```text
request/response
→ conversation state
→ failure/retry
→ structured output
→ function calling
→ streaming/async
→ integration
```

다음은 기본 scope가 아니다.

- model training/transformer theory
- prompt engineering pattern catalog
- Realtime audio application 전체
- Agents SDK/agent framework architecture
- provider-specific deployment/secret-manager design
- 다른 언어 SDK

## References

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Responses API](https://platform.openai.com/docs/api-reference/responses)
- [Conversation state](https://platform.openai.com/docs/guides/conversation-state)
- [Structured outputs](https://platform.openai.com/docs/guides/structured-outputs)
- [Function calling](https://platform.openai.com/docs/guides/function-calling)
- [Models](https://platform.openai.com/docs/models)
