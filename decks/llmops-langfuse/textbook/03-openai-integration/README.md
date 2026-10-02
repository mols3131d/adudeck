# 3장 · OpenAI Integration: Provider 호출과 Application 의미를 분리하기

2장까지는 우리가 직접 observation boundary를 만들었다. 이제 실제 LLM 호출을 넣으면 문제가 하나 생긴다.

LLM call마다 model, input, output, token usage, latency 같은 값을 application code가 직접 기록하면 observability code가
provider call보다 더 커질 수 있다. 반대로 provider integration에 모든 것을 맡기면 `support-turn`, retrieval,
validation처럼 **application만 아는 의미**가 사라진다.

이 장의 목표는 자동 계측을 많이 켜는 것이 아니다.

> **Provider integration은 provider call의 세부 evidence를 소유하고, application instrumentation은 business operation의
> 의미와 경계를 소유한다.**

이 책임 분리를 직접 확인한다.

## 학습 목표

이 장을 마치면 다음을 할 수 있어야 한다.

- span과 generation observation이 서로 다른 질문에 답한다는 것을 설명한다.
- `langfuse.openai.OpenAI`가 자동으로 만드는 generation과 직접 만든 application span의 관계를 설명한다.
- OpenAI integration이 수집할 수 있는 provider-level evidence와 application이 직접 기록해야 하는 context를 구분한다.
- 자동 instrumentation이 correctness, retrieval boundary, user/session 의미를 추론해 주지 않는 이유를 설명한다.
- provider failure, Langfuse export failure, application validation failure를 같은 실패로 취급하지 않는다.

## 1. 먼저 경계를 그린다

이번 장에서 만들고 싶은 trace는 다음과 같다.

```text
support-turn                         application span
└─ answer-generation                generation
   └─ OpenAI Responses API call     provider execution
```

`support-turn`은 "사용자 지원 요청 하나를 처리했다"는 application 의미다.

`answer-generation`은 "LLM provider를 호출해 답변을 만들었다"는 generation evidence다.

두 observation이 같은 trace에 들어가더라도 책임은 다르다.

| 질문 | 주로 누가 답하는가? |
| --- | --- |
| 이 요청은 어떤 business operation인가? | application instrumentation |
| 어느 model을 호출했는가? | provider integration |
| 어떤 input/output이 provider boundary를 통과했는가? | provider integration |
| retrieval은 언제, 왜 수행됐는가? | application instrumentation |
| user/session은 무엇인가? | application context |
| token usage와 model latency는 얼마인가? | provider integration |
| 답변이 정책상 올바른가? | evaluator/application rule |
| 어떤 값을 저장하면 안 되는가? | application privacy policy |

자동 instrumentation은 **알 수 있는 것만 자동화한다**.

## 2. Generation은 단순히 "LLM 함수"라는 뜻이 아니다

Langfuse에서 generation은 LLM generation을 나타내는 observation type이다. 일반 span과 마찬가지로 trace 안의 execution
evidence이지만, model, model parameters, usage, cost 같은 LLM-specific 정보를 표현할 수 있다.

중요한 구분은 다음이다.

```text
span
= application의 의미 있는 작업 단위

generation
= LLM provider/model 호출을 설명하는 observation
```

그래서 다음 두 trace는 정보량이 다르다.

```text
A. provider call만 관찰

answer-generation


B. application 의미 + provider call을 함께 관찰

support-turn
├─ retrieve-policy
└─ answer-generation
```

A도 model call을 디버깅하는 데 쓸 수 있다. 그러나 "이 generation이 어떤 사용자 요청의 어느 단계였는가?"라는 질문에는
B가 훨씬 강하다.

## 3. OpenAI integration은 현재 context 안에서 generation을 만든다

Langfuse Python SDK v4의 tracing은 OpenTelemetry context 위에서 동작한다. OpenAI integration도 현재 active context를
이용해 자동 생성한 generation을 기존 trace에 연결한다.

이번 장의 [`openai_integration.py`](openai_integration.py)는 application span만 직접 만든다.

핵심 부분은 다음과 같다.

```python
with langfuse.start_as_current_observation(
    as_type="span",
    name="support-turn",
    input={"question": question},
) as root:
    response = openai_client.responses.create(
        name="answer-generation",
        model=model,
        input=[{"role": "user", "content": question}],
    )

    answer = response.output_text
    root.update(output={"answer": answer})
```

