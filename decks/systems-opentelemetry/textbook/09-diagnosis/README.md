# 9장 · Telemetry Pipeline Diagnosis

마지막 장에서는 새로운 component를 더 배우기보다 지금까지 만든 경계를 **진단 도구로 사용**한다.

“Grafana에 trace가 안 보인다”는 하나의 문제처럼 보이지만 실제 data path는 여러 단계다.

```text
business operation
→ instrumentation
→ SDK / processor
→ exporter
→ OTLP transport
→ Collector receiver
→ Collector processors
→ Collector exporter
→ backend ingestion
→ query / UI
```

좋은 diagnosis는 모든 설정을 한꺼번에 바꾸는 것이 아니라
**마지막으로 확인된 evidence와 첫 번째로 사라진 evidence 사이**를 좁힌다.

## 학습 목표

- telemetry pipeline을 hop-by-hop evidence boundary로 나눈다.
- data absence를 곧바로 “instrumentation bug”나 “backend bug”로 단정하지 않는다.
- controlled failure를 사용해 hypothesis를 검증한다.
- sampling처럼 “데이터가 없어도 pipeline 고장이 아닐 수 있는 이유”를 고려한다.
- trace에서는 trace/span ID로 같은 execution을 연결하고, metric에서는 Resource·attributes·time window를 이용해 관련 관찰 범위를 좁힌다.
- 서로 다른 signal의 correlation과 개별 execution identity를 같은 것으로 취급하지 않는다.

## 1. Diagnosis의 기본 질문

항상 다음 두 질문부터 시작한다.

1. **마지막으로 telemetry를 확인한 boundary는 어디인가?**
2. **그 다음 boundary에서 어떤 evidence를 기대하는가?**

예를 들어:

```text
application business output 있음
ConsoleSpanExporter span 있음
Collector debug output 없음
```

이라면 business code와 span creation까지는 이미 지나왔다. 조사 범위는 exporter/transport/Collector receiver 쪽으로
좁아진다.

## 2. Failure matrix

| Failure | application 동작 | local span | Collector debug | backend |
| --- | --- | --- | --- | --- |
| instrumentation 제거 | 성공 가능 | 없음 | 없음 | 없음 |
| propagation 제거 | 성공 가능 | 양쪽 span은 있음 | 있음 | trace가 분리될 수 있음 |
| wrong OTLP endpoint | 성공 가능 | SDK 내부에는 span 생성 | 없음 | 없음 |
| Collector 중지 | 성공 가능 | span 생성 | 없음 | 없음 |
| Collector backend exporter 오류 | 성공 가능 | 있음 | debug branch가 있으면 확인 가능 | 없음 |

이 표를 정답으로 외우지 않는다. 각 failure가 어느 edge를 끊는지 설명할 수 있어야 한다.

## 3. Controlled fault injection

Unit 6과 Unit 7을 재사용해 다음 failure를 하나씩 만든다.

### A. Propagation 제거

```bash
uv run --locked textbook/06-propagation/client.py --drop-context
```

질문:

- telemetry는 사라졌는가, 아니면 두 trace로 갈라졌는가?
- “데이터 없음”과 “correlation 없음”은 어떻게 다른가?

### B. OTLP endpoint 오류

Unit 7의 script는 endpoint를 command-line option으로 바꿀 수 있다. baseline source를 수정하지 않고 실패를 만든다.

```bash
uv run \
  --with 'opentelemetry-exporter-otlp-proto-http==1.45.0' \
  textbook/07-otlp-collector/otlp_trace.py \
  --endpoint http://127.0.0.1:4319/v1/traces
```

질문:

- business output은 남는가?
- Collector가 받을 수 있는가?
- 어느 boundary까지 정상이라고 말할 수 있는가?

실험이 끝나면 별도 reset 없이 기본 endpoint 명령으로 돌아갈 수 있다. source file을 직접 수정하지 않았기 때문이다.

### C. Collector pipeline 오류

Receiver/exporter component를 선언해 두고 `service.pipelines` 연결을 잘못 구성한 disposable config copy를 사용한다.

질문:

- Collector가 시작하지 못하는가?
- 시작은 하지만 data path가 끊기는가?
- config validation과 runtime data evidence를 어떻게 구분할까?

## 4. Debug exporter를 tee처럼 활용한다

실전 diagnosis에서는 backend exporter와 함께 debug exporter를 임시로 붙여 Collector가 어느 단계까지 데이터를 받았는지
확인할 수 있다.

```text
receiver
  ↓
processor
  ├─→ debug exporter
  └─→ backend exporter
```

