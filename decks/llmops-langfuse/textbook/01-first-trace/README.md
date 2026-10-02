# 1장 · 첫 Trace와 Observation: Current Context가 Topology를 만든다

이번 장에서는 OpenAI나 framework integration을 붙이지 않는다.

먼저 작은 Python workflow를 Langfuse data model로 표현하고 **현재 실행 context가 observation parentage를 어떻게 결정하는지**
직접 확인한다.

이 mechanism을 이해하면 나중에 decorator, provider integration, distributed tracing을 사용할 때 trace가 왜 예상과 다르게
갈라지거나 붙는지 설명할 수 있다.

## 학습 목표

- trace와 observation의 관계를 설명한다.
- root observation과 child observation을 구분한다.
- `start_as_current_observation()`이 current context를 이용해 parent/child 관계를 만드는 방식을 설명한다.
- nested observation 종료 후 이전 current observation이 복원되는 이유를 설명한다.
- Langfuse v4가 OpenTelemetry context 위에서 동작한다는 boundary를 설명한다.
- short-lived script에서 `flush()`가 필요한 이유를 설명한다.

## 1. Observations-first mental model

현재 Langfuse Python SDK v4에서는 execution을 observation 중심으로 본다.

```text
trace
└─ root observation
   ├─ child observation
   └─ child observation
```

Observation은 application execution의 의미 있는 작업이다.

예:

```text
retrieve-policy
parse-tool-result
answer-generation
validate-output
```

Trace는 관련 observation을 한 execution으로 묶는다.

Session은 여러 trace를 더 큰 interaction 단위로 묶을 수 있다.

```text
session
├─ trace: turn-1
│  ├─ observation
│  └─ observation
└─ trace: turn-2
   ├─ observation
   └─ observation
```

중요한 점:

> **Python 함수 호출 관계 자체가 parent/child 관계를 만들지 않는다.**

핵심 state는 observation을 시작하는 순간의 **active OpenTelemetry execution context**다.

Langfuse는 이 context를 이용해 observation parentage와 trace correlation을 만든다.

## 2. 첫 experiment

실습 파일은 [`first_trace.py`](first_trace.py)다.

Baseline:

```text
support-turn
└─ search-policy
```

`support-turn` 안에서 `search-policy`를 시작한다.

확인할 evidence:

```text
root_trace_id
root_observation_id
search_trace_id
search_observation_id
current_after_search
```

비교할 것은 UUID 자체가 아니라 관계다.

```text
root trace id == search trace id ?
root observation id != search observation id ?
child 종료 후 current observation == root observation id ?
```

## 3. 실행 전 prediction

코드를 실행하지 말고 먼저 적는다.

1. baseline에는 trace가 몇 개 생길까?
2. observation은 몇 개인가?
3. root와 child의 `trace_id`는 같은가?
4. root와 child의 `observation_id`도 같은가?
5. `search-policy`가 끝난 직후 current observation은 무엇인가?

그 다음 실행한다.

```bash
cd decks/llmops-langfuse
uv run python textbook/01-first-trace/first_trace.py
```

예상 형태:

```text
root_trace_id=...
root_observation_id=...
search_trace_id=...
search_observation_id=...
current_after_search=...
same_trace=true
```

UI에서도 같은 trace tree를 확인한다.

## 4. Context state를 한 단계씩 추적한다

핵심 코드:

```python
with langfuse.start_as_current_observation(
    as_type="span",
    name="support-turn",
) as root:
    search_policy(langfuse, "환불 기간")
```

State transition:

```text
root 진입
current = support-turn

search-policy 진입
current = search-policy
parent context = support-turn

search-policy 종료
current = support-turn 복원

root 종료
current = 이전 outer context
```

Standalone script에서 이전 outer context가 없었다면 root 종료 뒤 Langfuse current observation도 없다.

이 복원 behavior가 중요한 이유는 nested operation을 끝낸 뒤 caller context에서 다시 child를 만들 수 있기 때문이다.

## 5. Variation: Langfuse root 밖으로 child를 옮긴다

```bash
uv run python textbook/01-first-trace/first_trace.py --detach-search
```

이번 variation에서는 `support-turn`이 끝난 뒤 `search-policy`를 시작한다.

이 standalone lab에는 root 밖의 다른 active parent를 만들지 않는다.

따라서 예상은:

```text
trace A
└─ support-turn

trace B
└─ search-policy
```

그리고:

```text
same_trace=false
```

### 왜 "항상 새 trace"라고 외우면 안 되는가?

Langfuse v4는 OpenTelemetry context 위에서 동작한다.

실제 web framework나 이미 instrumented된 runtime에서는 Langfuse root observation 바깥에도 **outer OpenTelemetry span**이
active할 수 있다.

그 경우:

```text
Langfuse observation block 종료
≠
OpenTelemetry parent context가 반드시 완전히 사라짐
```

따라서 정확한 statement는 다음이다.

> **이 standalone experiment에서는 outer active OpenTelemetry parent가 없기 때문에 root block 밖에서 시작한
> `search-policy`가 별도 trace가 된다. 일반적으로 parentage는 observation 시작 시점의 current OpenTelemetry context에
> 의해 결정된다.**

이 nuance는 distributed tracing을 배울 때 매우 중요하다.

## 6. 함수 구조와 trace 구조는 같은 것이 아니다

다음 코드가 있다고 하자.

```python
def a():
    b()
```

이것만으로:

```text
a observation
└─ b observation
```

