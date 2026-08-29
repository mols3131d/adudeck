# 2. Conversation state: "이전 대화"를 누가 소유하는가

첫 chapter에서는 한 번의 SDK call에서 application-owned arguments가 network boundary를 지나 typed `Response`로 돌아오는 흐름을 봤다.

multi-turn interaction에서는 새로운 질문이 생긴다.

> 두 번째 request가 첫 번째 turn의 context를 사용하려면, 그 context를 누가 보관하고 다음 call에 어떻게 연결하는가?

"SDK가 대화를 기억한다"라고만 말하면 세 가지 서로 다른 state model을 구분할 수 없다.

이번 chapter에서는 Responses API에서 다음 세 방식을 비교한다.

```text
1. manual history
   application이 이전 input/output items를 직접 보관하고 다시 보냄

2. response lineage
   application이 previous_response_id를 보관하고 API가 이전 response chain을 연결함

3. durable Conversation
   application이 conversation.id를 보관하고 별도 Conversation object에 state를 지속시킴
```

세 방식 모두 multi-turn conversation을 만들 수 있지만 **application이 직접 들고 있는 state, API가 resolve하는 state, persistence boundary가 다르다.**

## 2.1 request는 기본적으로 현재 call의 input을 받는다

첫 chapter의 call을 다시 보자.

```python
response = client.responses.create(
    model="gpt-5.6-luna",
    input="My project codename is Juniper.",
)
```

그 다음 완전히 별개의 call을 만든다.

```python
second = client.responses.create(
    model="gpt-5.6-luna",
    input="What is my project codename?",
)
```

application이 이전 context를 연결하는 어떤 정보도 주지 않았다면, 두 번째 call만 보고 첫 번째 turn을 이어갈 근거가 없다.

따라서 multi-turn state를 이해할 때 첫 질문은 "모델이 기억하는가?"보다 다음이 더 정확하다.

```text
이번 request의 context를 구성하는 state가 어디에 있는가?
```

## 2.2 Mode A: application이 history를 직접 소유한다

가장 명시적인 방식은 application이 다음 turn에 필요한 input/output item을 직접 보관하는 것이다.

```python
history = [
    {"role": "user", "content": "My project codename is Juniper."},
]

first = client.responses.create(
    model="gpt-5.6-luna",
    input=history,
    store=False,
)

history += first.output
history.append(
    {"role": "user", "content": "What is my project codename?"}
)

second = client.responses.create(
    model="gpt-5.6-luna",
    input=history,
    store=False,
)
```

여기서 중요한 것은 application이 text만 복사하는 것이 아니다.

공식 conversation-state guidance는 manual Responses API history를 구성할 때 **response output items 전체를 다음 input context에 포함**하는 방식을 보여준다. `response.output_text`는 편리한 text view지만 response 전체의 state representation이 아니다.

따라서 다음 두 코드는 의미가 다르다.

```python
# context를 단순 text transcript로 축소
history.append({"role": "assistant", "content": first.output_text})
```

```python
# SDK/API가 반환한 output item들을 유지
history += first.output
```

function call이나 reasoning-related item처럼 text message가 아닌 output type이 등장하면 차이는 더 커진다.

### ownership

manual mode에서는 다음 state를 application이 직접 소유한다.

```text
history list
current user input
어떤 prior output item을 보존할지에 대한 policy
history persistence / truncation / storage strategy
```

API가 이전 turn을 찾아줄 ID만 전달하는 방식이 아니라 **application이 다음 request의 context를 직접 구성한다.**

## 2.3 `store=False`가 바꾸는 것은 무엇인가

manual lab에서는 `store=False`를 사용한다.

```python
client.responses.create(
    model=model,
    input=history,
    store=False,
)
```

이 선택은 "application이 history를 직접 운반한다"는 실험을 더 명확하게 만든다. 공식 문서에서는 Response object가 기본적으로 저장되며 `store=false`로 해당 저장 동작을 끌 수 있다고 설명한다.

하지만 다음 식으로 과도하게 일반화하면 안 된다.

```text
store=False
=
모든 종류의 platform data retention / logging / policy가 사라짐
```

이번 chapter에서 필요한 결론은 더 좁다.

