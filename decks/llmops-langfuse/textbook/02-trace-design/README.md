# 2장 · 다시 찾을 수 있는 Trace 설계하기

Trace가 보인다고 observability가 완성된 것은 아니다. 몇 달 뒤에도 같은 operation을 묶어서 보고, 특정 user/session을
찾아가고, 실패 사례를 dataset이나 evaluator로 다시 사용할 수 있어야 한다.

이번 장에서는 같은 support operation을 두 user로 실행하면서 다음 질문을 다룬다.

> **실행마다 달라지는 값을 observation name에 넣지 않고도 어떻게 원하는 실행을 찾을 수 있을까?**

## 학습 목표

- stable observation name과 run-specific value를 구분한다.
- `user_id`, `session_id`, tags, metadata가 observation name과 다른 역할을 갖는 이유를 설명한다.
- `propagate_attributes()`가 current observation과 이후 child observations에 correlating attributes를 전달하는 방식을
  설명한다.
- root input/output을 trace 전체의 핵심 입출력으로 설계한다.
- sensitive data를 관찰 대상으로 삼기 전에 export boundary를 검토해야 하는 이유를 설명한다.

## 1. 이름은 operation을 표현한다

다음 이름을 비교해 보자.

```text
불안정한 이름
support-turn-user-18472
search-policy-user-18472

안정적인 이름
support-turn
search-policy
```

`user-18472`는 이 실행을 찾는 데 유용하지만 operation 자체의 이름은 아니다.
다음 요청이 `user-88420`에서 오면 같은 support operation이 다른 이름으로 갈라진다.

```text
support-turn-user-18472
support-turn-user-88420
```

이렇게 되면 “support-turn 전체를 보고 싶다”는 질문과 “user-18472의 실행을 보고 싶다”는 질문이 observation name 하나에
섞인다.

좋은 trace design은 두 질문을 분리한다.

```text
operation identity
→ observation name

run / correlation identity
→ user_id, session_id, metadata, tags
```

Model 이름이나 request ID처럼 실행마다 달라질 수 있는 값도 같은 이유로 operation name에 넣지 않는 편이 좋다.

## 2. 이번 실습의 구조

실습 파일은 [`trace_design.py`](trace_design.py)다.

두 user가 같은 support workflow를 실행한다고 하자.

```text
user-18472
trace A
└─ support-turn
   └─ search-policy

user-88420
trace B
└─ support-turn
   └─ search-policy
```

두 trace의 operation name은 같다.
대신 다음 correlating attributes가 다르다.

```text
user_id
session_id
```

그리고 두 실행에 공통으로 다음 context를 붙인다.

```text
tags = [support, web]
metadata.app_revision = abc123
metadata.route = /support
```

이 구조의 장점은 질문마다 적절한 dimension을 사용할 수 있다는 것이다.

```text
"support-turn 실행을 모두 보고 싶다"
→ observation name

"user-18472 실행만 보고 싶다"
→ user_id

"같은 conversation 흐름을 보고 싶다"
→ session_id

"abc123 revision에서 생긴 실행을 보고 싶다"
→ metadata
```

## 3. `propagate_attributes()`는 correlating context를 전달한다

현재 Python SDK v4에서는 `propagate_attributes()`가 correlating attributes를 다루는 기본 방식이다.
이 함수는 Langfuse client method가 아니라 module-level context manager다.

```python
from langfuse import propagate_attributes

with langfuse.start_as_current_observation(
    as_type="span",
    name="support-turn",
) as root:
    with propagate_attributes(
        user_id="user-18472",
        session_id="session-refund-1",
        tags=["support", "web"],
        metadata={
            "app_revision": "abc123",
            "route": "/support",
        },
    ):
        ...
```

이 context에 들어가면 현재 active observation과 그 안에서 이후 생성되는 child observations가 같은 correlating context를
사용할 수 있다.

중요한 시간 관계는 다음과 같다.

```text
root 시작
↓
propagate_attributes 진입
↓
현재 root에 correlating attributes 적용
↓
child 생성
↓
child도 같은 correlating attributes 상속
```

그래서 SDK reference도 `propagate_attributes()`를 trace/workflow의 이른 시점에 호출하도록 권장한다.
이미 context 밖에서 끝난 observation에 나중에 소급 적용되는 기능은 아니다.

