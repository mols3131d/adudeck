# 1장 · 첫 Trace와 Observation

이번 장에서는 OpenAI나 LangChain을 붙이지 않는다. 먼저 작은 Python 작업 하나를 Langfuse data model로 표현하고,
**current observation context가 관계를 만드는 방식**을 직접 확인한다.

## 학습 목표

- trace와 observation의 관계를 설명한다.
- root observation과 child observation을 구분한다.
- `start_as_current_observation()`이 current context를 이용해 관계를 만드는 방식을 설명한다.
- nested observation이 끝난 뒤 이전 current observation이 복원되는 이유를 설명한다.
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

여기서 중요한 점은 **Python 함수 호출 관계 자체가 parent/child를 만드는 것이 아니라는 것**이다.
관계를 만드는 핵심 상태는 현재 실행 context에 어떤 observation이 active한가이다.

## 2. 이번 실습에서 볼 것

실습 파일은 [`first_trace.py`](first_trace.py)다.

Baseline은 다음 구조를 만든다.

```text
support-turn
└─ search-policy
```

두 observation이 같은 trace에 들어가고, `search-policy`가 끝난 뒤 current observation이 다시 `support-turn`으로
복원되는지 확인한다.

그 다음 `--detach-search` variation에서는 `search-policy`를 root observation이 종료된 뒤 실행한다.

```text
baseline
trace A
└─ support-turn
   └─ search-policy

variation
trace A
└─ support-turn

trace B
└─ search-policy
```

한 가지 조건만 바꾸기 때문에 trace가 갈라진 원인을 current context 차이로 설명할 수 있다.

## 3. 환경 준비

Deck dependency contract는 root의 [`pyproject.toml`](../../pyproject.toml)이 소유한다.
현재 범위는 Langfuse Python SDK v4이며 `langfuse>=4.16,<5`를 사용한다.

```bash
cd decks/llmops-langfuse
uv sync
```

Langfuse Cloud 또는 self-hosted project의 key를 shell environment에 넣는다.
실제 secret은 Git에 기록하지 않는다.

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

`LANGFUSE_BASE_URL`은 key가 속한 Cloud region 또는 self-hosted deployment와 맞아야 한다.

## 4. 실행 전에 예측한다

먼저 코드를 실행하지 말고 다음을 예상한다.

1. baseline에서 trace는 몇 개 생길까?
2. observation은 몇 개 생길까?
3. `support-turn`과 `search-policy`의 `trace_id`는 같을까?
4. 두 observation의 `observation_id`도 같을까?
5. `search-policy` block이 끝난 직후 current observation은 무엇일까?

그 다음 실행한다.

```bash
uv run python textbook/01-first-trace/first_trace.py
```

Script는 learner-visible evidence를 stdout에도 출력한다.

```text
root_trace_id=...
root_observation_id=...
search_trace_id=...
search_observation_id=...
current_after_search=...
same_trace=true
```

ID의 실제 값은 매번 달라질 수 있다. 비교해야 하는 것은 **값 자체가 아니라 관계**다.

- root와 search의 `trace_id`가 같은가?
- root와 search의 `observation_id`가 다른가?
- `current_after_search`가 root observation ID로 복원되는가?

Langfuse UI에서도 같은 실행의 observation tree를 확인한다.

## 5. 코드에서 state가 어떻게 변하는가

핵심 부분은 다음과 같다.

```python
with langfuse.start_as_current_observation(
    as_type="span",
    name="support-turn",
) as root:
    search_policy(langfuse, "환불 기간")
```

실행 state를 풀어 쓰면 다음과 같다.

```text
with root 진입
current observation = support-turn

search-policy 진입
current observation = search-policy
trace context = support-turn과 동일

search-policy 종료
current observation = support-turn 으로 복원

root 종료
current observation = 없음
```

`search_policy()`가 root의 child가 되는 이유는 이름이나 Python call stack 때문이 아니다.
`search-policy`가 시작될 때 `support-turn`이 current observation이었기 때문이다.

## 6. 한 조건만 바꾼다

이제 같은 script를 다음처럼 실행한다.

```bash
uv run python textbook/01-first-trace/first_trace.py --detach-search
```

이 variation에서는 root context가 닫힌 뒤 `search-policy`를 시작한다.

실행 전에 예상한다.