debug exporter에는 보이는데 backend에는 없다면 instrumentation이나 application을 다시 의심할 필요가 줄어든다.

## 5. “없다”는 evidence는 조심해서 읽는다

Telemetry가 보이지 않는 이유가 항상 failure는 아니다.

예를 들어 **sampling**은 모든 trace candidate를 반드시 record/export하지 않고 일부를 의도적으로 선택할 수 있다. 이 장에서는
sampling algorithm 자체를 설계하지 않는다. 중요한 것은 “관찰 결과가 없음”이 곧바로 pipeline failure를 뜻하지 않을 수
있다는 점이다.

filter/processor가 데이터를 제거할 수도 있고, query time range나 Resource filter가 틀렸을 수도 있다.

따라서 absence를 해석할 때는 다음을 묻는다.

```text
이 데이터는 원래 생성되어야 했는가?
생성되었다면 어느 boundary까지 확인했는가?
중간 단계가 의도적으로 drop할 수 있는가?
내 query가 같은 Resource / attribute / time window를 찾고 있는가?
```

### Trace identity와 metric correlation은 다르다

Trace 안에서는 `trace_id`, `span_id`, `parent_id`로 개별 execution의 관계를 직접 연결할 수 있다.

Metric은 반복 measurement를 집계하므로 일반 metric series 자체에 “이 한 요청의 trace ID”와 같은 execution identity가 있는
것은 아니다. 이번 덱에서는 metric과 trace를 연결할 때 다음 정도까지만 주장한다.

```text
same observed Resource
+ compatible attributes
+ overlapping time window
→ 같은 workload 현상을 조사할 후보 범위를 좁힌다
```

특정 metric measurement와 특정 trace/span을 직접 연결하는 **Exemplar** 같은 mechanism은 현재 core scope가 아니다.
따라서 cross-signal correlation을 per-request identity와 혼동하지 않는다.

## 6. 독립 진단 과제

다음 상황을 해결한다.

> checkout 요청은 정상 응답한다. Service A의 local console에는 client span이 있다. Service B에도 server span이 있다. 두
> span의 trace ID는 다르다. Collector에는 두 span 모두 도착한다.

다음 순서로 답한다.

1. pipeline export 문제인가?
2. instrumentation 자체가 전혀 없는 문제인가?
3. 어느 boundary가 가장 의심스러운가?
4. 어떤 evidence를 추가로 확인하면 hypothesis를 검증할 수 있는가?
5. 한 번에 하나만 바꾼다면 무엇을 바꿀 것인가?

정답의 핵심은 “trace가 없다”가 아니라 **correlation이 끊겼다**는 사실을 먼저 분류하는 것이다.

## 7. 최종 synthesis

이제 다음 전체 흐름을 자신의 말로 설명해 본다.

```text
operation
→ manual/library/zero-code instrumentation
→ API
→ SDK Provider
→ span/metric + Resource + instrumentation scope
→ context / propagation
→ processor
→ exporter
→ OTLP
→ Collector pipeline
→ backend
```

각 화살표마다 한 가지 failure mode와 한 가지 observable evidence를 붙여 보자.

이 작업을 할 수 있다면 OpenTelemetry를 “몇 개의 설정 키”가 아니라 **state와 data flow를 가진 telemetry system**으로
이해한 것이다.

## 완료 평가 기준

다음 능력을 스스로 증명할 수 있어야 한다.

- span tree를 identifier로 복원한다.
- success/handled error/final failure를 구분한다.
- Resource와 Instrumentation Scope를 구분한다.
- manual/library/zero-code instrumentation을 목적에 따라 선택한다.
- `inject → carrier → extract`로 cross-process trace 연결을 설명한다.
- OTLP와 Collector pipeline boundary를 추적한다.
- Counter/UpDownCounter/Histogram을 measurement semantics로 선택한다.
- trace execution identity와 metric aggregation/correlation의 차이를 설명한다.
- telemetry가 사라졌을 때 마지막 확인 evidence부터 다음 hop을 조사한다.

### 참고 기준

- [OpenTelemetry Collector troubleshooting](https://opentelemetry.io/docs/collector/troubleshooting/)
- [OpenTelemetry Collector configuration](https://opentelemetry.io/docs/collector/configuration/)
- [OpenTelemetry Resource specification](https://opentelemetry.io/docs/specs/otel/resource/)
- [OpenTelemetry Metrics exemplars](https://opentelemetry.io/docs/specs/otel/metrics/sdk/#exemplar)
- [OpenTelemetry Demo feature flags](https://opentelemetry.io/docs/demo/feature-flags/)