## 4. 실행 전에 예측한다

먼저 두 user를 **stable name**으로 실행할 때를 예측한다.

```bash
cd decks/llmops-langfuse
uv run python textbook/02-trace-design/trace_design.py \
  --user-id user-18472 \
  --session-id session-refund-1

uv run python textbook/02-trace-design/trace_design.py \
  --user-id user-88420 \
  --session-id session-refund-2
```

실행 전에 답해 본다.

1. 두 실행의 `trace_id`는 같을까, 다를까?
2. 두 실행의 root observation name은 같을까?
3. `search-policy` 이름은 같을까?
4. user를 구분하기 위해 observation name이 달라질 필요가 있을까?
5. 같은 operation name을 유지하면서 user를 구분하는 값은 무엇일까?

Script는 다음 종류의 evidence를 stdout에 출력한다.

```text
root_name=support-turn
search_name=search-policy
trace_id=...
root_observation_id=...
search_observation_id=...
user_id=user-18472
session_id=session-refund-1
...
```

실제 ID 값보다 관계를 본다.

```text
다른 request
→ trace_id는 다름

같은 operation
→ root_name / search_name은 같음

다른 사용자와 session
→ user_id / session_id는 다름
```

Langfuse UI에서는 같은 observation name으로 묶어서 찾은 뒤 user/session filter로 두 실행을 구분해 본다.

## 5. 한 조건을 나쁘게 바꾼다

이제 application work와 correlating attributes는 그대로 두고 **이름만** 바꾼다.

```bash
uv run python textbook/02-trace-design/trace_design.py \
  --user-id user-18472 \
  --session-id session-refund-1 \
  --unstable-names

uv run python textbook/02-trace-design/trace_design.py \
  --user-id user-88420 \
  --session-id session-refund-2 \
  --unstable-names
```

이번에는 다음처럼 보인다.

```text
user-18472
support-turn-user-18472
└─ search-policy-user-18472

user-88420
support-turn-user-88420
└─ search-policy-user-88420
```

예측한다.

- trace parent/child 구조 자체는 바뀌는가?
- `user_id`, `session_id`는 사라지는가?
- “모든 support-turn”을 observation name으로 묶는 일은 쉬워지는가, 어려워지는가?
- user ID가 이미 별도 attribute인데 이름에도 다시 넣어서 얻는 정보는 무엇인가?

이 variation의 핵심은 **trace topology가 아니라 query dimension이 망가진다**는 것이다.

```text
좋은 설계
operation name = stable
run-specific identity = attribute

나쁜 설계
operation name 안에 run-specific identity를 섞음
→ 같은 operation이 실행마다 다른 이름으로 파편화
```

## 6. Root input/output은 trace의 대표 질문과 결과다

이번 예제의 root observation은 다음 값을 갖는다.

```text
input
{"question": "환불 기간은?"}

output
{"answer": "14일"}
```

Root input/output은 trace 전체를 열었을 때 사람이 가장 먼저 이해해야 하는 요청과 최종 결과를 표현하는 편이 좋다.

반대로 HTTP request object 전체, framework internal state, 대형 raw payload를 무조건 root input으로 넣으면 핵심 질문이
묻힐 수 있다.

판단 기준은 다음처럼 잡을 수 있다.

```text
root input/output
→ 이 workflow가 무엇을 받아 최종적으로 무엇을 냈는가?

child input/output
→ 각 operation이 무엇을 받아 무엇을 냈는가?

metadata
→ 실행을 해석하는 추가 context
```

## 7. Metadata와 tags는 score가 아니다

이번 예제는 다음 값을 사용한다.

```text
tags
support
web

metadata
app_revision = abc123
route = /support
```

이 값들은 실행을 시작할 때 이미 알고 있는 grouping/debugging context다.

반면 다음은 실행 결과를 **평가**한 정보다.

```text
correctness = true
hallucination = 0.2
```

이런 판단을 tag나 metadata로 대신하면 이후 evaluation 의미가 흐려진다.
4장에서 score를 별도로 배우는 이유다.

## 8. 너무 많은 observation도 좋은 trace가 아니다

