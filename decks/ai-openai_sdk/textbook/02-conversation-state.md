# 2. Conversation state: 다음 request가 이전 turn을 아는 이유

두 번 `responses.create()`를 호출했다고 해서 client가 자동으로 이전 대화를 기억하지 않는다.

핵심 질문은 이것이다.

> 두 번째 request에 prior context를 연결하는 값은 무엇인가?

이번 unit에서는 같은 문제를 세 방식으로 본다.

```text
manual history
previous_response_id
Conversation
```

각 방식은 별도 작은 file로 나뉜다. 한 번에 거대한 multi-mode script를 읽지 않는다.

## 2.1 가장 작은 연결: `previous_response_id`

먼저 실행한다.

```bash
uv run playground/conversation_state/lineage.py
```

핵심은 두 번째 call의 한 argument다.

```python
second = client.responses.create(
    model=model,
    previous_response_id=first.id,
    input="What project codename did I give you? Reply with the codename only.",
)
```

첫 call 뒤 application이 보관한 값:

```text
first.id
```

두 번째 call에서 그 값을:

```text
previous_response_id=first.id
```

로 사용한다.

### 직접 끊어 보기

`previous_response_id=first.id` 줄을 잠시 지우고 다시 실행한다.

실행 전에 예측한다.

- 두 번째 request에 이전 turn을 연결하는 값이 남아 있는가?
- follow-up이 codename을 맞힐 근거가 있는가?

관찰 후 원래 줄을 복구한다.

`previous_response_id`는 application이 prior content 전체를 다시 보내지 않고 Response lineage를 가리키는 방식이다. 현재
standard API behavior에서는 Response object가 기본적으로 30일 저장되며, `store=False`를 사용하면 이 저장을 끌 수 있다.
따라서 lineage 방식은 application이 ID만 보관하더라도 그 ID가 가리키는 remote Response lifecycle과 무관하지 않다.

## 2.2 Manual history: application이 context item을 직접 들고 간다

다음 file을 실행한다.

```bash
uv run playground/conversation_state/manual_history.py
```

핵심은 application이 `history`를 직접 변경한다는 점이다.

```python
history = [{"role": "user", "content": first_prompt}]

first = client.responses.create(
    model=model,
    input=history,
    store=False,
)

history += first.output
history.append({"role": "user", "content": followup})
```

두 번째 call 직전 application memory에는 prior user item, prior output item, 새 user item이 함께 있다.
이 lab은 `store=False`를 사용하므로 다음 turn을 위한 context ownership을 application 쪽에 명시적으로 둔다.

### 직접 관찰하기

두 번째 call 바로 전에 다음 줄을 추가한다.

```python
print([getattr(item, "type", "input_message") for item in history])
```

질문:

- `output_text` 문자열만 추가하지 않고 `first.output` item을 보관하는 이유는 무엇인가?
- 다음 unit에서 function call 같은 non-text output이 등장하면 이 차이가 왜 중요해지는가?

## 2.3 Conversation: 별도 durable resource를 사용한다

다음 file을 실행한다.

```bash
uv run playground/conversation_state/conversation.py
```

핵심 state는 `conversation.id`다.

```python
conversation = client.conversations.create()

first = client.responses.create(
    model=model,
    conversation=conversation.id,
    input=first_prompt,
)

second = client.responses.create(
    model=model,
    conversation=conversation.id,
    input=followup,
)
```

Application은 Conversation resource 자체를 local memory에 보관하는 것이 아니라,
그 resource를 가리키는 ID와 자신의 user/session/job mapping을 관리한다.

여기서는 **remote state의 lifetime**도 함께 봐야 한다. Conversation에 붙은 item은 일반 Response의 기본 30일 TTL 대상이
아니다. 즉, `conversation.id`는 단순한 편의용 pointer가 아니라 durable server-side state의 identity다.

또 하나 중요한 cleanup boundary가 있다.

```text
conversation container 삭제
!=
conversation item 삭제
```

현재 API에서 `client.conversations.delete(conversation.id)`는 Conversation container를 삭제하지만 그 안의 item까지
삭제하지는 않는다. 그래서 playground는 종료 전에 저장된 item ID를 직접 관찰한 뒤 item을 하나씩 삭제하고 마지막에
Conversation container를 삭제한다.

```python
items = list(client.conversations.items.list(conversation.id, order="asc", limit=100))
print([item.id for item in items])

for item in items:
    client.conversations.items.delete(item.id, conversation_id=conversation.id)

client.conversations.delete(conversation.id)
```

이 cleanup code는 production lifecycle policy의 완성형이 아니라, 이 lab이 만든 remote state를 남기지 않기 위한 teaching
boundary다.

## 2.4 세 방식을 같은 질문으로 비교한다

| 방식 | call 사이에 application이 보관하는 핵심 state | 다음 call 연결 | remote state / lifetime 관점 |
| --- | --- | --- | --- |
| manual history | prior input/output items | history 전체를 `input`으로 보냄 | 이 lab은 `store=False`; next-turn context는 application이 직접 보관 |
| lineage | `response.id` | `previous_response_id` | Response는 기본적으로 30일 저장되므로 remote Response lifetime에 의존 |
| Conversation | `conversation.id` | 같은 `conversation` 사용 | Conversation item은 일반 Response의 30일 TTL 대상이 아니며 명시적 lifecycle 관리가 필요 |

중요한 것은 "어떤 API가 더 멋진가"가 아니다.

다음 질문으로 선택한다.

```text
context item을 application이 직접 inspect/transform해야 하는가?
직전 Response만 간단히 이어 가면 되는가?
long-running identity가 별도 resource로 필요한가?
remote state를 얼마나 오래 유지하고 어떻게 정리할 것인가?
```

## 2.5 Ollama compatibility 주의

이 unit은 official OpenAI Responses API의 stateful features를 학습한다.

현재 Ollama의 `/v1/responses` compatibility는 non-stateful subset이며
`previous_response_id`와 `conversation`을 지원하지 않는다.

따라서 Unit 1의 stateless example이 Ollama에서 동작했다는 사실만으로
이 unit도 같은 방식으로 동작한다고 가정하지 않는다.

## Practice

다음 state만 보고 어떤 방식인지 분류한다.

```text
A. [user item, output items, next user item]
B. resp_123
C. conv_456
```

각 경우 두 번째 request가 prior context를 사용할 수 있게 만드는 값을 직접 적는다.
그다음 각 방식에서 **application-owned state**와 **remote state lifetime**을 따로 적는다.

## Checkpoint

세 방식 중 하나를 선택해 다음 requirement를 설계한다.

> 여러 process restart 이후에도 같은 support session을 이어야 한다.

선택한 방식에서 application이 반드시 보관해야 하는 state, remote state의 lifetime, cleanup 책임을 함께 설명한다.
정답은 API 이름보다 ownership과 lifecycle requirement에 달려 있다.
