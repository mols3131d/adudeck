# 7장 · OTLP와 Collector

지금까지 span은 application process의 `ConsoleSpanExporter`에서 바로 stdout으로 갔다. 이제 처음으로 **telemetry를 application process 밖으로 보낸다.**

```text
Python app
→ OTLP/HTTP
→ Collector receiver
→ Collector pipeline
→ debug exporter
→ Collector stdout
```

아직 vendor backend를 붙이지 않는다. 먼저 transport와 Collector boundary 자체를 증명한다.

## 학습 목표

- Exporter, OTLP, Collector의 책임을 구분한다.
- Collector의 receiver / processor / exporter / service pipeline 구조를 설명한다.
- component를 config에 선언하는 것과 pipeline에 연결해 활성화하는 것을 구분한다.
- application output과 Collector output이 서로 다른 process boundary의 evidence임을 설명한다.

## 1. OTLP는 telemetry transport contract다

OTLP exporter는 OpenTelemetry data model을 다른 process로 보내기 위해 사용한다.

이번 장에서는 HTTP/protobuf를 사용한다.

```text
http://127.0.0.1:4318/v1/traces
```

4318은 OTLP/HTTP의 기본 port다. gRPC 4317도 널리 사용되지만 이번 장에서는 protocol 자체가 학습 노이즈가 되지 않도록 HTTP 하나만 사용한다.

## 2. Collector는 pipeline을 조립한다

[`collector-config.yaml`](collector-config.yaml)은 최소 trace pipeline이다.

```text
receiver: otlp
   ↓
processor: batch
   ↓
exporter: debug
```

Collector config의 핵심 함정은 **component를 선언했다고 자동으로 실행되는 것이 아니라는 점**이다. `service.pipelines.traces`에 연결되어야 해당 signal pipeline에서 사용된다.

## 3. Collector를 실행한다

현재 calibration 기준 Collector는 `0.162.0`이다.

```bash
docker run --rm \
  -p 4318:4318 \
  -v "$PWD/textbook/07-otlp-collector/collector-config.yaml:/etc/otelcol/config.yaml:ro" \
  otel/opentelemetry-collector:0.162.0
```

Collector가 뜬 뒤 다른 terminal에서 application을 실행한다.

## 4. Application을 실행한다

OTLP exporter는 현재 deck core dependency에 포함하지 않고, 이 장에서 검증 기준 version을 명시해 일시적으로 추가한다.

```bash
uv run \
  --with 'opentelemetry-exporter-otlp-proto-http==1.45.0' \
  textbook/07-otlp-collector/otlp_trace.py
```

## 5. 어디를 관찰할까

Application terminal에서는 business output만 보일 수 있다.

Collector terminal에서는 debug exporter가 받은 span을 출력한다.

이 차이가 중요하다.

```text
application process stdout != Collector process stdout
```

Collector 쪽에 span이 보인다면 최소한 다음 경계는 통과했다.

```text
SDK/exporter
→ HTTP transport
→ Collector OTLP receiver
→ traces pipeline
→ debug exporter
```

아직 external backend storage나 UI는 검증한 것이 아니다.

## 6. 실패 실험 1 · endpoint를 틀린다

`otlp_trace.py`의 port를 `4319`로 바꿔 실행한다.

예측한다.

- application business code는 실행되는가?
- Collector debug output은 생기는가?
- export failure는 application failure와 같은가?

telemetry export 실패가 business operation을 반드시 실패시키는 것은 아니다.

## 7. 실패 실험 2 · pipeline에서 receiver를 뺀다

`collector-config.yaml`을 복사한 뒤 `service.pipelines.traces`에서 `otlp` receiver를 참조하지 않는 변형을 만든다. OpenTelemetry Collector에서는 receiver를 `receivers:`에 **configure**하는 것과 `service.pipelines`에 넣어 **enable**하는 것이 별개다.

가장 단순한 관찰 방법은 traces pipeline 자체를 제거한 변형 config로 Collector를 시작한 뒤 4318 listener가 생기는지 확인하는 것이다. Collector version과 validation rule에 따라 “활성 pipeline이 없음”을 startup에서 거부한다면 그 오류도 configuration boundary evidence다.

핵심 질문은 이것이다.

> component가 파일에 존재하는 것과 active data path에 연결되는 것은 같은가?

정답은 아니다. configured component는 `service`에서 참조되어야 활성화된다.

## 이해도 점검

1. OTLP exporter와 Collector의 역할은 어떻게 다른가?
2. receiver가 선언되어 있어도 telemetry를 못 받을 수 있는 이유는 무엇인가?
3. Collector debug exporter에서 span을 봤을 때 어디까지 검증했다고 말할 수 있는가?
4. backend가 없는데도 Unit 7을 학습할 수 있는 이유는 무엇인가?

## 다른 사례에 적용하기

Collector가 OTLP를 정상적으로 받고 debug exporter에도 span을 출력하지만 vendor backend에는 데이터가 없다.

Unit 9에 들어가기 전에, 문제 범위를 어느 boundary 이후로 좁힐 수 있는지 설명해 보자.

### 참고 기준

- [OpenTelemetry Python exporters](https://opentelemetry.io/docs/languages/python/exporters/)
- [OpenTelemetry Collector configuration](https://opentelemetry.io/docs/collector/configuration/)
- [OpenTelemetry Collector troubleshooting](https://opentelemetry.io/docs/collector/troubleshooting/)
