# 6장 · Process 경계를 넘는 Context Propagation

Unit 2에서는 한 process 안에서 current context가 parent-child 관계를 만들었다. 하지만 다른 process는 Python의 current
context를 공유할 수 없다.

그래서 distributed tracing에는 새로운 단계가 필요하다.

```text
Service A current context
→ inject
→ HTTP carrier / traceparent
→ extract
→ Service B context
→ child span
```

## 학습 목표

- in-process context와 cross-process propagation을 구분한다.
- `inject → carrier → extract` 흐름을 설명한다.
- W3C `traceparent`가 trace/parent identity를 process boundary로 전달하는 역할을 설명한다.
- propagation을 끊었을 때 두 service가 별도 trace로 갈라지는 이유를 설명한다.
- Baggage와 span attribute를 구분한다.

## 1. Context와 Propagation은 다르다

Context는 현재 execution과 연결할 trace/span 정보를 담는다.

Propagation은 그 context를 다른 execution unit으로 이동시키는 과정이다.

한 process 안에서는 runtime context mechanism이 이어 준다. HTTP boundary를 넘을 때는 context를 header 같은 carrier에
직렬화해야 한다.

## 2. 실습 구조

두 process를 사용한다.

```text
client.py                 service_b.py
Service A                 Service B
client span
  │
  ├─ inject(traceparent) ───────→ extract
  │                                │
  │                                └─ server span
  │
  └──────── same trace_id ─────────┘
```

## 3. Service B를 실행한다

첫 terminal:

```bash
uv run --locked textbook/06-propagation/service_b.py
```

Service B는 `http://127.0.0.1:8090/`에서 요청을 기다린다.

## 4. 실행 전에 예측한다

두 번째 terminal에서 client를 실행하기 전에 예측한다.

- request header에 어떤 propagation field가 추가될까?
- Service A와 B의 span은 같은 `trace_id`를 가질까?
- Service B span의 parent는 누구일까?

## 5. 정상 propagation

```bash
uv run --locked textbook/06-propagation/client.py
```

client는 실제로 전송할 `traceparent`를 화면에 출력한다. 두 process의 ConsoleSpanExporter output에서 trace ID와 parent
ID를 비교한다.

관찰해야 할 핵심은 “HTTP 요청이 성공했다”가 아니다.

```text
A span.trace_id == B span.trace_id
B parent_id == A span_id
```

## 6. Propagation을 끊는다

```bash
uv run --locked textbook/06-propagation/client.py --drop-context
```

이번에는 HTTP 요청 자체는 성공하지만 carrier에 trace context를 넣지 않는다.

예측한다.

- Service B는 span을 만들 수 있는가?
- 같은 trace에 속하는가?
- Service A의 application behavior는 달라지는가?

이 실험은 **business request 성공과 distributed trace 연결 성공이 서로 다른 상태**라는 것을 보여 준다.

## 7. `traceparent`를 어떻게 읽을까

W3C Trace Context의 `traceparent`는 대략 다음 정보를 담는다.

```text
version-trace_id-parent_span_id-flags
```

learner가 header 문자열을 암기할 필요는 없다. 중요한 것은 Service B가 이 carrier에서 upstream identity를 복원해 새
span의 parent context로 사용한다는 것이다.

## 8. Baggage는 span attribute가 아니다

Baggage는 process/service 경계를 넘어 전달할 수 있는 key-value context다. 하지만 baggage에 값을 넣었다고 모든 span
attribute에 자동 복사되는 것은 아니다.

또한 baggage는 downstream으로 전달되므로 credential, token, PII 같은 민감 정보를 넣으면 안 된다.

## 이해도 점검

1. Unit 2의 current context와 이번 장의 propagation은 어디에서 연결되는가?
2. HTTP 요청이 성공했는데 trace가 둘로 갈라질 수 있는 이유는 무엇인가?
3. `inject`와 `extract`의 책임을 설명해 보자.
4. baggage와 span attribute의 차이를 설명해 보자.

## 다른 사례에 적용하기

Service A → Queue → Worker B 구조를 생각해 보자.

HTTP header가 없더라도 context propagation에 필요한 세 단계는 무엇일까?

- 어떤 객체가 carrier가 될 수 있는가?
- producer는 언제 inject해야 하는가?
- consumer는 언제 extract해야 하는가?

### 참고 기준

- [OpenTelemetry Context propagation](https://opentelemetry.io/docs/concepts/context-propagation/)
- [OpenTelemetry Python propagation](https://opentelemetry.io/docs/languages/python/propagation/)
- [W3C Trace Context](https://www.w3.org/TR/trace-context/)
- [OpenTelemetry Baggage](https://opentelemetry.io/docs/concepts/signals/baggage/)
