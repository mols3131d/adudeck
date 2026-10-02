# 3장 · OpenAI Integration: Provider Evidence와 Application Meaning을 분리하기

2장까지는 우리가 직접 observation boundary를 만들었다. 이제 실제 LLM provider 호출을 넣어 보자.

여기서 두 극단 모두 문제가 된다.

```text
모든 provider telemetry를 application code가 직접 기록
→ instrumentation boilerplate가 커짐

provider integration에 모든 관찰 책임을 맡김
→ support-turn, retrieval, validation 같은 application 의미가 사라짐
```

이 장의 핵심은 자동 계측을 많이 켜는 것이 아니다.

> **Provider integration은 provider call의 반복적인 telemetry를 맡고, application instrumentation은 business operation의
> 의미와 경계를 맡는다.**

이 책임 분리를 OpenAI Responses API와 Langfuse Python SDK v4로 확인한다.

## 학습 목표

이 장을 마치면 다음을 할 수 있어야 한다.

- application span과 generation observation이 서로 다른 질문에 답한다는 것을 설명한다.
- `langfuse.openai.OpenAI`가 OpenAI 호출 하나를 generation observation으로 기록하는 방식을 설명한다.
- provider integration이 자동으로 수집할 수 있는 evidence와 application이 직접 정의해야 하는 context를 구분한다.
- current OpenTelemetry context가 auto-instrumented generation의 parentage에 영향을 주는 이유를 설명한다.
- provider failure, application failure, telemetry export failure를 같은 실패로 취급하지 않는다.
- model usage/cost 같은 operational evidence와 correctness 같은 quality evidence를 구분한다.

## 1. 먼저 observation boundary를 그린다

이번 장에서 원하는 trace는 다음과 같다.

```text
support-turn                         application span
└─ answer-generation                OpenAI Responses API call을 나타내는 generation
```

여기서 중요한 점이 있다.

`answer-generation` 아래에 별도의 "OpenAI API call" observation이 하나 더 생긴다고 생각하지 않는다.

```text
answer-generation
= wrapped OpenAI provider call 자체를 표현하는 generation observation
```

Langfuse OpenAI integration은 OpenAI SDK call을 가로채 input/output, model, latency, usage, error 같은 provider-level
evidence를 generation에 기록한다.

반면 `support-turn`은 OpenAI가 알 수 없는 application 의미다.

| 질문 | 주된 owner |
| --- | --- |
| 이 요청은 어떤 business operation인가? | application instrumentation |
| 어느 model을 호출했는가? | provider integration |
| provider에 실제로 어떤 input이 전달됐는가? | provider integration |
| provider가 어떤 output을 반환했는가? | provider integration |
| retrieval은 언제, 왜 수행됐는가? | application instrumentation |
| user/session은 무엇인가? | application context |
| token usage와 provider latency는 얼마인가? | provider integration |
| 최종 답변이 정책상 올바른가? | evaluator / domain rule |
| 어떤 값을 trace에 남기면 안 되는가? | application privacy policy |

자동 instrumentation은 **provider boundary에서 관찰 가능한 것**을 자동화한다. Application semantics까지 추론해 주지는
않는다.

## 2. Span과 generation은 질문이 다르다

Langfuse에서 generation은 LLM/model 호출을 표현하는 observation type이다. 일반 span처럼 trace 안의 execution
evidence이지만 model, model parameters, usage, cost 같은 LLM-specific 정보를 표현하는 데 적합하다.

```text
span
= application의 의미 있는 작업 단위

generation
= model/provider 호출의 execution evidence
```

예를 들어 provider call만 관찰하면 다음처럼 보일 수 있다.

```text
answer-generation
```

이것만으로도 model call 자체는 디버깅할 수 있다. 하지만 application을 이해하기에는 부족할 수 있다.

```text
support-turn
├─ retrieve-policy
└─ answer-generation
```

두 번째 trace에서는 "어느 사용자 요청의 어느 단계에서 이 generation이 실행됐는가?"까지 설명할 수 있다.

## 3. Auto instrumentation은 current context 안에서 동작한다

Langfuse Python SDK v4의 tracing은 OpenTelemetry context 위에서 동작한다. Wrapped OpenAI client도 호출 시점의 active
context를 이용해 generation을 기존 trace에 연결할 수 있다.

[`openai_integration.py`](openai_integration.py)는 application root span만 직접 만든다.

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

