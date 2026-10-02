# 2장 · 첫 트레이스

첫 실습에서는 **한 프로세스 안에서 세 작업이 스팬으로 기록되고, current context를 통해 부모·자식 관계로 연결되는 과정**을 직접 확인한다.

```text
checkout
├─ validate_cart
└─ charge_payment
```

## 학습 목표

이 장을 마치면 다음을 설명할 수 있어야 한다.

- 스팬과 트레이스가 무엇을 표현하는지 구분한다.
- 같은 트레이스에 속한 스팬이 공유하는 `trace_id`와 각 스팬의 `span_id`를 구분한다.
- `parent_id`를 이용해 출력 순서와 무관하게 span tree를 복원한다.
- `start_as_current_span()`이 current context를 바꾸고 복원하는 과정을 설명한다.
- 함수 호출 관계와 telemetry 관계가 같은 것이 아님을 설명한다.

`Resource`, processor, exporter의 세부 책임은 아직 외우지 않는다. 이번 장에서는 span 관계를 관찰할 수 있을 만큼만 사용하고, [4장](../04-resource-api-sdk/README.md)에서 다시 분해한다.

## 1. 코드를 실행하기 전에 구조를 읽는다

[`first_trace.py`](first_trace.py)를 먼저 읽고 다음 제어 흐름을 손으로 그린다.

```text
checkout()
  ├─ validate_cart()
  └─ charge_payment()
```

함수 호출 구조만 보고 span tree가 반드시 같다고 결론 내리지는 않는다. **함수는 실행 단위이고, span은 instrumentation이 선택한 관찰 단위**이기 때문이다.

## 2. 스팬과 트레이스

가게에서 주문 한 건을 처리한다고 생각해 보자. 장바구니를 확인하고 결제를 마친다. 나중에 어느 작업이 오래 걸렸는지 알고 싶다면 각 작업의 시작과 끝, 그리고 작업 사이의 관계를 기록해야 한다.

**스팬(span)은 instrumented operation 하나를 시간 범위와 함께 표현하는 기록**이라고 생각하면 된다.

| 코드 이름 | 이 예제에서 표현하는 operation |
| --- | --- |
| `checkout` | 주문 한 건 처리 |
| `validate_cart` | 장바구니 검증 |
| `charge_payment` | 결제 |

관련 span을 한 논리적 실행으로 연결한 것이 trace다.

```text
trace_id  → 어느 trace에 속하는가
span_id   → 이 span은 무엇인가
parent_id → 바로 위 부모 span은 무엇인가
```

루트 span은 활성 부모 없이 시작하므로 ConsoleSpanExporter 출력에서 `parent_id`가 `null`이다.

## 3. Current context가 관계를 만든다

각 함수는 `tracer.start_as_current_span()`으로 span을 시작한다.

```python
with tracer.start_as_current_span("checkout"):
    validate_cart()
    charge_payment()
```

`checkout` 블록에 들어가면 `checkout` span이 current span이 된다. 그 상태에서 `validate_cart` span을 시작하면 SDK는 current context를 부모 context로 사용한다.

```text
before checkout block     current: none
inside checkout block     current: checkout
inside validate block     current: validate_cart
leave validate block      current: checkout
inside payment block      current: charge_payment
leave payment block       current: checkout
leave checkout block      current: none
```

`validate_cart` 블록을 빠져나오면 이전 context인 `checkout`이 복원된다. 그래서 다음 `charge_payment`는 `validate_cart`의 자식이 아니라 `checkout`의 또 다른 자식이 된다.

여기서 중요한 불변식은 이것이다.

> **새 span의 부모 관계는 Python 함수의 호출자 이름이 아니라 span을 시작하는 순간의 context에 의해 결정된다.**

함수 호출만으로 span이 자동 생성되는 것도 아니다. 함수 하나에 span이 없을 수도 있고, 함수 하나가 여러 span을 만들 수도 있다.

## 4. 이번 실습의 export 경로

현재 스크립트는 학습자가 span 데이터를 바로 읽을 수 있도록 단순한 경로를 사용한다.

```text
span 종료
   ↓
SimpleSpanProcessor
   ↓
ConsoleSpanExporter
   ↓
stdout
```

`SimpleSpanProcessor`는 span이 끝날 때 exporter를 즉시 호출한다. 네트워크 전송에서는 batching이 더 적합한 경우가 많지만, 이번 장의 목표는 processor 성능이 아니라 span 관계를 눈으로 확인하는 것이다.

## 5. 실행 결과를 예측한다

실행 전에 다음 질문에 답한다.

1. span은 총 몇 개 만들어질까?
2. 세 span의 `trace_id`는 같을까?
3. `validate_cart`의 `parent_id`는 어느 `span_id`와 같을까?
4. `charge_payment`의 `parent_id`는 어느 `span_id`와 같을까?
5. `checkout`의 `parent_id`는 무엇일까?

정확한 16진수 값을 맞히는 것이 아니다. **식별자 사이의 관계**를 예측한다.

## 6. 실행하고 필요한 필드만 본다

먼저 [환경 준비](../01-setup/README.md)를 마친다. 덱 최상위 디렉터리에서 실행한다.

```bash
uv run --locked textbook/02-first-trace/first_trace.py
```

애플리케이션 메시지와 ConsoleSpanExporter JSON이 함께 나온다.

```text
validate_cart: ok
...
charge_payment: ok
...
```