이 만들어지는 것은 아니다.

Observation을 실제로 어디에서 시작했는지, 시작 순간 current context가 무엇인지가 중요하다.

반대로 decorator나 auto instrumentation을 쓰면 Python call boundary가 observation과 비슷하게 보일 수 있다. 그래도
mechanism은 "함수이기 때문에"가 아니라 instrumentation이 context를 만들고 전파했기 때문이다.

## 7. `flush()`는 topology가 아니라 export boundary다

Langfuse SDK는 telemetry를 background batch/export할 수 있다.

Short-lived script는 process가 너무 빨리 종료될 수 있으므로 마지막에:

```python
langfuse.flush()
```

를 호출한다.

구분:

```text
start_as_current_observation()
→ observation lifetime / current context / parentage

flush()
→ 이미 생성된 pending telemetry를 export하는 boundary
```

`flush()`를 호출한다고 잘못 연결된 parent/child 관계가 고쳐지는 것은 아니다.

## 8. Decorator는 mechanism을 숨겨 편리하게 만든다

Langfuse는 `@observe()`도 제공한다.

```python
from langfuse import observe


@observe()
def search_policy(query: str) -> str:
    return "구매 후 14일 이내 환불 가능"
```

Decorator는 function input/output/timing/error capture를 줄여 준다.

하지만 첫 학습부터 decorator만 보면 다음 state가 가려질 수 있다.

```text
언제 context에 들어갔는가?
언제 이전 context로 복원됐는가?
어떤 active parent를 상속했는가?
```

그래서 이 deck은 explicit context manager로 mechanism을 먼저 보고 convenience API로 이동한다.

## 9. Credential-free contract test

[`test_first_trace.py`](test_first_trace.py)는 fake client로 **teaching code 자체의 control flow**를 검증한다.

```bash
python textbook/01-first-trace/test_first_trace.py
```

검증:

```text
baseline
- child가 root 안에서 시작
- 같은 fake trace identity를 상속
- child 종료 후 root context 복원

detached
- root context가 닫힌 뒤 search 실행
- 이 standalone fake model에서는 별도 trace
```

검증하지 않음:

```text
실제 OpenTelemetry runtime semantics
Langfuse SDK 4.16.x exporter behavior
Cloud ingestion
UI rendering
outer framework span과의 distributed parentage
```

Fake test와 live/runtime evidence를 같은 수준으로 말하지 않는다.

## 10. Live observation checklist

Langfuse project에서 baseline과 variation을 각각 실행한 뒤 확인한다.

### Baseline

```text
support-turn
└─ search-policy
```

- trace id 공유
- observation id 분리
- child timing이 root 안에 포함
- stdout의 current context evidence와 UI tree가 일치

### Detached variation

Standalone script 기준:

```text
support-turn

search-policy
```

- 서로 다른 trace identity
- 같은 Python helper를 사용했지만 topology 변화
- 차이는 helper name이 아니라 active parent context

## 11. 오해하기 쉬운 점

- 함수 하나가 자동으로 observation 하나라는 뜻은 아니다.
- trace는 Python call tree의 복사본이 아니다.
- root observation 종료가 모든 환경에서 "OTel context 없음"을 뜻하지 않는다.
- 모든 함수에 observation을 만들 필요는 없다.
- `flush()`는 parent/child 관계를 만들지 않는다.
- UUID 값 자체보다 identity 관계가 중요하다.
- 의미 없는 세부 span을 많이 만들면 오히려 trace readability가 나빠진다.

## 12. Checkpoint

코드 없이 답한다.

1. `trace_id`와 `observation_id`는 무엇을 식별하는가?
2. child observation이 root와 같은 trace에 들어가는 직접적인 원인은 무엇인가?
3. child 종료 후 root current context가 복원되는 것이 왜 필요한가?
4. standalone detached variation이 새 trace가 되는 조건은 무엇인가?
5. web request의 outer OTel span이 active하다면 detached experiment의 결과가 달라질 수 있는 이유는 무엇인가?
6. `flush()`와 context manager가 각각 어떤 state를 다루는가?

## 13. Transfer exercise

다음 runtime을 상상한다.

```text
HTTP server span
└─ support-turn
   └─ search-policy
```

`support-turn`을 닫은 뒤에도 HTTP server span은 active하다.

그 상태에서 새 Langfuse observation을 시작한다.

예측하라.

- 새 observation이 반드시 완전히 새로운 distributed trace가 될까?
- 어떤 outer context를 확인해야 하는가?
- "Langfuse current observation 없음"과 "OpenTelemetry current span 없음"은 같은 statement인가?

답을 설명할 때 **current execution context**라는 말을 사용한다.

## 다음 장

이제 observation을 만드는 mechanism을 알았다.

다음 장에서는 observation을 많이 만드는 법이 아니라 **나중에 사람이 읽고 evaluator가 사용할 수 있는 trace를 어떻게
설계하는가**를 다룬다.

## References

- [Langfuse SDK Overview](https://langfuse.com/docs/observability/sdk/overview)
- [Get Started with LLM Tracing](https://langfuse.com/docs/observability/get-started)
- [Trace IDs & Distributed Tracing](https://langfuse.com/docs/observability/features/trace-ids-and-distributed-tracing)
- [OpenTelemetry Context](https://opentelemetry.io/docs/languages/python/context/)
- [OpenTelemetry Library Instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
- [Langfuse Python SDK Reference](https://python.reference.langfuse.com/)