Application code는 generation을 직접 시작하지 않는다.

```text
application code
→ support-turn context 생성

wrapped OpenAI call
→ current context를 상속
→ answer-generation 생성
```

이 구조의 장점은 provider-specific telemetry boilerplate를 줄이면서 application topology를 유지하는 데 있다.

## 4. 실행 전에 prediction을 만든다

Live call 전에 다음을 적는다.

1. Application code가 직접 만드는 observation은 몇 개인가?
2. OpenAI integration이 정상 동작하면 추가로 어떤 observation이 생기는가?
3. `answer-generation`은 어떤 parent를 가질 것으로 예상하는가?
4. Model name과 token usage는 어느 observation에서 보는 것이 자연스러운가?
5. `support-turn`이라는 이름을 OpenAI wrapper가 스스로 추론할 수 있는가?
6. Correctness score가 자동으로 생길까?

좋은 prediction은 "성공할 것 같다"가 아니라 **관찰 가능한 identity와 관계**를 예상한다.

## 5. 환경 준비

이 deck의 core path는 Langfuse와 OpenAI SDK를 모두 사용한다.

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

Secret과 실제 customer data는 repository에 기록하지 않는다.

`OPENAI_MODEL`을 환경에서 주입하는 이유도 학습 대상이다. Model은 이후 experiment에서 바꿔 비교할 수 있는
**condition**이다.

## 6. Live lab: stdout과 trace를 같은 execution으로 연결한다

실행한다.

```bash
uv run python textbook/03-openai-integration/openai_integration.py
```

Script는 application이 직접 알고 있는 identity를 출력한다.

```text
trace_id=...
root_observation_id=...
answer=...
```

그 다음 Langfuse UI에서 같은 trace를 찾아 확인한다.

```text
surface A: stdout
- root trace id
- root observation id
- final answer

surface B: Langfuse trace
- support-turn
- 그 child인 answer-generation
- generation model
- provider input/output
- usage / latency / error evidence
```

핵심은 두 surface가 **같은 logical execution**을 설명하는지 확인하는 것이다.

### 관찰 질문

- `answer-generation`의 parent는 무엇인가?
- Generation input은 provider에 전달된 실제 request shape와 어떻게 대응하는가?
- Root output과 generation output은 왜 비슷하지만 책임이 다른가?
- Model/usage를 root span이 아니라 generation에서 보는 것이 자연스러운 이유는 무엇인가?
- Provider call이 실패하면 generation과 root span에는 각각 어떤 evidence가 남는가?

## 7. Variation: application context 밖에서 provider call을 실행한다

Mechanism을 확인하려면 한 조건만 바꾼다.

Baseline:

```text
support-turn context 안에서 OpenAI call
```

Variation:

```text
support-turn context를 닫은 뒤 OpenAI call
```

Standalone process에서 다른 active OpenTelemetry parent가 없다면 두 실행의 topology가 달라질 수 있다.

```text
baseline
support-turn
└─ answer-generation

variation
support-turn

answer-generation   # 별도 root/trace가 될 수 있음
```

단, 1장에서 배운 boundary를 유지한다. Web framework나 다른 instrumentation이 outer OTel span을 제공한다면 provider
generation은 그 outer context를 상속할 수 있다.

따라서 정확한 mental model은 다음이다.

> **Auto instrumentation도 결국 호출 시점의 current execution context에서 parentage를 얻는다.**

## 8. Manual instrumentation과 automatic instrumentation 비교

Manual generation instrumentation을 직접 구현한다면 application이 대략 다음 lifecycle을 책임져야 한다.

```text
generation 시작
→ model/input 기록
→ provider 호출
→ output 기록
→ usage 기록
→ exception/error 반영
→ generation 종료
```

OpenAI integration은 이 provider-boundary 반복 작업의 상당 부분을 맡는다.

그러나 다음은 여전히 application 책임이다.

```text
support-turn 같은 business operation
retrieval / rerank / validation boundary
user/session correlation
feature/release metadata
privacy/masking policy
correctness rule
release decision
```

그래서:

```text
automatic instrumentation
≠ observability 자동 완성

automatic instrumentation
= provider boundary의 반복 계측을 위임하는 것
```

## 9. Usage와 cost는 quality가 아니다

Generation에서 usage와 cost를 볼 수 있다는 것은 유용하지만 quality 판정은 아니다.