다음 함수가 있다고 하자.

```text
normalize_text()
strip_whitespace()
lowercase()
search_policy()
rerank_results()
call_model()
validate_answer()
```

모든 함수에 observation을 만들면 자세해 보이지만 반드시 더 유용한 trace가 되는 것은 아니다.

Observation boundary를 만들기 전에 다음을 묻는다.

> 이 operation을 별도로 봐야 failure 원인, latency/cost, evaluation target 중 하나를 더 잘 이해할 수 있는가?

그렇지 않다면 일반 application code로 남겨 두는 편이 더 읽기 쉬울 수 있다.

## 9. Sensitive data는 export 전에 경계를 정한다

LLM application에는 prompt, response, retrieved document, user context가 들어가기 쉽다.
그 안에는 PII, credential, confidential data가 포함될 수 있다.

따라서 다음 두 집합은 같지 않다.

```text
관찰하고 싶은 데이터
≠ 외부 observability system으로 보내도 되는 데이터
```

현재 Langfuse Python SDK의 새 setup에서는 export-stage `mask_otel_spans` hook이 권장된다. 이 hook은 Langfuse client가
export할 OpenTelemetry span attribute를 내보내기 전에 patch할 수 있고, third-party instrumentation span에도 적용할 수
있다.

하지만 중요한 경계가 있다.

- masking rule은 application/domain의 data classification을 대신 결정하지 않는다.
- `mask_otel_spans`는 span name, IDs, parent relationship 자체를 바꾸는 도구가 아니다.
- 느리거나 외부 network에 의존하는 masking logic은 export queue를 지연시킬 수 있다.
- Langfuse 외의 다른 exporter에도 같은 data를 보낸다면 그 exporter의 masking 책임은 별도다.

이번 core 실습에서는 synthetic support data만 사용하고 실제 customer data를 넣지 않는다.

## 10. Local contract test

[`test_trace_design.py`](test_trace_design.py)는 credential이나 live Langfuse project 없이 teaching code의 설계
contract를 검사한다.

```bash
python textbook/02-trace-design/test_trace_design.py
```

검사하는 것:

```text
- stable mode에서 user ID가 observation name에 섞이지 않음
- 다른 user를 실행해도 operation name은 동일함
- user_id / session_id / tags / metadata가 propagate_attributes에 전달됨
- unstable variation은 이름만 파편화하고 correlation attributes는 유지함
```

검사하지 않는 것:

```text
- 실제 Langfuse SDK가 attributes를 export한 결과
- Cloud UI filtering/grouping
- mask_otel_spans runtime behavior
```

이 부분은 locked SDK runtime과 live project를 사용할 수 있을 때 별도로 검증한다.

## 11. Trace design review

다음 trace를 검토한다.

```text
trace
├─ gpt-5.6-user-18472
├─ helper-1
└─ helper-2
```

Root input/output은 비어 있고 metadata도 없다.

다음 질문에 답한다.

1. 이름에서 제거해야 할 run-specific 값은 무엇인가?
2. `helper-1`, `helper-2` 대신 operation 의미를 드러내려면 어떤 정보가 필요한가?
3. reviewer가 첫 화면에서 봐야 할 root input/output은 무엇인가?
4. model 이름은 observation name과 generation model attribute 중 어디가 더 적절한가?
5. user ID와 app revision은 어떤 dimension으로 두는 것이 좋은가?
6. 실제 user 질문에 PII가 포함된다면 trace를 보내기 전에 어떤 경계를 검토해야 하는가?

## 다음 장

지금까지는 application code가 Langfuse observation boundary를 직접 만들었다.
다음 장에서는 OpenAI integration이 model call을 generation으로 자동 instrument할 때 **무엇이 자동화되고 무엇은 여전히
application이 표현해야 하는지** 비교한다.

## References

- [Python SDK Reference](https://python.reference.langfuse.com/langfuse)
- [Python v3 → v4](https://langfuse.com/docs/observability/sdk/upgrade-path/python-v3-to-v4)
- [Masking](https://langfuse.com/docs/observability/features/masking)
- [Langfuse Trace Best Practices](https://langfuse.com/docs/observability/best-practices)
- [Tags](https://langfuse.com/docs/observability/features/tags)
