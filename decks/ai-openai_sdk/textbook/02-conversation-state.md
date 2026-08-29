# 2. Conversation state: "이전 대화"를 누가 소유하는가

한 번의 `responses.create()`는 현재 request의 input을 처리한다. Multi-turn interaction에서 중요한 질문은
"model이 기억하는가?"가 아니라 다음이다.

> **다음 request가 사용할 context를 누가 보관하고, 어떤 값으로 이어 주는가?**

Responses API에서는 세 가지 state model을 구분해 두면 대부분의 설계가 단순해진다.

| 방식 | application이 보관하는 핵심 | 다음 call의 연결 방식 |
| --- | --- | --- |
| manual history | prior input/output items | history 전체를 다시 `input`으로 보냄 |
| response lineage | 이전 `response.id` | `previous_response_id` |
| Conversation | `conversation.id` | 같은 durable Conversation을 계속 사용 |

세 방식 모두 multi-turn을 만들 수 있지만 **state owner와 persistence boundary가 다르다.**

## 2.1 기본값: 연결하지 않으면 별개의 call이다

```python
first = client.responses.create(
    model="...",
    input="My project codename is Juniper.",
)

second = client.responses.create(
    model="...",
    input="What is my project codename?",
)
```

두 번째 call에 prior context를 연결하는 정보가 없다. 따라서 "client object가 알아서 이전 turn을 기억한다"는 mental model은
버린다.

```text
current request context
= application이 보낸 input
+ application이 명시적으로 연결한 API-side state
```

## 2.2 Manual history: application이 context를 직접 구성한다

가장 명시적인 방식은 application이 이전 item을 직접 보관하는 것이다.

```python
history = [
    {"role": "user", "content": "My project codename is Juniper."},
]

first = client.responses.create(
    model="...",
    input=history,
    store=False,
)

history += first.output
history.append(
    {"role": "user", "content": "What is my project codename?"}
)

second = client.responses.create(
    model="...",
    input=history,
    store=False,
)
```

여기서 핵심은 `first.output_text`만 복사하지 않고 **response output items를 context로 유지한다는 것**이다. Text가 아닌
output item이 등장할 수 있기 때문이다.

Manual mode에서 application은 다음 책임까지 소유한다.

```text
어떤 item을 보관할지
어디에 persist할지
언제 truncate/summarize할지
다음 request에 어떤 history를 넣을지
```

`store=False`는 이 실험에서 Response 저장을 끄는 설정이다. 이것을 "모든 platform-side retention이 사라진다"는
privacy/compliance 결론으로 확대하지 않는다.

## 2.3 Response lineage: history 대신 이전 Response ID를 연결한다

```python
first = client.responses.create(
    model="...",
    input="My project codename is Juniper.",
)

second = client.responses.create(
    model="...",
    previous_response_id=first.id,
    input="What is my project codename?",
)
```

두 call 사이에서 application이 보관하는 핵심 state가 바뀐다.

```text
manual
prior input/output items

lineage
first.id
```

`previous_response_id`는 **이전 Response resource를 다음 request에 명시적으로 연결하는 argument**다. SDK client가 local
memory에서 conversation을 자동 복원하는 기능으로 이해하지 않는다.

## 2.4 Conversation: long-running identity를 별도 resource로 둔다

```python
conversation = client.conversations.create()

first = client.responses.create(
    model="...",
    conversation=conversation.id,
    input="My project codename is Juniper.",
)

second = client.responses.create(
    model="...",
    conversation=conversation.id,
    input="What is my project codename?",
)
```

이 방식에서는 Conversation이 durable state container의 중심이 된다. Application은 여전히
`conversation.id`와 그것을 어느 user/session/job에 연결할지 소유한다.

다음 identifier를 섞지 않는다.

```text
response.id
→ 한 Response resource

conversation.id
→ 여러 turn을 연결하는 Conversation resource
```

## 2.5 선택 기준: "어떤 API가 편한가"보다 state owner를 본다

| 요구 | 우선 검토할 방식 |
| --- | --- |
| application이 context item을 직접 inspect/transform해야 함 | manual history |
| 직전 Response를 간단히 이어 가면 충분함 | `previous_response_id` |
| session/device/job을 넘어 유지할 long-running identity가 필요함 | Conversation |

이 표는 정답표가 아니다. 특히 persistence, data-control, token-cost requirement가 중요하면 해당 요구를 별도로 검토한다.
`previous_response_id`를 쓴다고 prior context token cost가 사라지는 것도 아니다.

