# 2장 · 좋은 Trace 설계하기

Trace가 보인다고 observability가 완성된 것은 아니다.
나중에 filter, evaluator, dataset, experiment에서 다시 사용할 수 있어야 좋은 trace다.

이번 장의 핵심 질문은 다음이다.

> **몇 달 뒤에도 의미를 잃지 않는 observation을 어떻게 설계할까?**

## 학습 목표

- stable observation name과 run-specific value를 구분한다.
- input/output, metadata, tags의 역할을 구분한다.
- user/session 같은 correlating attribute를 child observation에 전파하는 이유를 설명한다.
- sensitive data를 trace에 무조건 넣으면 안 되는 이유를 설명한다.

## 1. 이름은 operation을 표현한다

나쁜 이름:

```text
search-policy-user-18472
call-gpt-5-20261001
request-1f92a3
```

좋은 이름:

```text
search-policy
answer-generation
validate-answer
```

Observation name은 반복 가능한 **operation type**을 표현하는 편이 좋다.
user ID, request ID, model version처럼 매 실행마다 달라지는 값은 metadata나 별도 attribute가 더 적절하다.

Model 이름도 observation name에 넣지 않는다.
Model은 generation attribute로 기록할 수 있기 때문에 model 교체만으로 dashboard/evaluator filter가 깨지지 않게 한다.

## 2. root input/output은 reviewer의 첫 화면이다

Root observation의 input/output은 trace 전체를 이해하는 데 가장 중요한 값이다.

예를 들어 chatbot이면:

```text
root input
= user message

root output
= final assistant response
```

반대로 raw request object 전체를 root input으로 넣으면 중요한 질문이 bury될 수 있다.
원본 payload가 필요하면 metadata에 두는 편이 더 읽기 쉽다.

## 3. metadata와 tags

Metadata는 디버깅 context다.

```python
metadata = {
    "route": "/support",
    "app_revision": "abc123",
    "retriever": "policy-index-v2",
}
```

Tags는 business-level grouping처럼 creation 시점에 알고 있는 안정적인 분류에 적합하다.

```text
channel:web
feature:support
experiment:refund-v2
```

실행이 끝난 뒤 알게 된 “좋은 답/나쁜 답” 같은 판단은 tag보다 score가 자연스럽다.

## 4. correlating attributes는 context로 전파한다

Python SDK v4에서는 user/session/tags/metadata 같은 correlating attribute를 `propagate_attributes()`로 current context
아래에 전파하는 방식이 중요하다.

```python
from langfuse import get_client, propagate_attributes

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span",
    name="support-turn",
) as root:
    with propagate_attributes(
        user_id="user-123",
        session_id="session-abc",
        tags=["support", "web"],
        metadata={"app_revision": "abc123"},
    ):
        with langfuse.start_as_current_observation(
            as_type="span",
            name="search-policy",
        ):
            pass
```

v4의 observations-first model에서는 이런 correlating attributes가 child observations에도 함께 존재하는 것이 query와
분석에 유리하다. 오래된 v3 tutorial의 `update_current_trace()` pattern을 새 코드의 기본 경로로 가져오지 않는다.

## 5. trace를 너무 잘게 쪼개지 않는다

다음 Python 함수가 있다고 하자.

```text
normalize_text()
strip_whitespace()
lowercase()
search_policy()
rerank_results()
call_model()
validate_answer()
```

모든 함수를 observation으로 만들면 구조는 자세해지지만 사람이 읽기 어려워질 수 있다.

질문은 이것이다.

> 실패 원인을 구분하거나 latency/cost를 이해하거나 evaluation target으로 삼기 위해 이 boundary가 필요한가?

필요한 operation만 instrument한다.

## 6. sensitive data는 관찰 가능성보다 먼저 경계를 정한다

LLM trace에는 prompt, response, retrieved text가 들어가기 쉽다.
그 안에는 PII, credential, confidential data가 포함될 수 있다.

따라서 기본 사고방식은:

```text
관찰하고 싶은 데이터
≠ 보내도 되는 데이터
```

이다.

현재 Python SDK는 export 단계의 `mask_otel_spans` hook을 권장한다. 실제 production masking rule은 domain과 compliance
요구에 따라 달라지므로 이 초안에서는 특정 regex가 충분하다고 가정하지 않는다.

또한 `@observe()`의 automatic input/output capture가 너무 넓다면 `capture_input=False`, `capture_output=False` 같은
option으로 관찰 범위를 줄일 수 있다.

## 7. Trace design review

다음 trace를 검토한다.

```text
trace: request-user-18472
├─ gpt-5.6-user-18472
├─ helper-1
└─ helper-2
```

Metadata에는 아무것도 없고 root input/output도 비어 있다.

다음 질문에 답한다.

1. operation name에서 제거해야 할 run-specific 값은 무엇인가?
2. 어떤 observation을 합치거나 이름을 바꾸면 좋은가?
3. reviewer가 첫 화면에서 봐야 할 root input/output은 무엇인가?
4. model 이름은 어디에 두는 것이 더 좋은가?
5. user ID와 app revision은 어디에 두는 것이 좋은가?

## 다음 장

지금까지는 Langfuse API로 직접 observation을 만들었다.
다음 장에서는 실제 LLM provider integration이 generation을 자동으로 만들 때 무엇이 달라지는지 비교한다.

## References

- [Langfuse Trace Best Practices](https://langfuse.com/docs/observability/best-practices)
- [Tags](https://langfuse.com/docs/observability/features/tags)
- [Masking](https://langfuse.com/docs/observability/features/masking)
- [Python v3 → v4](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4)
