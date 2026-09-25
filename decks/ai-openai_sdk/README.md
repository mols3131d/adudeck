# OpenAI Python SDK

OpenAI Python SDK를 **직접 작성하고 수정하면서** 배우는 deck이다.

이 deck의 중심 질문은 단순하다.

```text
내 Python 값
→ SDK call
→ OpenAI API
→ typed response
→ 다음 application state
```

완성된 diagnostic program을 실행하는 대신, 각 unit에서 작은 Python 파일을 읽고 한두 줄을 직접 바꾼다.
실습은 가능한 한 다음 흐름을 따른다.

```text
작게 실행
→ 결과를 예측
→ 한 부분을 직접 수정
→ 다시 실행
→ 무엇이 달라졌는지 설명
```

## Goal

이 deck을 마치면 다음을 할 수 있어야 한다.

- `OpenAI` client와 `responses.create()`의 역할을 구분한다.
- `Response` object에서 text, IDs, output items, usage를 필요한 만큼 읽는다.
- multi-turn context를 manual history, `previous_response_id`, Conversation 중 요구에 맞게 연결한다.
- transport/API/application failure와 SDK retry/timeout을 구분한다.
- Structured Outputs를 typed contract로 사용하고 business validation과 분리한다.
- Function Calling에서 model proposal과 application-owned execution을 구분한다.
- 이후 streaming/async와 application integration boundary로 같은 mental model을 확장한다.

## Prerequisites

- Python 함수, class, exception, list/dict
- JSON과 Python value의 기본 대응
- environment variable과 package 실행 기초
- HTTP request/response의 기본 개념

Pydantic, retry, async는 prerequisite가 아니다. 필요한 unit에서 도입한다.

## Learning path

| Unit | 핵심 질문 | Material |
| --- | --- | --- |
| 0. Start | SDK를 실행할 최소 환경은 무엇인가? | [Bundle](textbook/00-start/README.md) |
| 1. Client → Response | 한 번의 SDK call에서 무엇을 보내고 무엇을 받는가? | [Bundle](textbook/01-client-request-response/README.md) |
| 2. Conversation state | 다음 turn의 context를 누가 소유하는가? | [Bundle](textbook/02-conversation-state/README.md) |
| 3. Failure boundaries | Python call 하나가 몇 HTTP attempt를 만들 수 있는가? | [Bundle](textbook/03-failure-boundaries/README.md) |
| 4. Structured Outputs | 언제 model output을 typed application data로 받아들여도 되는가? | [Bundle](textbook/04-structured-outputs/README.md) |
| 5. Function Calling | 누가 tool을 제안하고 누가 실제 code를 실행하는가? | [Bundle](textbook/05-function-calling/README.md) |
| 6. Streaming + async | intermediate event와 final state를 어떻게 구분하는가? | planned |
| 7. Integration | SDK boundary를 application code에서 어떻게 작고 testable하게 유지하는가? | planned |

Unit 0~5의 textbook은 unit directory bundle이다. 각 bundle의 `README.md`가 교본 entrypoint이고, 그 unit에서 사용하는
runnable playground와 supporting code를 같은 directory에 둔다.

Unit 1~5는 구현되어 있다. Unit 6~7이 구현되기 전에는 전체 deck completion을 선언하지 않는다.

## Start here

Repository root에서 deck directory로 이동한 뒤 committed lockfile 그대로 project dependency를 준비한다.

```bash
cd decks/ai-openai_sdk
uv sync --locked
export OPENAI_API_KEY='...'
uv run textbook/01-client-request-response/request_response.py
```

`uv run`도 필요하면 project environment를 동기화하므로 이후에는 playground 실행만 반복하면 된다.
성공하면 model의 한 줄 설명이 출력된다.

Official OpenAI API를 호출하는 playground는 API usage와 quota를 소비할 수 있으며 계정 설정에 따라 비용이 발생할 수 있다.
실행 전에 사용하는 model과 account usage policy를 확인한다.

`OPENAI_MODEL`을 설정하면 예제의 기본 model을 바꿀 수 있다.

```bash
export OPENAI_MODEL='gpt-5.5'
```

환경 자체가 의심스러울 때만 optional preflight를 사용한다.

```bash
python scripts/setup.py
```

## Dependency ownership

이 deck의 Python dependency contract는 [`pyproject.toml`](pyproject.toml)과 [`uv.lock`](uv.lock)이 함께 소유한다.

```text
pyproject.toml
→ Python version requirement
→ openai dependency range
→ pydantic dependency range

uv.lock
→ 이 deck에서 실제로 resolve한 exact dependency set

textbook/<unit>/*.py
→ 해당 unit에서 학습할 Python/SDK code와 supporting code
```

Playground마다 PEP 723 dependency metadata를 반복하지 않는다. Dependency range를 바꾸려면 `pyproject.toml`을 수정한 뒤
`uv lock`으로 `uv.lock`을 갱신한다. 일반 학습 실행에서는 committed lockfile을 사용한다.

## How to use the bundled playgrounds

Playground는 완성된 CLI 도구가 아니다. **학습자가 수정해도 되는 작은 실험 파일**이다.

각 unit bundle의 순서대로:

1. 먼저 실행 결과를 예측한다.
2. 파일을 읽고 어떤 줄이 핵심인지 찾는다.
3. 교본이 지정한 한 부분만 직접 수정한다.
4. 다시 실행한다.
5. 출력 차이를 SDK state/data flow로 설명한다.

실습을 망가뜨렸다면 Git diff로 원래 상태를 확인하거나 파일을 되돌리고 다시 시작하면 된다.

## Environment boundary

Canonical learning path는 official OpenAI API다. 이 deck은 `previous_response_id`, Conversation,
Structured Outputs, Function Calling처럼 provider compatibility가 달라질 수 있는 기능을 학습한다.

Ollama의 OpenAI compatibility는 stateless Responses 등 일부 surface를 실험하는 데 유용할 수 있지만,
현재 `previous_response_id`와 `conversation`을 지원하지 않는다. 따라서 Ollama를 전체 deck의 drop-in
replacement로 가정하지 않는다.

## Version baseline

작성/검토 기준일: **2026-09-24**

- OpenAI Python SDK reviewed baseline: `3.19.2`
- dependency range in `pyproject.toml`: `openai>=3.19.2,<4`
- exact resolved versions: `uv.lock`
- Python: 3.10+
- primary model interaction surface: Responses API
- example default model: `gpt-5.5`
- model은 `OPENAI_MODEL`로 override 가능

`3.19.2`는 이 자료를 검토한 calibration version이지 dependency declaration의 exact pin이 아니다. `pyproject.toml`은
compatible v3 update를 허용하고 v4 breaking change만 막으며, `uv.lock`이 현재 deck에서 실제 실행할 exact set을 기록한다.
Dependency를 의도적으로 update하면 retry, response state, conversation state, tool loop의 관찰 결과를 현재
documentation과 다시 확인한다.

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

기본 scope가 아닌 것:

- model training/transformer theory
- prompt engineering pattern catalog
- Realtime audio application 전체
- Agents SDK/agent framework architecture
- provider-specific deployment/secret-manager design
- 다른 언어 SDK

## References

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Responses API](https://developers.openai.com/api/reference/resources/responses)
- [Conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
- [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Function calling](https://developers.openai.com/api/docs/guides/function-calling)
- [Ollama OpenAI compatibility](https://docs.ollama.com/api/openai-compatibility)