- `same_trace`는 어떻게 바뀔까?
- `search_trace_id`는 root와 어떤 관계가 될까?
- `search-policy`의 parent가 사라지는 이유는 무엇일까?
- 함수 `search_policy()` 자체는 그대로인데 trace topology가 바뀌는 이유는 무엇일까?

기대하는 핵심 차이는 다음과 같다.

```text
baseline  → same_trace=true
variation → same_trace=false
```

UI에서는 baseline이 하나의 tree로, variation은 두 개의 root execution으로 보이는지 비교한다.

## 7. `flush()`의 역할

Langfuse SDK는 trace data를 background에서 batch/export할 수 있다.
짧게 실행되고 바로 종료되는 script에서는 process가 export보다 먼저 끝날 수 있다.

그래서 이번 실습은 마지막에 다음을 호출한다.

```python
langfuse.flush()
```

`flush()`는 observation 관계를 만드는 함수가 아니다.
이미 만들어진 telemetry를 short-lived process가 종료되기 전에 내보내는 **export boundary**에 가깝다.

즉 다음 둘을 구분한다.

```text
start_as_current_observation()
→ execution context와 observation lifetime

flush()
→ pending telemetry export 완료를 기다림
```

## 8. `@observe()`는 같은 문제를 더 짧게 푼다

Langfuse는 decorator도 제공한다.

```python
from langfuse import observe


@observe()
def search_policy(query: str) -> str:
    return "구매 후 14일 이내 환불 가능"
```

Decorator는 function input/output, timing, error를 자동으로 capture하기 편하다.
하지만 처음부터 decorator만 사용하면 **observation lifetime과 current context 변화**가 감춰질 수 있다.
그래서 이 deck은 context manager로 mechanism을 먼저 확인한 뒤 decorator로 넘어간다.

## 9. Local contract test

[`test_first_trace.py`](test_first_trace.py)는 Langfuse Cloud credential 없이 실행할 수 있는 작은 contract test다. 외부
SDK를 흉내 내는 fake client를 사용해 **우리 teaching code가 의도한 nesting과 variation을 정확히 수행하는지** 확인한다.

```bash
python textbook/01-first-trace/test_first_trace.py
```

이 test가 증명하는 범위는 제한적이다.

```text
증명함
- baseline에서 child call이 root context 안에서 일어남
- child 종료 뒤 root context를 다시 읽음
- detach variation에서 root context 밖에서 child를 실행함

증명하지 않음
- Langfuse SDK 4.16.x의 실제 runtime behavior
- Cloud ingestion 성공
- UI rendering
```

실제 SDK/API behavior는 current Langfuse documentation과 live playground 실행으로 별도 검증한다.

## 10. 이해도 점검

다음 질문에 코드 없이 답해 본다.

1. `trace_id`와 `observation_id`는 각각 무엇을 식별하는가?
2. 두 observation이 같은 `trace_id`를 가지면서 서로 다른 `observation_id`를 가지는 이유는 무엇인가?
3. nested child가 끝난 뒤 root가 다시 current observation이 되는 것이 왜 유용한가?
4. `search_policy()` 호출을 root 밖으로 옮겼을 뿐인데 새 trace가 생기는 이유는 무엇인가?
5. 모든 Python 함수에 observation을 만들면 오히려 trace가 나빠질 수 있는 이유는 무엇인가?

## 오해하기 쉬운 점

- 함수 하나가 자동으로 observation 하나라는 뜻은 아니다.
- trace는 Python call tree 자체가 아니다.
- 모든 함수에 observation을 만들 필요도 없다.
- `flush()`가 parent/child relationship을 만드는 것도 아니다.
- 의미 있는 operation boundary를 선택해야 한다.

## 다음 장

다음 장에서는 observation을 많이 만드는 법이 아니라
**나중에 사람이 읽고 evaluator가 사용할 수 있는 trace를 어떻게 설계할지** 다룬다.

## References

- [Langfuse SDK Overview](https://langfuse.com/docs/observability/sdk/overview)
- [Get Started with LLM Tracing](https://langfuse.com/docs/observability/get-started)
- [Trace IDs & Distributed Tracing](https://langfuse.com/docs/observability/features/trace-ids-and-distributed-tracing)
- [Python SDK Reference](https://python.reference.langfuse.com/)
