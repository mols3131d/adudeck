# 3장 · OpenAI Integration과 Generation

Manual instrumentation만으로 LLM call의 model, token usage, latency 같은 값을 직접 기록하려면 코드가 빠르게 늘어난다.
Langfuse integration은 provider SDK call을 instrument해서 **generation observation**을 자동으로 만드는 데 도움을 준다.

하지만 자동 instrumentation이 application 의미까지 알아주는 것은 아니다.

## 학습 목표

- 일반 span과 generation observation의 역할을 구분한다.
- OpenAI integration이 자동 capture하는 정보와 application이 직접 표현해야 하는 정보를 구분한다.
- business operation span 안에 generation이 child로 들어가는 구조를 설명한다.
- automatic instrumentation이 domain correctness를 판단하지 않는다는 점을 설명한다.

## 1. Generation은 LLM call을 표현한다

Trace 안에서 LLM 호출은 보통 generation으로 표현한다.

```text
support-turn           span
├─ search-policy       span
└─ answer-generation   generation
```

Generation에는 일반 span보다 LLM-specific 정보가 중요하다.

- model
- input messages / prompt
- output
- token usage
- latency
- cost 계산에 필요한 정보

Provider integration이 지원하면 이 중 상당수를 자동으로 수집할 수 있다.

## 2. OpenAI integration

현재 Python SDK에서는 Langfuse의 OpenAI integration client를 사용할 수 있다.

```python
import os

from langfuse import get_client
from langfuse.openai import OpenAI

langfuse = get_client()
client = OpenAI()

with langfuse.start_as_current_observation(
    as_type="span",
    name="support-turn",
    input={"question": "환불 기간은?"},
) as root:
    response = client.chat.completions.create(
        model=os.environ["OPENAI_MODEL"],
        messages=[
            {"role": "user", "content": "환불 기간은?"},
        ],
    )

    answer = response.choices[0].message.content
    root.update(output={"answer": answer})

langfuse.flush()
```

이 code의 핵심은 OpenAI call이 자동으로 generation observation을 만들 수 있다는 점이다.
Root business span은 “support turn”의 의미를 표현하고, provider integration은 그 안의 model call을 자세히 기록한다.

## 3. 자동화되는 것과 자동화되지 않는 것

Integration이 잘할 수 있는 것:

```text
model call boundary
model parameters
messages
response
usage
latency
```

Application이 직접 결정해야 하는 것:

```text
이 request의 business 의미
retrieval operation boundary
validation result
user/session context
어떤 값이 sensitive한지
어떤 output이 올바른지
```

그래서 “OpenAI integration을 켰다 = observability가 끝났다”가 아니다.

## 4. Manual generation과 integration을 비교한다

학습용으로 다음 두 구조를 비교한다.

```text
A. manual
support-turn
└─ generation을 직접 생성하고 model/input/output/usage를 update

B. integration
support-turn
└─ OpenAI SDK call이 generation을 자동 생성
```

예측할 것:

- 어떤 코드가 사라지는가?
- 어떤 application-level span은 여전히 필요할까?
- provider를 바꾸면 어떤 부분이 달라질까?
- correctness score는 어느 방식에서도 자동으로 생기지 않는 이유가 무엇일까?

## 5. Cost와 token은 결과가 아니라 evidence다

Token usage와 cost는 application quality와 별개의 dimension이다.

```text
quality ↑, cost ↑
quality ↓, cost ↓
latency ↓, quality ↔
```

같은 trade-off가 가능하다.
Langfuse는 generation을 중심으로 usage/cost를 관찰할 수 있지만 “비싼 것이 나쁘다” 같은 정책은 application/evaluation 쪽에서 결정해야 한다.

## 6. Live API 실습의 경계

실제 OpenAI call은 API credential과 비용을 사용한다.
따라서 이 장의 runnable playground를 구현할 때는:

- credential을 Git에 기록하지 않는다.
- model name은 environment/config에서 주입한다.
- 최소 request 수로 실습한다.
- provider failure와 Langfuse export failure를 구분한다.

Langfuse 전송이 실패했다고 application의 LLM call 자체를 성공으로 가장하거나 반대로 바꾸면 안 된다.

## 이해도 점검

다음 구조가 있다고 하자.

```text
answer-request
├─ retrieve-context
└─ openai generation
```

1. generation은 누가 만드는 것이 적절한가?
2. `retrieve-context`는 왜 OpenAI integration이 자동으로 알 수 없는가?
3. 답변 correctness는 왜 token usage로 대체할 수 없는가?
4. root span이 없어 OpenAI generation 하나만 보인다면 어떤 application context를 잃을 수 있는가?

## 다음 장

다음 장에서는 실행을 “관찰”하는 것에서 한 단계 나아가, application이 계산한 평가 결과를 **score**로 연결한다.

## References

- [Get Started with LLM Tracing](https://langfuse.com/docs/observability/get-started)
- [Observability Overview](https://langfuse.com/docs/observability/overview)
- [Langfuse Python SDK](https://python.reference.langfuse.com/)