```text
quality ↑   cost ↑
quality ↑   cost ↓
quality ↓   cost ↑
quality ↓   cost ↓
```

"token을 덜 썼으니 더 좋은 prompt"라고 결론 내릴 수 없다.

Dimension을 나눈다.

```text
quality
- correctness
- relevance
- groundedness
- style / safety

operational
- latency
- token usage
- cost
- provider error rate
```

이후 experiment에서는 여러 dimension을 함께 볼 수 있지만 서로를 대체하지 않는다.

## 10. Failure ownership을 분리한다

### Provider failure

예: authentication, rate limit, timeout.

```text
OpenAI request
→ provider error
```

이 실패의 의미와 retry/fallback contract는 application/provider integration 정책이 소유한다.

### Application failure

예: provider output은 정상적으로 왔지만 parser나 business validation이 실패했다.

```text
provider success
→ application validation failure
```

Provider generation이 성공했다는 사실과 request 전체가 성공했다는 사실은 다르다.

### Telemetry/export failure

```text
application/provider call 성공
→ observability export 실패
```

관찰 도구 장애를 business failure와 같은 것으로 만들지 않는다. 동시에 telemetry gap 자체는 운영상 별도로 관찰해야 한다.

### Evaluation failure

```text
answer 생성 성공
→ evaluator 실행 실패
```

이것은 `score=0`과 다르다. 다음 장에서 이 차이를 직접 다룬다.

## 11. Credential-free contract test

[`test_openai_integration.py`](test_openai_integration.py)는 외부 API 없이 application-side contract를 검증한다.

```bash
python textbook/03-openai-integration/test_openai_integration.py
```

검증하는 것:

```text
support-turn span을 application이 직접 만든다
→ Responses API call에 model/input/name을 전달한다
→ provider response를 root output으로 연결한다
```

검증하지 않는 것:

```text
실제 langfuse.openai.OpenAI가 generation을 export하는가
실제 usage/cost가 계산되는가
Cloud UI에서 parent/child가 예상대로 보이는가
```

Fake contract test와 live integration evidence를 같은 수준으로 주장하지 않는다.

## 12. Checkpoint: 어느 layer가 소유해야 하는가?

다음 정보를 `application span`, `provider generation`, `score`, `metadata/tag` 중 어디에 두는 것이 자연스러운지 정하고
이유를 설명한다.

1. `support-turn`
2. model name
3. token usage
4. `user_id`
5. retrieval source count
6. final answer correctness
7. `channel=web`
8. provider latency
9. parser validation failure

정답 단어보다 **그 evidence를 나중에 어떤 질문에 사용할 것인가**를 설명하는 것이 중요하다.

## 13. Transfer exercise

다음 application을 설계한다.

```text
answer-request
├─ classify-intent
├─ retrieve-context
├─ rerank-context
└─ OpenAI Responses call
```

질문:

- 어떤 application operation을 별도 span으로 남길 것인가?
- 어떤 내부 helper는 observation으로 만들지 않을 것인가?
- user/session context는 어디에서 주입할 것인가?
- sensitive input은 어느 boundary에서 mask하거나 기록하지 않을 것인가?
- provider를 OpenAI에서 다른 provider로 바꿔도 유지되어야 하는 observation은 무엇인가?
- provider generation만 보고는 판정할 수 없는 correctness 질문은 무엇인가?

이 설계를 설명할 수 있다면 OpenAI wrapper 사용법보다 더 중요한 **observability ownership**을 이해한 것이다.

## 다음 장

Trace와 generation은 execution evidence다. 다음 장에서는 실행을 평가한 결과를 **score evidence**로 연결한다.

중요한 질문은 "점수를 어떻게 보내는가?"가 아니라 먼저 다음이다.

> **무엇을, 어떤 rule로, 어느 execution scope에서 평가하는가?**

## References

- [Langfuse OpenAI Integration](https://langfuse.com/integrations/model-providers/openai-py)
- [Get Started with LLM Tracing](https://langfuse.com/docs/observability/get-started)
- [Langfuse Python SDK Reference](https://python.reference.langfuse.com/)
- [Langfuse Python SDK v4.16.0 source](https://github.com/langfuse/langfuse-python/tree/v4.16.0)
- [OpenAI Responses API migration guidance](https://platform.openai.com/docs/guides/migrate-to-responses)
