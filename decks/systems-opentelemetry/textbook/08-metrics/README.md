# 8장 · Metrics: 어떤 질문을 어떤 Instrument로 측정할까

Trace는 한 execution의 관계를 깊게 본다. 하지만 “지난 10분 동안 요청이 몇 번 왔는가?”, “동시에 처리 중인 요청은 몇 개인가?”, “latency 분포는 어떤가?”는 개별 trace를 하나씩 읽는 방식으로 답하기 어렵다.

그래서 metrics는 **반복되는 measurement를 집계 가능한 형태로 표현**한다.

## 학습 목표

- Counter, UpDownCounter, Histogram의 measurement semantics를 구분한다.
- 질문에 맞는 instrument를 선택하고 이유를 설명한다.
- attribute 조합이 metric time series cardinality를 늘릴 수 있음을 설명한다.
- trace와 metric이 같은 시스템을 보더라도 서로 다른 질문에 답한다는 것을 설명한다.

## 1. Instrument를 이름으로 외우지 않는다

먼저 질문을 본다.

```text
요청이 총 몇 번 발생했는가?       → Counter
현재 처리 중인 요청 수는?         → UpDownCounter
요청 latency의 분포는?            → Histogram
```

### Counter

값이 누적 방향으로만 증가하는 사건이나 양을 기록한다.

예: request count, processed bytes.

### UpDownCounter

증가와 감소가 모두 가능한 상태 변화에 사용한다.

예: request 시작 시 +1, 종료 시 -1.

### Histogram

개별 measurement의 분포를 집계할 때 사용한다.

예: latency, payload size.

## 2. 실행 전에 예측한다

[`metrics_demo.py`](metrics_demo.py)는 세 checkout 요청을 흉내 낸다.

예측한다.

- request counter의 최종 합은 얼마인가?
- active request 값은 마지막에 얼마로 돌아와야 하는가?
- Histogram에서 평균 하나만 알면 충분한가?

## 3. 실행한다

```bash
uv run --locked textbook/08-metrics/metrics_demo.py
```

ConsoleMetricExporter output은 SDK diagnostic output이라 양이 많다. 이번에는 다음 instrument 이름만 찾아 관계를 읽는다.

```text
checkout.requests
checkout.active
checkout.duration
```

## 4. 같은 label이 항상 좋은 것은 아니다

Metric attribute는 분석 차원을 만든다.

```python
counter.add(1, {"payment.method": "card"})
```

이 값이 `card`, `bank_transfer`처럼 작은 집합이라면 유용할 수 있다.

반면 다음과 같은 값을 attribute로 넣으면 위험하다.

```text
user.id
request.id
raw URL with unique ids
```

각 조합이 별도 time series를 만들 수 있기 때문이다.

**관찰 가능성을 높이려다 cardinality와 비용을 폭발시킬 수 있다.**

## 5. Semantic Conventions는 왜 필요한가

서로 다른 instrumentation이 같은 HTTP request를 서로 다른 metric name, attribute name, unit으로 표현하면 backend에서 합쳐 분석하기 어렵다.

Semantic Conventions는 공통 operation과 signal에 대해 이름과 attribute의 의미를 맞추는 vocabulary를 제공한다.

여기서 중요한 것은 convention을 무조건 외우는 것이 아니라:

```text
같은 의미 → 같은 이름과 단위
```

라는 interoperability 목적을 이해하는 것이다.

Semantic Conventions의 개별 영역은 stability가 다를 수 있으므로 version-sensitive field를 textbook의 영구 불변 사실처럼 가정하지 않는다.

## 6. 변형 실험

`payment.method` 대신 각 요청마다 다른 `checkout.request_id`를 metric attribute로 넣는다고 가정한다.

- 요청 3개면 몇 개의 distinct attribute combination이 생기는가?
- 요청이 초당 수천 건이면 어떤 문제가 생길 수 있는가?
- 이 ID가 개별 실행 추적에 정말 필요하다면 metric보다 어떤 signal이 더 적합할까?

## 7. Trace와 Metric을 함께 생각한다

다음 질문을 signal에 연결해 보자.

| 질문 | 더 직접적인 signal |
| --- | --- |
| 특정 checkout 하나가 왜 느렸나? | trace |
| checkout latency 분포가 지난 1시간 동안 악화됐나? | metric |
| 오류율이 증가한 시점의 개별 실패 흐름은? | metric으로 이상 감지 → trace로 상세 조사 |

둘 중 하나가 다른 하나를 대체하는 것이 아니다.

## 이해도 점검

1. 요청 “횟수”와 “현재 동시 요청 수”가 다른 instrument를 요구하는 이유는 무엇인가?
2. Histogram이 latency에 적합한 이유는 무엇인가?
3. high-cardinality attribute가 왜 문제인가?
4. Semantic Conventions가 vendor lock-in을 줄이는 데 어떤 도움을 주는가?

## 다른 사례에 적용하기

다음 measurement를 어떤 instrument로 표현할지 선택하고 이유를 설명한다.

- queue에 들어온 job 총수
- 현재 queue depth의 변화량
- image processing duration
- 한 user의 raw email address별 request count

마지막 항목은 instrument 선택보다 **attribute design 자체가 적절한지** 먼저 판단해야 한다.

### 참고 기준

- [OpenTelemetry Python metrics instrumentation](https://opentelemetry.io/docs/languages/python/instrumentation/#metrics)
- [OpenTelemetry Metrics specification](https://opentelemetry.io/docs/specs/otel/metrics/)
- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/)