> manual history experiment에서는 next-turn context ownership을 application 쪽에 두고, `previous_response_id`나 Conversation object를 state carrier로 사용하지 않는다.

privacy/compliance requirement를 판단하려면 별도의 current data-control documentation을 확인해야 한다.

## 2.4 worked trace: manual history에서 state가 어떻게 커지는가

첫 user input부터 두 번째 request까지 추적해 보자.

```text
Step 1
history = [user message A]

Step 2
first request
input = history

Step 3
first response
Response.output = [output item ...]

Step 4
application mutation
history += first.output
history += [user message B]

Step 5
second request
input = expanded history
```

이 흐름에서 `history`는 application memory다.

| 시점 | application이 직접 가지고 있는 state | API에서 새로 얻는 state |
| --- | --- | --- |
| 첫 call 전 | first user item | 없음 |
| 첫 call 후 | original history + `first` object | first response/output/id |
| second call 전 | prior input + `first.output` + followup | 없음 |
| second call 후 | history + second response | second response/output/id |

application이 process를 종료하고 history를 어디에도 저장하지 않았다면 그 local state는 사라진다.

이것은 durable Conversation object와 중요한 차이다.

## 2.5 Mode B: `previous_response_id`로 response lineage를 잇는다

두 번째 방식은 첫 response의 ID를 다음 call에 넘기는 것이다.

```python
first = client.responses.create(
    model="gpt-5.6-luna",
    input="My project codename is Juniper.",
)

second = client.responses.create(
    model="gpt-5.6-luna",
    previous_response_id=first.id,
    input="What is my project codename?",
)
```

application이 보관하는 핵심 state가 크게 달라진다.

```text
manual history
application keeps: input/output item history

response lineage
application keeps: previous response ID
```

공식 documentation은 `previous_response_id`를 이용해 generated responses를 chain하고 threaded conversation을 구성할 수 있다고 설명한다.

여기서 중요한 mental model은 다음이다.

```text
previous_response_id
!=
"SDK client object가 메모리에 모든 대화를 자동 저장한다"
```

두 번째 request가 연결되는 이유는 application이 **명시적으로 이전 Response resource의 identifier를 제공했기 때문**이다.

## 2.6 worked trace: lineage에서는 어떤 state가 이동하는가

```text
first call
application input A
      ↓
API
      ↓
Response(id=resp_1, output=...)

application keeps resp_1
      ↓
second call
previous_response_id=resp_1
input B
      ↓
API resolves prior response context
      ↓
Response(id=resp_2, output=...)
```

두 call 사이에서 application이 반드시 전체 `first.output` list를 다시 보내는 것은 아니다.

대신 다음 state transition을 이해한다.

```text
application-owned value
first.id

becomes

second request argument
previous_response_id
```

이것이 lineage ownership의 핵심이다.

## 2.7 Mode C: durable Conversation object를 사용한다

세 번째 방식은 별도 Conversation object를 만든 뒤 그 ID를 subsequent response에 연결하는 것이다.

```python
conversation = client.conversations.create()

first = client.responses.create(
    model="gpt-5.6-luna",
    conversation=conversation.id,
    input="My project codename is Juniper.",
)

second = client.responses.create(
    model="gpt-5.6-luna",
    conversation=conversation.id,
    input="What is my project codename?",
)
```

공식 documentation은 Conversations API를 Responses API와 함께 사용해 **고유한 durable identifier를 가진 long-running conversation object**로 state를 persist할 수 있다고 설명한다.

conversation에는 message뿐 아니라 tool call, tool output 등 item이 들어갈 수 있다.

### ownership

application은 여전히 아무 state도 없는 것이 아니다.

최소한 다음을 소유한다.

```text
conversation.id
이 conversation을 어느 user/session/job에 연결할지에 대한 application mapping
lifecycle policy
```

하지만 prior item history 자체를 매 call마다 application이 직접 재구성해서 보내는 것과는 다르다.

## 2.8 세 가지 mode를 한 표에서 비교한다

