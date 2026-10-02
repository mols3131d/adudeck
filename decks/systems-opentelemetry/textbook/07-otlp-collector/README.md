# 7장 · OTLP와 Collector

지금까지 span은 application process의 `ConsoleSpanExporter`에서 바로 stdout으로 갔다. 이제 처음으로
**telemetry를 application process 밖으로 보낸다.**

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
- application이 출력한 trace/span ID와 Collector가 받은 ID를 비교해 같은 telemetry execution임을 확인한다.
- telemetry delivery failure와 business operation failure를 구분한다.

## 준비할 것

이 장은 Docker가 필요하다. 다음 두 command가 성공해야 한다.

```bash
docker version
docker info
```

Docker를 사용할 수 없는 환경에서는 config와 data path 설명까지 학습하고, runtime evidence는 Docker가 가능한 환경에서
다시 확인한다. 이 경우 “Collector까지 검증했다”고 주장하지 않는다.

현재 calibration 기준은 다음과 같다.

- OpenTelemetry Python OTLP HTTP exporter `1.45.0`
- OpenTelemetry Collector `0.162.0`

## 1. OTLP는 telemetry transport contract다

OTLP exporter는 OpenTelemetry data model을 다른 process로 보내기 위해 사용한다.

이번 장에서는 HTTP/protobuf를 사용한다.

```text
http://127.0.0.1:4318/v1/traces
```

4318은 OTLP/HTTP의 기본 port다. gRPC 4317도 널리 사용되지만 이번 장에서는 protocol 자체가 학습 노이즈가 되지 않도록 HTTP
하나만 사용한다.

## 2. Collector는 pipeline을 조립한다

[`collector-config.yaml`](collector-config.yaml)은 최소 trace pipeline이다.

```text
receiver: otlp
   ↓
processor: batch
   ↓
exporter: debug
```

Collector config의 핵심 함정은 **component를 선언했다고 자동으로 실행되는 것이 아니라는 점**이다.
`service.pipelines.traces`에 연결되어야 해당 signal pipeline에서 사용된다.

## 3. Collector를 실행한다

덱 최상위 디렉터리에서 실행한다.

```bash
docker run --rm \
  --name adudeck-otel-collector \
  -p 127.0.0.1:4318:4318 \
  -v "$PWD/textbook/07-otlp-collector/collector-config.yaml:/etc/otelcol/config.yaml:ro" \
  otel/opentelemetry-collector:0.162.0
```

`127.0.0.1:4318:4318`은 host 쪽 publish를 loopback으로 제한한다. 단순히 `-p 4318:4318`로 쓰면 Docker는 기본적으로
host의 모든 network interface에 port를 publish할 수 있으므로, 이 localhost 학습에서는 불필요한 노출을 만들지 않는다.

Collector를 종료할 때는 해당 terminal에서 `Ctrl-C`를 사용한다. 다른 terminal에서 정리해야 한다면 다음 command를 사용할
수 있다.

```bash
docker rm -f adudeck-otel-collector
```

`--rm`을 사용했으므로 container가 종료되면 playground-owned container state는 남지 않는다.

## 4. Application을 실행한다

Collector가 뜬 뒤 다른 terminal에서 실행한다.

```bash
uv run --locked \
  --with 'opentelemetry-exporter-otlp-proto-http==1.45.0' \
  textbook/07-otlp-collector/otlp_trace.py
```

application은 다음 evidence를 먼저 출력한다.

```text
application trace_id=... span_id=...
application endpoint=http://127.0.0.1:4318/v1/traces
checkout: business work completed
```

그 뒤 `BatchSpanProcessor`가 ended span을 OTLP exporter에 넘기고, `provider.shutdown()`이 pending export를 flush한 뒤
process가 끝난다.

## 5. 같은 span이 Collector까지 갔는지 확인한다

Application terminal의 trace/span ID를 기록한다.

Collector terminal의 debug exporter output에서 `checkout` span을 찾고 같은 ID를 확인한다.

```text
application trace_id/span_id
           ==
Collector debug trace_id/span_id
```

이 equality가 중요한 이유는 단순히 “Collector에 checkout이라는 이름이 보였다”보다 강한 evidence이기 때문이다. 같은
logical span이 process boundary를 건넜음을 identifier로 확인한다.