JSON 전체를 한 번에 이해하려 하지 말고 다음 필드만 찾는다.

```text
name
context.trace_id
context.span_id
parent_id
attributes
resource.attributes.service.name
```

세 span을 표로 옮긴다.

| span | trace_id | span_id | parent_id |
| --- | --- | --- | --- |
| checkout |  |  |  |
| validate_cart |  |  |  |
| charge_payment |  |  |  |

다음 관계가 실제 출력에서 성립하는지 확인한다.

- 세 span의 `trace_id`가 같다.
- 세 span의 `span_id`는 서로 다르다.
- 두 child의 `parent_id`가 `checkout.span_id`와 같다.
- 세 span에서 `service.name=adudeck-otel-first-trace`가 관찰된다.

마지막 항목을 과도하게 해석하지 않는다. **같은 `service.name` 값만으로 같은 process나 같은 Resource object라고 증명할 수는 없다.** 이 예제에서 세 span이 같은 Resource configuration을 갖는 직접적인 이유는 하나의 `TracerProvider(resource=...)`를 공유하기 때문이다. Resource의 의미는 4장에서 다룬다.

## 7. 출력 순서에서 tree를 추측하지 않는다

Child span은 parent보다 먼저 끝날 수 있다. 따라서 ConsoleSpanExporter에는 child가 parent보다 먼저 나타날 수 있다.

```text
출력 순서 ≠ span tree
```

관계의 근거는 `trace_id`, `span_id`, `parent_id`다.

예를 들어 `checkout.span_id=C`, `validate_cart.span_id=V`, `charge_payment.span_id=P`라고 하자.

```text
validate_cart.parent_id = C
charge_payment.parent_id = C
```

이라면 V와 P는 형제다. 반대로 `charge_payment.parent_id=V`라면 payment는 validation의 자식이다. 같은 `trace_id`만 확인해서는 이 두 tree를 구분할 수 없다.

## 8. 변형 실험 · current context를 끊는다

[`first_trace.py`](first_trace.py)에서 **`charge_payment()` 호출 한 줄만** `checkout` span의 `with` 블록 밖으로 옮긴다. 다른 코드는 바꾸지 않는다.

실행 전에 예측한다.

- 이번 실행에서 `charge_payment`는 `checkout`과 같은 `trace_id`를 가질까?
- `charge_payment.parent_id`는 무엇이 될까?
- `checkout`과 `validate_cart`의 관계는 그대로 유지될까?

다시 실행한 뒤 새 표를 작성한다.

이번 실험에서는 들여쓰기 자체보다 `charge_payment()`가 실행되는 순간 **활성 current span이 있는가**를 본다.

`checkout`의 `with` 블록을 이미 빠져나왔다면 이전 context가 복원되어 활성 parent span이 없다. 그러면 `charge_payment`는 새 root span이 되고 새 trace를 시작한다.

서로 다른 실행에서 생성된 임의의 ID 값을 직접 비교하지 않는다. **변형 실행 하나 안에서** `charge_payment`와 `checkout`의 관계를 비교한다.

실험이 끝나면 파일을 원래 상태로 되돌린다.

## 이해도 점검

다음 질문에 자신의 말로 답할 수 있으면 이 장의 목표를 달성한 것이다.

1. `trace_id`, `span_id`, `parent_id`는 각각 어떤 관계를 표현하는가?
2. `validate_cart`가 끝난 뒤 `checkout` context가 다시 current가 되는 이유는 무엇인가?
3. ConsoleSpanExporter 출력 순서만으로 span tree를 판단할 수 없는 이유는 무엇인가?
4. 함수가 여전히 `checkout()` 내부에서 호출되더라도 `charge_payment`가 새 trace가 될 수 있는 이유는 무엇인가?
5. 같은 `service.name`을 봤다는 사실과 같은 trace라는 사실은 왜 다른가?

## 다른 사례에 적용하기

다음 span 기록을 발견했다고 하자. T, A, B, C, D는 실제 식별자 대신 붙인 이름표다.

| name | trace_id | span_id | parent_id |
| --- | --- | --- | --- |
| read_file | T | C | B |
| parse_file | T | B | A |
| save_result | T | D | A |
| import_job | T | A | null |

다음 조건을 가정한다.

- 코드는 동기식으로 실행된다.
- `import_job` 시작 전에는 활성 span이 없다.
- 각 operation은 `start_as_current_span()`의 중첩된 `with` 블록으로 표현된다.

과제를 수행한다.

1. 함수 이름이나 출력 순서에 기대지 않고 span tree를 그린다. 각 연결선을 어떤 식별자로 판단했는지 설명한다.
2. `parse_file` 블록 안에서 `read_file`을 시작했다고 하자. `read_file`의 `with` 블록을 빠져나온 직후 current span과 `parse_file` 블록을 빠져나온 직후 current span을 각각 예측한다.
3. `save_result`만 `import_job`의 `with` 블록 밖에서 시작하도록 옮기면 어떤 관계가 바뀌는가? `read_file`과 `parse_file` 사이에서 유지되어야 할 관계도 설명한다.

스스로 점검할 기준은 세 가지다.

- root를 `parent_id`로 찾았는가?
- 모든 연결선을 `span_id`/`parent_id` 관계로 설명했는가?
- block exit를 context 복원과 연결했는가?

답이 막히면 실행 순서가 아니라 **span을 시작하는 순간의 current context**를 다시 추적한다.