| 질문 | Manual history | `previous_response_id` | Conversation |
| --- | --- | --- | --- |
| application이 다음 turn 전에 보관하는 핵심 | prior input/output items | prior response ID | conversation ID |
| next call에 history 전체를 직접 다시 구성 | 예 | 아니오 | 아니오 |
| API-side resource identity로 연결 | 필수 아님 | Response ID | Conversation ID |
| 여러 session/job에 걸친 durable object가 core abstraction인가 | 아니오 | response chain | 예 |
| application이 state policy를 강하게 통제 | 가장 큼 | 중간 | conversation lifecycle 중심 |

이 표를 "어떤 방식이 항상 최고인가"로 읽지 않는다.

선택은 application requirement에 따라 달라진다.

## 2.9 선택 질문: state를 어디에 두고 싶은가

### manual history가 자연스러운 경우

- application이 context item을 직접 inspect/transform해야 한다.
- external database나 application session state가 이미 conversation history의 owner다.
- 어떤 item을 다음 request에 넣을지 application이 명시적으로 결정해야 한다.

### response lineage가 자연스러운 경우

- 직전 response를 중심으로 간단히 turn을 이어가고 싶다.
- 전체 prior item을 application에서 매번 재조립하고 싶지 않다.
- response resource identity로 chain을 표현하는 것이 충분하다.

### Conversation이 자연스러운 경우

- 하나의 long-running conversation identity가 필요하다.
- session/device/job boundary를 넘어 같은 conversation object를 다시 사용해야 한다.
- tool call/output을 포함한 conversation items를 durable object에 축적하는 model이 application에 맞는다.

이것은 architecture recipe가 아니라 **state ownership을 판단하기 위한 질문**이다.

## 2.10 Observable Lab A: network 없이 call plan을 비교한다

playground는 세 mode 모두 preview를 제공한다.

```bash
python playground/conversation_state.py --mode manual --preview
python playground/conversation_state.py --mode lineage --preview
python playground/conversation_state.py --mode conversation --preview
```

각 output에서 다음을 표시한다.

```text
application이 직접 가진 state
second call에 전달되는 argument
API-side identity가 필요한지
```

이 preview는 SDK serialization이나 실제 API persistence를 검증하지 않는다. **application-side call plan과 ownership model만 확인한다.**

다음 질문에 답한다.

1. manual mode의 두 번째 call에서 가장 큰 application-owned value는 무엇인가?
2. lineage mode에서 첫 response의 어떤 field가 다음 request argument가 되는가?
3. conversation mode에서는 response ID 대신 어떤 durable identity를 계속 사용하게 되는가?

## 2.11 Observable Lab B: manual history를 live로 관찰한다

valid API key가 있는 environment에서 실행한다.

```bash
uv run playground/conversation_state.py --mode manual
```

playground는 first response 뒤 application-owned history의 item 수와 type을 보여준다.

관찰한다.

```text
first response.id
first output item types
second call 직전 history item types
second response.id
```

중요한 것은 follow-up 답이 "Juniper"인지 여부만이 아니다.

> second request가 context를 가진 이유를 application history mutation으로 설명할 수 있는가?

## 2.12 Observable Lab C: lineage를 live로 관찰한다

```bash
uv run playground/conversation_state.py --mode lineage
```

첫 response 뒤 다음 값을 확인한다.

```text
response_id: ...
```

그리고 playground가 그 값을 `previous_response_id`로 사용해 두 번째 request를 만든다는 것을 code와 output에서 연결한다.

다음을 설명한다.

```text
first.id
→ application state
→ second request.previous_response_id
→ API-side context resolution
```

## 2.13 Observable Lab D: durable Conversation identity를 관찰한다

```bash
uv run playground/conversation_state.py --mode conversation
```

먼저 생성되는 값은 Response ID가 아니라 Conversation ID다.

```text
conversation_id: ...
```

그 다음 first/second response 모두 같은 `conversation.id`를 사용한다.

질문한다.

- 두 response의 `response.id`는 같은가?
- conversation ID는 같은가?
- application이 long-running identity로 들고 있어야 하는 것은 어느 값인가?

Response resource와 Conversation resource를 하나의 "대화 ID"로 뭉개지 않는다.

## 2.14 비용/retention을 state ownership과 혼동하지 않는다

`previous_response_id`가 편하다고 해서 이전 context token이 무료가 되는 것은 아니다. 공식 conversation-state documentation은 response chain에서 prior input token도 input token으로 계산된다고 명시한다.