Collector 쪽에 그 span이 보인다면 최소한 다음 경계는 통과했다.

```text
SDK / BatchSpanProcessor
→ OTLP HTTP exporter
→ HTTP transport
→ Collector OTLP receiver
→ traces pipeline
→ batch processor
→ debug exporter
```

아직 external backend storage나 UI를 검증한 것은 아니다.

## 6. 실패 실험 · source를 수정하지 않고 endpoint를 틀린다

baseline source를 직접 수정하지 않는다. command-line option 하나만 바꾼다.

```bash
uv run --locked \
  --with 'opentelemetry-exporter-otlp-proto-http==1.45.0' \
  textbook/07-otlp-collector/otlp_trace.py \
  --endpoint http://127.0.0.1:4319/v1/traces
```

예측한다.

- `checkout: business work completed`는 출력되는가?
- application trace/span ID는 만들어지는가?
- Collector debug output에 그 ID가 나타나는가?
- export failure와 application failure는 같은가?

telemetry export 실패가 business operation을 반드시 실패시키는 것은 아니다.

실험 후 reset은 source edit 복원이 아니라 **기본 command를 다시 실행하는 것**뿐이다.

## 7. 실패 실험 · pipeline을 끊는다

`collector-config.yaml` 자체를 망가뜨리지 말고 disposable copy를 만든다.

```bash
cp textbook/07-otlp-collector/collector-config.yaml /tmp/adudeck-otel-collector.yaml
```

복사본의 `service.pipelines.traces`에서 receiver 연결을 제거하거나 traces pipeline을 제거해 본다.

OpenTelemetry Collector에서는 receiver를 `receivers:`에 **configure**하는 것과 `service.pipelines`에 넣어 **enable**하는
것이 별개다.

Collector version과 validation rule에 따라 active pipeline이 없는 config를 startup 단계에서 거부할 수 있다. 그 경우
startup error 자체가 configuration boundary evidence다. 시작은 되지만 listener/data path가 없어진다면 그것도 별개의
evidence다.

실험이 끝나면 `/tmp/adudeck-otel-collector.yaml`만 삭제한다.

```bash
rm -f /tmp/adudeck-otel-collector.yaml
```

핵심 질문은 이것이다.

> component가 파일에 존재하는 것과 active data path에 연결되는 것은 같은가?

정답은 아니다. configured component는 `service`에서 참조되어야 활성화된다.

## 8. 검증 경계를 말로 표현한다

다음 문장을 구분할 수 있어야 한다.

- “application에서 span을 만들었다.”
- “OTLP exporter가 Collector endpoint로 전송을 시도했다.”
- “Collector debug exporter에서 **같은 trace/span ID**를 확인했다.”
- “외부 backend에 저장되고 query된다.”

앞 문장이 뒤 문장을 자동으로 증명하지 않는다.

## 이해도 점검

1. OTLP exporter와 Collector의 역할은 어떻게 다른가?
2. receiver가 선언되어 있어도 telemetry를 못 받을 수 있는 이유는 무엇인가?
3. Collector debug exporter에서 같은 trace/span ID를 봤을 때 어디까지 검증했다고 말할 수 있는가?
4. business output은 성공했는데 Collector에 span이 없을 수 있는 이유는 무엇인가?
5. backend가 없는데도 Unit 7의 transport/Collector mechanism을 학습할 수 있는 이유는 무엇인가?

## 다른 사례에 적용하기

Collector가 OTLP를 정상적으로 받고 debug exporter에도 span을 출력하지만 vendor backend에는 데이터가 없다.

Unit 9에 들어가기 전에, 문제 범위를 어느 boundary 이후로 좁힐 수 있는지 설명해 보자.

### 참고 기준

- [OpenTelemetry Python exporters](https://opentelemetry.io/docs/languages/python/exporters/)
- [OTLP exporter configuration](https://opentelemetry.io/docs/languages/sdk-configuration/otlp-exporter/)
- [Collector Docker installation](https://opentelemetry.io/docs/collector/install/docker/)
- [OpenTelemetry Collector configuration](https://opentelemetry.io/docs/collector/configuration/)
- [OpenTelemetry Collector troubleshooting](https://opentelemetry.io/docs/collector/troubleshooting/)
- [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/)