직접 `generation` observation을 만들지 않았다는 점을 본다.

```text
application code
→ support-turn의 의미를 기록

Langfuse OpenAI integration
→ OpenAI call을 가로채 generation evidence를 기록
```

이 패턴의 장점은 provider-specific telemetry boilerplate를 줄이면서도 application-level structure를 잃지 않는 데 있다.

## 4. 실행 전에 예측한다

Live API를 호출하기 전에 다음을 적어 본다.

1. 직접 생성하는 Langfuse observation은 몇 개인가?
2. OpenAI integration이 정상적으로 동작하면 UI에는 observation이 몇 개 보일 것으로 예상하는가?
3. `answer-generation`은 `support-turn`과 같은 trace에 들어갈까?
4. model name과 usage는 어느 layer가 기록하는가?
5. `support-turn`이라는 이름은 OpenAI integration이 스스로 알 수 있는가?
6. 답변 correctness score가 자동으로 만들어질까?

예측을 먼저 적으면 "화면에 뭔가 생겼다"가 아니라 **어떤 mechanism을 검증했는지** 설명할 수 있다.

## 5. 환경 준비

이 deck은 OpenAI integration을 실제 학습 경로로 사용하므로 deck dependency에 `openai`가 명시되어 있어야 한다.

```bash
cd decks/llmops-langfuse
uv sync
```

Live lab에는 다음 값이 필요하다.

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"

export OPENAI_API_KEY="sk-..."
export OPENAI_MODEL="<사용할 model>"
```

Secret과 실제 customer data는 Git에 기록하지 않는다.

`OPENAI_MODEL`을 코드에 고정하지 않는 이유도 학습 대상이다. Model은 experiment에서 바꿔 비교할 수 있는 **condition**이지
source code에 숨겨야 하는 상수가 아니다.

## 6. Live lab: 한 번만 호출하고 evidence를 삼각측량한다

실행한다.

```bash
uv run python textbook/03-openai-integration/openai_integration.py
```

stdout에는 application이 직접 아는 identity를 출력한다.

```text
trace_id=...
root_observation_id=...
answer=...
```

그 다음 Langfuse UI에서 같은 `trace_id`를 찾아 다음을 확인한다.

```text
surface A: stdout
- root trace id
- root observation id
- final answer

surface B: Langfuse trace
- support-turn root
- 그 아래의 answer-generation
- generation의 model
- generation input/output
- usage / latency evidence
```

두 surface가 **같은 logical execution**을 가리키는지 확인하는 것이 핵심이다.

### 관찰 질문

- `answer-generation`의 parent는 무엇인가?
- generation의 input은 root input과 완전히 같은가, 아니면 provider에 실제 전달된 형태인가?
- root output과 generation output은 어떤 관계인가?
- model/usage는 root span이 아니라 generation에서 보는 편이 자연스러운 이유는 무엇인가?
- OpenAI call이 실패하면 generation evidence와 root span의 상태는 어떻게 보이는가?

## 7. Manual instrumentation과 automatic instrumentation을 비교한다

Manual 방식에서는 application이 대략 다음 정보를 직접 전달해야 한다.

```text
start generation
→ model 기록
→ input 기록
→ provider 호출
→ output 기록
→ usage 기록
→ exception/error 반영
→ generation 종료
```

Integration 방식에서는 provider call을 감싸는 반복 작업의 상당 부분을 wrapper가 처리한다.

그러나 다음 정보는 여전히 application에 남는다.

```text
support-turn이라는 operation boundary
retrieve-policy라는 domain step
user/session correlation
business metadata
privacy/masking policy
correctness rule
release decision
```

따라서 좋은 mental model은 다음이다.

```text
automatic instrumentation
≠ observability 자동 완성

automatic instrumentation
= provider boundary의 반복 계측을 맡기는 것
```

## 8. Cost와 usage는 quality가 아니다

Generation에서 token usage와 cost를 볼 수 있다는 사실은 매우 유용하다. 그러나 이것은 quality 판정이 아니다.

가능한 결과는 모두 존재한다.

```text
quality ↑   cost ↑
quality ↑   cost ↓
quality ↓   cost ↑
quality ↓   cost ↓
```

그래서 다음과 같은 문장은 근거가 부족하다.

> "candidate가 token을 덜 썼으니 더 좋은 prompt다."

대신 질문을 분리한다.

```text
quality dimension
- correctness
- relevance
- style
- safety

