# OpenAI Python SDK

OpenAI Python SDK를 단순한 `client.responses.create(...)` 호출법이 아니라,
**Python application과 OpenAI API 사이의 request/response 경계를 다루는 typed client library**로 이해하기 위한 deck이다.

이 deck은 LLM 이론이나 prompt 모음집을 만들지 않는다. 대신 SDK를 사용하는 application에서 어떤 입력이 call argument가
되고, 어떤 output item과 metadata가 response로 돌아오며, state·failure·structured output·tool calling·streaming이 이
경계를 어떻게 확장하는지를 단계적으로 학습한다.

## Goal

학습이 끝나면 다음을 할 수 있어야 한다.

- `OpenAI` client가 configuration과 transport를 소유하고 endpoint method가 실제 API request를 만든다는 경계를 설명한다.
- Responses API call arguments를 구성하고 `Response` 객체의 type, identifiers, output items, usage를 구분해 해석한다.
- application이 history/output items를 직접 운반하는 방식, `previous_response_id` 기반 response lineage, durable
  Conversations API의 state ownership 차이를 설명하고 상황에 맞는 연결 방식을 선택한다.
- timeout, connection failure, rate limit, API status error를 서로 다른 failure boundary로 진단하고 SDK의 retry 동작을
  합리적으로 제어한다.
- Pydantic schema를 사용해 structured output을 받고, completed response·refusal/incomplete state·parsed schema result를
  구분해 처리한다.
- function calling에서 **model이 tool call을 제안하는 단계**와
  **application이 함수를 실행하고 `call_id`에 대응하는 결과를 돌려주는 단계**를 분리해 구현한다.
- streaming event와 async client를 사용하면서 최종 response와 중간 event의 차이를 설명한다.
- API key를 source code에 넣지 않고, model/version drift를 격리하며, SDK 호출부를 testable한 application boundary로
  설계한다.

## Scope

core path에서 다룬다.

1. client → application call arguments → HTTP boundary → typed response mental model
2. `response.output` item 구조와 세 가지 context ownership: manual history (`store=False`), `previous_response_id`,
   Conversations API
3. errors, automatic retries, timeouts, request ID 기반 observability
4. structured outputs, Pydantic parsing, refusal/incomplete handling
5. function calling loop, `call_id` correlation, application-owned tool execution
6. streaming event와 `AsyncOpenAI`
7. 작은 application adapter로 통합하고 fake/stub로 test하는 방법

초기 scope에서는 다음을 다루지 않는다.

- 모델 학습 원리, transformer 수학, fine-tuning 이론
- prompt engineering 패턴 카탈로그
- Realtime audio application의 전체 설계
- Agents SDK나 별도 agent framework의 architecture
- 특정 cloud provider의 secret manager, network, deployment 구성
- JavaScript/TypeScript SDK와 다른 언어 SDK

필요해지면 별도 deck 또는 curriculum delta로 다룬다.

## Prerequisites

- Python 함수, module, class, exception의 기본 문법
- dictionary/list와 JSON 사이의 대응 관계
- environment variable과 package installation의 기본 사용법
- HTTP가 request를 보내고 response를 받는다는 정도의 기본 mental model

`**mapping` keyword unpacking처럼 첫 unit에서 바로 필요한 작은 Python 문법은 사용 지점에서 설명한다. asyncio, Pydantic,
retry 전략은 prerequisite로 요구하지 않고 필요한 시점에 SDK 사용에 필요한 만큼 도입한다.

## Concept Dependencies

```text
Python call / object
        ↓
client configuration + application call arguments
        ↓
Responses API request / typed Response
        ↓
output items + usage + request/response identifiers
        ↓
conversation context ownership
  ├─ manual history + output replay (`store=False`)
  ├─ response lineage (`previous_response_id`)
  └─ durable Conversations API object
        ↓
client failure boundaries + retry / timeout semantics
        ↓
structured outputs + schema parsing
        ↓
function calling + `call_id` + application-owned execution
        ↓
streaming events + async control flow
        ↓
application integration boundary
```

이 순서는 API feature 목록을 나열한 것이 아니다. 먼저 평범한 request/response와 state ownership을 이해하고, 그 다음 모든
후속 실습에 적용되는 failure/retry boundary를 확립한다. 이후 schema를 통해 machine-readable output contract를 배우고,
function calling에서 schema와 application-owned execution을 결합한다. 마지막으로 같은 의미를 event stream과 async
control flow에서 추적한다.

“이전 대화를 이어간다”는 한 문장으로 state를 뭉개지 않는다. application이 full history와 prior output items를 직접
소유·재전송하는 방식, response ID로 lineage를 잇는 방식, 별도 durable conversation object에 state를 두는 방식은
persistence와 ownership이 다르다.

## Learning Path