또한 Response object와 Conversation object는 persistence semantics가 다르다.

이런 detail은 중요한 운영 조건이지만 이번 chapter의 핵심 abstraction은 다음이다.

```text
state ownership
persistence
billing
```

세 축은 관련되지만 같은 개념이 아니다.

application architecture를 결정할 때 각각 확인한다.

## 2.15 흔한 잘못된 mental model

### "OpenAI client가 이전 request를 자동으로 기억한다"

`OpenAI()` client object를 재사용하는 것만으로 conversation context가 자동 연결된다고 생각하지 않는다. manual input, `previous_response_id`, Conversation 같은 명시적 state mechanism을 본다.

### "`output_text`만 저장하면 response history를 완전히 보존한다"

text-only application에서는 충분할 수 있지만 Responses API output에는 다른 item type이 존재할 수 있다. context fidelity가 필요하면 output item model을 이해해야 한다.

### "`previous_response_id`를 쓰면 application state가 없다"

application은 최소한 어떤 response ID를 어떤 user/session flow에 연결할지 소유한다.

### "Conversation이 있으면 response ID는 필요 없다"

Conversation과 Response는 다른 resource다. debugging, observability, lineage에는 response/request identity가 여전히 의미가 있다.

### "state persistence와 context ownership과 비용은 같은 문제다"

별도 축이다. 어떤 object가 state를 소유하는지, 얼마나 유지되는지, token billing이 어떻게 되는지는 따로 확인한다.

## 2.16 Practice

### A. Trace

manual mode에서 다음 값을 시간 순서대로 추적한다.

```text
history
first.output
followup user item
second input
```

각 단계에서 application이 직접 mutation하는 state를 표시한다.

### B. Compare

다음 요구에 가장 적절한 mode를 하나 선택하고 이유를 설명한다.

```text
application DB가 이미 chat history의 canonical owner이며
각 turn 전에 일부 system-generated item을 필터링해야 한다.
```

후보:

```text
manual history
response lineage
Conversation
```

### C. Debug

개발자가 같은 `OpenAI()` object로 두 번 `responses.create()`를 호출했는데 두 번째 response가 첫 질문을 기억하지 못한다고 한다.

client reuse와 conversation state connection이 왜 다른지 설명하고, 세 가지 해결 방향을 제시한다.

### D. Boundary repair

다음 helper를 검토한다.

```python
def continue_chat(client, previous_text, prompt):
    return client.responses.create(
        model="gpt-5.6-luna",
        input=f"Assistant: {previous_text}\nUser: {prompt}",
    )
```

이 helper가 text-only transcript를 재구성한다는 점과 Responses API output item fidelity 사이의 tradeoff를 설명한다. application requirement가 tool calling까지 확장된다면 어떤 state model이 더 안전한지 판단한다.

## Assessment checkpoint

이번 chapter는 다음 과제를 독립적으로 수행할 수 있을 때 통과한다.

### 1. Ownership map

세 mode를 다음 축으로 비교한다.

```text
application-owned state
API-side identity
next request argument
persistence model
failure/debugging에 필요한 identifiers
```

단순 feature 정의가 아니라 **call 사이에 어떤 값이 실제로 이동하거나 유지되는지**를 설명해야 한다.

### 2. State design

다음 세 application requirement 각각에 대해 state model을 선택하고 정당화한다.

1. application DB가 history의 source of truth다.
2. 짧은 request chain을 직전 response ID로 이어가면 충분하다.
3. 여러 job/session에 걸쳐 같은 durable conversation identity가 필요하다.

평가 기준:

- manual history, response lineage, Conversation의 ownership 차이를 구분했는가?
- `Response.id`, `conversation.id`, `_request_id`를 역할별로 혼동하지 않았는가?
- `output_text`와 전체 `output`의 차이를 설명했는가?
- persistence/billing을 state ownership과 별도 축으로 인식했는가?

이 기준을 만족하면 Unit 2의 핵심 outcome인 **conversation context를 누가 소유하고 어떤 identifier/data가 turn 사이를 연결하는지 판단하는 능력**을 갖춘 것으로 본다.