operational dimension
- latency
- token usage
- cost
- error rate
```

나중의 experiment에서는 이 dimension들을 함께 보되 서로를 대체하지 않는다.

## 9. 실패도 ownership별로 나눈다

### Provider failure

예: authentication, rate limit, timeout.

```text
OpenAI request
→ provider error
```

Application은 provider failure contract를 따라 처리해야 한다. Langfuse export 성공 여부가 provider failure의 의미를
바꾸지 않는다.

### Observability/export failure

```text
application/model call은 성공
→ telemetry export 실패
```

관찰 도구 장애 때문에 성공한 business operation을 실패로 가장해서도 안 되고, 반대로 observability failure를 숨겨서도
안 된다. 실제 production failure policy는 application 요구사항에 따라 별도로 정한다.

### Evaluation failure

```text
answer 생성 성공
→ evaluator 실행 실패
```

이것은 "answer score = 0"과 다르다. 다음 장에서 이 distinction을 코드로 다룬다.

## 10. Credential-free contract test

[`test_openai_integration.py`](test_openai_integration.py)는 외부 API 없이 다음 application contract를 검증한다.

```text
support-turn span을 application이 직접 만든다
→ Responses API call에 model/input/name을 전달한다
→ provider response를 root output으로 연결한다
```

실행:

```bash
python textbook/03-openai-integration/test_openai_integration.py
```

이 test는 의도적으로 **Langfuse OpenAI integration 자체를 fake로 증명하지 않는다**.

증명하는 것:

- teaching code의 application boundary가 유지된다.
- model이 hard-code되지 않고 주입된다.
- provider response가 root output으로 연결된다.

증명하지 않는 것:

- 실제 `langfuse.openai.OpenAI`가 generation을 export한다.
- token/cost가 실제 project에서 계산된다.
- Langfuse Cloud UI의 parent/child tree가 예상대로 렌더링된다.

그 세 항목은 installed SDK contract와 live lab evidence로 확인해야 한다.

## 11. Checkpoint: 어떤 layer가 소유해야 하는가?

다음 정보를 `application span`, `provider generation`, `score`, `metadata/tag` 중 어디에 두는 것이 자연스러운지 정하고 이유를
설명한다.

1. `support-turn`
2. model name
3. token usage
4. `user_id`
5. retrieval source count
6. final answer correctness
7. `channel=web`
8. OpenAI response latency

정답 단어보다 중요한 것은 **왜 그 위치에서 가장 잘 해석되는가**다.

## 12. Transfer exercise

새 application은 다음 구조를 가진다.

```text
answer-request
├─ classify-intent
├─ retrieve-context
├─ rerank-context
└─ model call
```

OpenAI integration을 붙였더니 generation 하나는 잘 보인다.

설계하라.

- 어떤 application operation을 별도 span으로 남길 것인가?
- 어떤 operation은 너무 세밀해서 observation으로 만들지 않을 것인가?
- user/session context는 어디서 주입할 것인가?
- 어떤 sensitive input은 기록하지 않거나 mask해야 하는가?
- model call이 다른 provider로 바뀌어도 유지되어야 하는 observation은 무엇인가?

이 설계가 가능하면 "OpenAI integration 사용법"이 아니라 **observability ownership**을 이해한 것이다.

## 다음 장

Trace는 execution evidence다. 다음 장에서는 execution을 평가한 결과를 **score evidence**로 붙인다. 중요한 질문은
"어떻게 점수를 보내는가?"보다 먼저 **무엇을, 어떤 rule로, 어느 level에서 평가하는가?**다.

## References

- [Langfuse OpenAI Integration](https://langfuse.com/integrations/model-providers/openai-py)
- [Get Started with LLM Tracing](https://langfuse.com/docs/observability/get-started)
- [Langfuse Python SDK Reference](https://python.reference.langfuse.com/)
- [Langfuse Python SDK v4.16.0 source](https://github.com/langfuse/langfuse-python/tree/v4.16.0)
- [OpenAI Responses API migration guidance](https://platform.openai.com/docs/guides/migrate-to-responses)
