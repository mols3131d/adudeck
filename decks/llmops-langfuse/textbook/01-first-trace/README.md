# 1장 · 첫 Trace와 Observation

이번 장에서는 OpenAI나 LangChain을 붙이지 않는다.
먼저 Python 작업 자체를 Langfuse data model로 표현한다.

## 학습 목표

- trace와 observation의 관계를 설명한다.
- root observation과 child observation을 구분한다.
- `start_as_current_observation()`이 current context를 이용해 관계를 만드는 방식을 설명한다.
- 짧은 script에서 `flush()`가 필요한 이유를 설명한다.

## 1. observations-first mental model

현재 Langfuse Python SDK v4는 **observation을 중심으로** 생각한다.

```text
trace
└─ root observation
   ├─ child observation
   └─ child observation
```

Observation은 application execution의 한 작업이다.
예를 들면 retrieval, parsing, tool call, LLM generation이 각각 observation이 될 수 있다.

Trace는 관련 observation들을 하나의 실행으로 묶는다.
Session은 여러 trace를 더 큰 사용자 interaction 단위로 묶을 수 있다.

```text
session
├─ trace: turn-1
│  ├─ observation
│  └─ observation
└─ trace: turn-2
   ├─ observation
   └─ observation
```

## 2. 첫 observation

현재 Python SDK의 기본 client entrypoint는 `get_client()`다.

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span",
    name="process-request",
    input={"question": "환불 기간은?"},
) as root:
    result = {"answer": "14일"}
    root.update(output=result)

langfuse.flush()
```

이 코드에서 중요한 것은 syntax보다 lifetime이다.

```text
with 진입
→ observation 시작 + current context 설정
→ application work
→ output update
→ with 종료
→ observation 종료
```

짧게 실행되고 바로 종료되는 script에서는 background export가 끝나기 전에 process가 종료될 수 있다.
그래서 학습용 short-lived script에서는 마지막에 `flush()`를 명시적으로 호출하는 편이 관찰 경계를 이해하기 쉽다.

## 3. child observation 만들기

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span",
    name="support-turn",
    input={"question": "환불 기간은?"},
) as root:
    with langfuse.start_as_current_observation(
        as_type="span",
        name="search-policy",
        input={"query": "환불 기간"},
    ) as search:
        document = "구매 후 14일 이내 환불 가능"
        search.update(output={"document": document})

    root.update(output={"answer": "14일"})

langfuse.flush()
```

`search-policy`는 별도 parent ID를 직접 전달하지 않았다.
그런데도 `support-turn` 안에서 시작했으므로 current context를 통해 같은 trace의 child observation이 된다.

이 구조는 OpenTelemetry span context와 비슷한 사고방식을 사용한다.
Langfuse Python SDK v4가 OpenTelemetry 기반이라는 사실은 이후 integration을 이해할 때 다시 사용한다.

## 4. 실행 전에 예측할 것

실습으로 옮길 때는 UI를 먼저 열지 않는다. 먼저 다음을 예상한다.

1. trace는 몇 개 생길까?
2. observation은 몇 개 생길까?
3. `search-policy`의 parent는 무엇일까?
4. `support-turn`과 `search-policy`는 같은 trace일까?
5. `search-policy` block이 끝난 뒤 current observation은 무엇으로 복원될까?

## 5. `@observe()`는 같은 문제를 더 짧게 푼다

Langfuse는 decorator도 제공한다.

```python
from langfuse import observe

@observe()
def search_policy(query: str) -> str:
    return "구매 후 14일 이내 환불 가능"

@observe()
def support_turn(question: str) -> str:
    policy = search_policy(question)
    return f"정책: {policy}"
```

Decorator는 function input/output, timing, error를 자동으로 capture하기 편하다.
하지만 처음부터 decorator만 사용하면 **observation lifetime과 current context**가 감춰질 수 있다.
이 deck이 context manager부터 시작하는 이유다.

## 6. 비교 문제

다음 두 코드를 비교한다.

```text
A
with root observation:
    child()

B
with root observation:
    pass
child()
```

`child()`가 내부에서 새 observation을 만든다고 가정한다.

- A와 B에서 trace 개수는 어떻게 달라질까?
- B의 child observation은 왜 root의 child가 아니게 되는가?

함수 호출 관계가 아니라 **active observation context**가 관계를 만든다는 점을 설명해 본다.

## 오해하기 쉬운 점

- 함수 하나가 자동으로 observation 하나라는 뜻은 아니다.
- trace는 “함수 call tree” 그 자체가 아니다.
- 모든 함수에 observation을 만들 필요도 없다.
- 의미 있는 operation boundary를 선택해야 한다.

## 다음 장

다음 장에서는 observation을 많이 만드는 법이 아니라
**나중에 사람이 읽고 evaluator가 사용할 수 있는 trace를 어떻게 설계할지** 다룬다.

## References

- [Langfuse SDK Overview](https://langfuse.com/docs/observability/sdk/overview)
- [SDK Instrumentation](https://langfuse.com/docs/observability/sdk/instrumentation)
- [Python SDK Reference](https://python.reference.langfuse.com/)