| Unit | Responsibility | Outcome development | State |
| --- | --- | --- | --- |
| 1. Client, arguments, request, response | SDK call 한 번의 data flow와 observation surface를 확립한다. | state ownership 추적, typed response 해석 | implemented |
| 2. Response and conversation state | output item과 세 가지 context ownership 방식을 구분해 추적한다. | manual history·response lineage·durable conversation 선택 | planned |
| 3. Failure boundaries | transport/API failure, automatic retry, timeout을 관찰하고 분류한다. | retry/timeout/error diagnosis | planned |
| 4. Structured outputs | schema와 response status가 parsing contract에 추가되는 지점을 이해한다. | Pydantic parsing, refusal/incomplete 처리 | planned |
| 5. Function calling | model decision, `call_id`, application execution의 control flow를 분리한다. | tool call/output correlation·debugging | planned |
| 6. Streaming and async | event stream과 coroutine execution을 추적한다. | streaming/async 선택과 구현 | planned |
| 7. Integration | SDK 호출을 작은 application boundary로 감싼다. | testability·observability·upgrade 판단 | planned |

현재 구현된 calibration slice는 [Client → Arguments → Request → Response](01-client-request-response.md)다. 이후 unit은 이
slice의 explanation depth, worked state trace, playground observability, practice와 assessment 강도를 기준으로 증분 구현한다.

## Textbook + Lab Contract

실행 가능한 개념은 다음 loop를 기본으로 한다.

```text
mental model
   ↓
worked state/control-flow trace
   ↓
실행 전 prediction
   ↓
application-owned arguments 또는 event를 observable하게 만든다
   ↓
실제 SDK/API 실행
   ↓
typed response / metadata / failure를 관찰한다
   ↓
관찰을 model과 연결해 설명한다
   ↓
한 조건을 바꾸고 다시 비교한다
   ↓
transfer / assessment
```

lab의 성공 기준은 “문장이 출력됐다”가 아니다. learner가
**어떤 Python 값이 endpoint call argument가 되었고, network boundary 뒤에서 돌아온 어떤 response field를 지금 읽고
있는지** 설명할 수 있어야 한다. local preview는 SDK serialization이나 실제 HTTP wire payload를 검증하지 않는다는
validation boundary도 함께 설명할 수 있어야 한다.

## Lab Runtime

첫 lab은 [lab/request_response.py](lab/request_response.py) 하나로 구성한다. PEP 723 inline dependency metadata를
사용하므로 별도 lab package를 만들지 않는다.

network call 없이 application이 `responses.create()`에 넘길 arguments만 먼저 본다.

```bash
python lab/request_response.py --preview
```

이 preview는 SDK를 import하지 않으므로 SDK serialization이나 실제 HTTP request body를 보여주는 기능이 아니다. 첫 단계의
목적은 application-owned state와 network boundary를 분리해서 관찰하는 것이다.

lab의 `build_call_args()`와 dictionary는 같은 값을 preview와 live call에서 비교하기 위한 **teaching instrumentation**이다.
OpenAI SDK를 사용할 때 반드시 따라야 하는 application architecture가 아니다.

실제 API를 호출하려면 key를 source file에 기록하지 말고 environment variable로 제공한다.

```bash
export OPENAI_API_KEY='...'
uv run lab/request_response.py
```

credential configuration은 `OpenAI()` client construction의 책임으로 남겨 둔다. lab이 별도 credential validator를 두지
않으므로 missing configuration과 remote API rejection을 application wrapper가 가리지 않는다.

현재 lab의 default model은 작성 시점의 cost-sensitive model인 `gpt-5.6-luna`다. account에서 사용할 model이 다르거나
model alias가 바뀌면 source를 수정하지 말고 다음처럼 override한다.

```bash
OPENAI_MODEL='your-model-id' uv run lab/request_response.py
```

API 호출에는 비용과 quota가 적용될 수 있다. `--preview`는 API를 호출하지 않는다.

## Version Baseline

작성 기준일은 **2026-08-29**다.

- OpenAI Python SDK: v3.x (`v3.0.0`을 기준으로 calibration)
- Python SDK minimum: Python 3.10+
- primary model interaction API: Responses API
- calibration model: `gpt-5.6-luna`
- current repository runtime: Python 3.14.x

SDK의 generated types, transport, model identifiers는 변할 수 있다. 그래서 이 deck은 private implementation보다 public
client, endpoint, typed response contract를 우선한다. major SDK upgrade가 발생하면 syntax만 고치지 말고 request/response
mental model과 lab observation이 여전히 유효한지 함께 검토한다.

## Outcome Coverage

- Unit 1은 application call arguments, network boundary, typed response와 identifiers를 worked trace와 playground에서
  관찰하고, transfer task와 self-contained assessment에서 독립적으로 설명하도록 평가한다.
- context ownership, failure handling, structured output, function calling, streaming/async outcome은 아직 미구현 completion
  gap이다.
- 전체 deck completion은 planned unit이 파일로 존재하는지가 아니라 각 outcome에 explanation, practice, observable
  evidence, assessment path가 갖춰졌을 때만 선언한다.

## References

- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Responses API reference](https://platform.openai.com/docs/api-reference/responses)
- [Conversation state](https://platform.openai.com/docs/guides/conversation-state)
- [Models](https://platform.openai.com/docs/models)
- [Function calling guide](https://platform.openai.com/docs/guides/function-calling)
- [Structured outputs guide](https://platform.openai.com/docs/guides/structured-outputs)
