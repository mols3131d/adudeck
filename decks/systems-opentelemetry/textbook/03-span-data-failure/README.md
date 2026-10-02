# 3장 · Span data와 실패

Unit 2에서는 span의 **관계**를 읽었다. 이제 같은 span 안에서 “무슨 일이 있었는가”를 읽는다.

한 작업이 실패했다고 해서 단순히 exception text를 남기는 것으로 충분하지 않다. 관찰하는 사람은 최소한 다음을 구분해야
한다.

- operation 자체가 실패했는가?
- 실패 유형은 무엇인가?
- 내부에서 오류가 발생했지만 처리되어 operation은 성공했는가?
- 어떤 입력이나 상태가 결과를 설명하는가?

## 학습 목표

이 장을 마치면 다음을 할 수 있어야 한다.

- span attribute와 status가 서로 다른 질문에 답한다는 것을 설명한다.
- 성공한 operation의 status를 억지로 `OK`로 채우지 않고 기본 `UNSET`과 구분한다.
- 최종 실패에는 `StatusCode.ERROR`와 low-cardinality `error.type`을 연결한다.
- 내부에서 처리된 오류와 최종 operation failure를 구분한다.
- exception detail과 operation failure semantics를 같은 것으로 취급하지 않는다.

## 1. 실패에는 층위가 있다

다음 코드를 생각해 보자.

```text
checkout
├─ reserve_inventory  ← 첫 시도 실패, fallback 처리 후 성공
└─ charge_payment     ← 최종 실패
```

`reserve_inventory` 내부에서 한 번 오류가 발생했다는 사실만으로 `checkout` 전체를 실패로 표시하면 잘못된 모델이 된다.
반대로 `charge_payment`가 실패했는데 status를 그대로 두면 operation failure를 숨기게 된다.

핵심은 **“exception이 있었는가?”보다 “이 operation은 최종적으로 실패했는가?”**다.

OpenTelemetry Semantic Conventions의 현재 error guidance도 handled/retried error와 최종 operation failure를 구분한다.
실패한 operation은 span status를 `Error`로 두고, `error.type`에는 예측 가능하고 낮은 cardinality의 실패 유형을 기록하는
방향을 권장한다.

## 2. attribute와 status의 역할

이번 장에서는 다음처럼 나눈다.

| 정보 | 예 | 질문 |
| --- | --- | --- |
| attribute | `payment.method=card` | 어떤 조건에서 일어났는가? |
| attribute | `error.type=__main__.PaymentDeclined` | 어떤 실패 유형인가? |
| span status | `ERROR` | 이 operation은 최종적으로 실패했는가? |

`error.type`에 exception message 전체를 넣지 않는다. 메시지는 사용자 입력이나 동적 값 때문에 cardinality가 폭발할 수
있다.

## 3. 실행 전에 예측한다

[`span_failure.py`](span_failure.py)는 두 시나리오를 실행한다.

1. 재고 예약에서 첫 시도가 실패하지만 fallback으로 성공한다.
2. 결제가 거절되어 operation이 최종 실패한다.

실행 전에 적어 보자.

- 어떤 span이 `ERROR`가 되어야 하는가?
- `reserve_inventory`에 `error.type`이 남아야 하는가?
- 실패한 `charge_payment`의 `error.type`은 어떤 종류의 값이어야 하는가?
- 실패한 child span이 있으면 parent `checkout`도 자동으로 `ERROR`가 될까?

마지막 질문이 중요하다. **child의 status가 parent에 자동 전파된다고 가정하지 않는다.** 각 operation의 의미는 해당
instrumentation이 결정한다.

## 4. 실행한다

덱 최상위 디렉터리에서 실행한다.

```bash
uv run --locked textbook/03-span-data-failure/span_failure.py
```

출력에서 두 시나리오의 span을 나눠 보고 다음 필드를 찾는다.

```text
name
status.status_code
attributes.error.type
attributes.checkout.result
attributes.inventory.fallback_used
```

## 5. 관찰하고 해석한다

첫 시나리오에서는 inventory의 첫 시도가 실패하지만 operation은 fallback으로 완료된다. 따라서 “처리된 내부 오류가
있었다”는 사실과 “operation이 실패했다”는 결론을 분리해야 한다.

두 번째 시나리오에서는 결제 operation이 최종 실패하므로 `charge_payment` span에 `ERROR`와 `error.type`이 남는다.

여기서 parent `checkout`의 status도 코드가 명시적으로 결정한다. OpenTelemetry가 child status를 보고 비즈니스 의미를
추론해 주지 않는다.

## 6. `record_exception()`은 무엇인가

Python API에는 exception event를 span에 기록하는 `record_exception()` 기능이 있다. 하지만
**exception event와 span status는 같은 개념이 아니다.** 또한 최신 Semantic Conventions의 error guidance는 exception
detail을 log record로 기록하는 방향을 제시하고 있다.

따라서 이 덱에서는 다음 순서로 사고한다.

```text
operation semantics
→ failed / succeeded 판단
→ span status + error.type
→ 필요한 경우 exception detail을 별도 signal로 기록
```

`record_exception()`을 “실패를 기록하는 유일한 정답”으로 외우지 않는다.

## 7. 변형 실험

`run_checkout(payment_should_fail=True)` 안에서 payment 실패를 catch한 뒤 fallback 결제수단으로 성공하도록 바꿔 보자.

변경 전에 예측한다.

- `charge_payment`는 여전히 `ERROR`여야 하는가?
- `checkout`은 `ERROR`여야 하는가?
- “실패한 시도”와 “최종 operation 결과”를 하나의 span으로 표현하는 것이 적절한가, 별도 child span이 더 나은가?

정답보다 reasoning이 중요하다. instrumentation boundary가 무엇을 operation으로 정의했는지 먼저 말할 수 있어야 한다.

## 이해도 점검

1. status와 `error.type`은 각각 어떤 질문에 답하는가?
2. handled error를 최종 operation failure로 기록하면 어떤 오해가 생기는가?
3. `error.type`에 사용자 메시지 전체를 넣지 않는 이유는 무엇인가?
4. child span의 실패가 parent span의 실패를 자동으로 결정하지 않는 이유는 무엇인가?

## 다른 사례에 적용하기

HTTP client가 요청을 보냈고 첫 연결은 timeout이었지만 재시도 후 200 응답을 받았다.

- 전체 HTTP client operation을 하나의 span으로 본다면 최종 status는 무엇이어야 하는가?
- retry attempt를 별도 span으로 본다면 어떤 span에 failure evidence를 남길 수 있는가?
- `error.type`에 timeout의 구체 메시지 대신 어떤 종류의 값을 쓰는 것이 더 안정적인가?

### 참고 기준

- [OpenTelemetry Semantic Conventions · Recording errors](https://opentelemetry.io/docs/specs/semconv/general/recording-errors/)
- [OpenTelemetry Semantic Conventions · `error.type`](https://opentelemetry.io/docs/specs/semconv/registry/attributes/error/)
- [OpenTelemetry Python manual instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/)
