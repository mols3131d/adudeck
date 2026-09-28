# Unit 0 · First Trace

첫 실습의 목표는 OpenTelemetry 설정을 많이 배우는 것이 아니다.

**한 process 안에서 세 operation이 어떤 parent/child 관계를 가진 telemetry가 되는지 직접 확인하는 것**이 목표다.

```text
checkout
├─ validate_cart
└─ charge_payment
```

## Learning target

이 unit을 마치면 다음을 설명할 수 있어야 한다.

- span과 trace가 무엇을 표현하는지 구분한다.
- 같은 trace에 속한 span들이 어떤 identifier를 공유하는지 찾는다.
- child span의 parent가 무엇인지 output에서 확인한다.
- `start_as_current_span()`의 `current`가 다음 child span 생성에 왜 중요한지 설명한다.

`Resource`, processor, exporter의 세부 책임은 아직 외우지 않는다. 이번에는 span 관계를 관찰할 수 있을 만큼만 사용한다.

## 1. 먼저 code를 읽는다

[`first_trace.py`](first_trace.py)를 실행하기 전에 다음 control flow를 손으로 그린다.

```text
checkout()
  ├─ validate_cart()
  └─ charge_payment()
```

각 함수는 `tracer.start_as_current_span()`으로 span을 시작한다.

중요한 점은 `with` block 안에서 span이 **current span**이 된다는 것이다. 그 안에서 다른 span을 시작하면 별도 parent를
직접 지정하지 않아도 현재 context를 이용해 parent/child 관계가 만들어진다.

현재 script는 `SimpleSpanProcessor`와 `ConsoleSpanExporter`를 사용한다.

```text
Span ends
   ↓
SimpleSpanProcessor
   ↓
ConsoleSpanExporter
   ↓
stdout
```

`SimpleSpanProcessor`는 학습 중 span 하나가 끝날 때 바로 관찰하기 쉽게 선택한 teaching setup이다. Network exporter를
사용하는 일반 application에서는 batching이 더 적합할 수 있으며, 그 차이는 이후 unit에서 다룬다.

## 2. Predict

실행하기 전에 다음 질문에 답한다.

1. span은 총 몇 개 만들어질까?
2. 세 span의 `trace_id`는 같을까, 다를까?
3. `validate_cart`의 parent는 어떤 span일까?
4. `charge_payment`의 parent는 어떤 span일까?
5. `checkout`에도 parent가 있을까?

정확한 16진수 identifier 값을 맞히는 것이 아니다. **identifier 사이의 관계**를 예측한다.

## 3. Run

Deck root에서 실행한다.

```bash
uv sync
uv run textbook/00-first-trace/first_trace.py
```

먼저 application output이 보이고, span이 끝날 때 `ConsoleSpanExporter`의 JSON output이 이어진다.

```text
validate_cart: ok
...
charge_payment: ok
...
```

JSON 전체를 읽으려고 하지 말고 각 span에서 다음 field만 찾는다.

```text
name
context.trace_id
context.span_id
parent_id
attributes
resource.attributes.service.name
```

## 4. Observe

세 span을 작은 표로 직접 옮겨 적는다.

| span | trace_id | span_id | parent_id |
| --- | --- | --- | --- |
| checkout |  |  |  |
| validate_cart |  |  |  |
| charge_payment |  |  |  |

다음 invariant가 실제 output에서 성립하는지 확인한다.

- 세 span은 하나의 logical checkout execution을 표현한다.
- child span은 자신만의 `span_id`를 가진다.
- child의 `parent_id`는 parent span의 `span_id`와 연결된다.
- `service.name`은 세 span 모두 같은 application resource에서 온 telemetry임을 보여준다.

Output 순서만 보고 parent/child 관계를 판단하지 않는다. Child span은 parent보다 먼저 끝날 수 있으므로 console에 먼저
export될 수 있다. 관계의 근거는 identifier다.

## 5. Interpret

이 실습에서 trace를 다음처럼 이해하면 된다.

```text
Trace
= 하나의 logical execution을 연결하는 span들의 관계
```

그리고 span은:

```text
Span
= 그 execution 안의 한 operation에 대한 telemetry record
```

따라서 `checkout`, `validate_cart`, `charge_payment`는 서로 다른 span이지만 같은 `trace_id`를 공유할 수 있다.
`span_id`는 각각 다르고, `parent_id`가 tree structure를 만든다.

## 6. Variation · current context를 끊어 본다

이제 [`first_trace.py`](first_trace.py)에서 **`charge_payment()` 호출 한 줄만** `checkout` span의 `with` block 밖으로
옮긴다. 다른 코드는 바꾸지 않는다.

실행 전에 먼저 예측한다.

- `charge_payment`의 `trace_id`는 이전과 같을까?
- `parent_id`는 무엇이 될까?
- `checkout`과 `validate_cart`의 관계는 그대로 유지될까?

다시 실행한 뒤 표를 새로 작성한다.

이 variation의 목적은 “indentation을 바꾸면 output이 달라진다”가 아니다. `charge_payment()`가 실행될 때 **current span이
존재하는가**가 새 span의 관계를 어떻게 바꾸는지 설명하는 것이 목적이다.

실험이 끝나면 파일을 원래 상태로 되돌린다.

## Checkpoint

다음 질문에 자신의 말로 답할 수 있으면 이 unit의 목표를 달성한 것이다.

1. `trace_id`와 `span_id`는 각각 무엇을 식별하는가?
2. child span은 parent를 어떻게 알게 되었는가?
3. console에 출력된 순서와 span tree가 반드시 같은 순서가 아닌 이유는 무엇인가?
4. `charge_payment()`를 current span 밖으로 옮겼을 때 trace 관계가 달라진 이유는 무엇인가?

다음 slice에서는 span에 attribute와 failure evidence를 어떻게 남기고, “실패한 operation”을 telemetry에서 어떻게 읽을지
다룬다.