## 2.6 Worked trace: 두 번째 request 직전 무엇이 존재하는가

같은 첫 turn을 세 방식으로 실행했다고 하자.

```text
user: My project codename is Juniper.
```

두 번째 turn 직전 state를 비교한다.

```text
manual
application:
  [user item, first.output..., followup user item]

lineage
application:
  first.id
  followup user input

conversation
application:
  conversation.id
  followup user input
```

질문은 하나다.

> **두 번째 request가 prior context를 사용할 수 있게 만드는 값은 정확히 무엇인가?**

이 질문에 답할 수 있으면 "model memory"라는 모호한 표현 없이 state flow를 설명할 수 있다.

## 2.7 Playground: 같은 질문을 세 ownership model로 비교한다

먼저 network 없이 call plan을 본다.

```bash
python playground/conversation_state.py --mode manual --preview
python playground/conversation_state.py --mode lineage --preview
python playground/conversation_state.py --mode conversation --preview
```

Preview에서 확인할 것은 세 가지뿐이다.

1. application이 call 사이에 무엇을 보관하는가?
2. 두 번째 call에 어떤 argument가 추가되는가?
3. API-side resource identity가 필요한가?

Preview는 SDK serialization, 실제 API persistence, model behavior를 검증하지 않는다.

Live access가 있다면 같은 순서로 실행한다.

```bash
uv run playground/conversation_state.py --mode manual
uv run playground/conversation_state.py --mode lineage
uv run playground/conversation_state.py --mode conversation
```

관찰 결과를 다음 표로 기록한다.

| Mode | first call 뒤 application state | second call 연결 evidence |
| --- | --- | --- |
| manual | | |
| lineage | | |
| conversation | | |

답변 text가 맞았다는 사실만 기록하지 않는다. **왜 두 번째 call에 context가 있었는지**를 state evidence로 설명한다.

### Validation boundary

- `--preview`: application-owned call plan만 검증
- live manual: history mutation + API response를 관찰
- live lineage: `response.id → previous_response_id` 연결을 관찰
- live conversation: 같은 `conversation.id`가 여러 Response에 연결되는 것을 관찰
- 어느 경로도 privacy/compliance policy나 domain correctness를 대신 검증하지 않음

## 2.8 흔한 오해

### "`OpenAI()` client가 conversation을 기억한다"

아니다. Context는 application이 다시 보내거나, `previous_response_id` 또는 Conversation resource로 명시적으로 연결한다.

### "`output_text`만 transcript에 넣으면 항상 충분하다"

Text-only case에는 가능할 수 있지만 Response에는 text 외 item이 존재할 수 있다. Manual history에서는 필요한 output item
전체를 보존하는 이유를 이해해야 한다.

### "Conversation을 쓰면 application state가 0이 된다"

아니다. Application은 최소한 Conversation ID의 ownership과 lifecycle mapping을 관리한다.

### "`store=False`는 모든 data retention을 끈다는 뜻이다"

이번 chapter에서는 Response 저장 설정의 좁은 의미만 사용한다. broader data-control 판단은 별도 current policy surface를
확인해야 한다.

## 2.9 Practice

### A. State trace

다음 세 application state를 보고 mode를 분류하고, second request에 필요한 값을 적는다.

```text
1. [user item, output items, next user item]
2. resp_123
3. conv_456
```

### B. Design choice

다음 요구에 대해 ownership model을 선택하고 이유를 설명한다.

- application DB가 이미 canonical chat history를 소유한다.
- 한 process 안에서 직전 answer를 이어 가는 간단한 assistant다.
- 여러 device에서 같은 long-running support conversation을 이어야 한다.

API 이름보다 **누가 state를 소유해야 하는지**를 근거로 답한다.

### C. Debugging

Follow-up이 prior context를 전혀 반영하지 않는다. 다음 순서로 조사한다.

```text
application이 기대한 state를 실제로 보관했는가?
→ second call에 연결 argument가 들어갔는가?
→ 연결한 resource/ID가 의도한 것인가?
→ 그 뒤에야 model output을 해석한다
```

## Assessment checkpoint

다음을 독립적으로 할 수 있으면 통과한다.

1. 세 ownership model에서 **call 사이에 application이 보관하는 state**를 정확히 그린다.
2. "대화를 이어야 한다"는 요구 하나를 받아 manual / lineage / Conversation 중 하나를 선택하고, persistence와 control
   trade-off를 설명한다.
3. Preview evidence와 live API evidence를 구분한다.
