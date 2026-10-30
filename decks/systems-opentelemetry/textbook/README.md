# OpenTelemetry Textbook

이 textbook은 OpenTelemetry를 “설정법”보다
**telemetry가 어디서 만들어지고, 어떤 상태를 담고, 어떤 경계를 넘어 이동하는지**를 이해하는 순서로 배운다.

처음에는 한 Python process의 span 관계만 본다. 이후 실패 의미, Resource/API/SDK, instrumentation, process boundary,
OTLP/Collector, metrics, diagnosis를 차례로 추가한다.

```text
operation
→ span / metric
→ context
→ Resource + instrumentation scope
→ exporter
→ OTLP
→ Collector
→ backend
```

중요한 원칙은 세 가지다.

1. 실행 전에 관계를 예측한다.
2. 성공 여부가 아니라 learner-visible evidence를 관찰한다.
3. 한 조건만 바꾸고 무엇이 달라지고 무엇이 유지되는지 설명한다.

## Chapters

| 장 | 핵심 질문 |
| --- | --- |
| [0. 소개](00-intro/README.md) | 왜 telemetry가 필요한가? |
| [1. 환경 준비](01-setup/README.md) | 같은 환경에서 관찰을 재현할 수 있는가? |
| [2. 첫 트레이스](02-first-trace/README.md) | current context는 span을 어떻게 한 trace로 연결하는가? |
| [3. Span data와 실패](03-span-data-failure/README.md) | 실패를 span에서 어떤 의미로 표현해야 하는가? |
| [4. Resource와 API/SDK](04-resource-api-sdk/README.md) | 무엇의 telemetry이고, 누가 만들고 처리하는가? |
| [5. Instrumentation](05-instrumentation/README.md) | manual, library, zero-code는 무엇을 각각 잘 보는가? |
| [6. Propagation](06-propagation/README.md) | context는 process boundary를 어떻게 건너는가? |
| [7. OTLP와 Collector](07-otlp-collector/README.md) | telemetry는 application process 밖으로 어떻게 이동하는가? |
| [8. Metrics](08-metrics/README.md) | 어떤 질문을 어떤 instrument로 측정해야 하는가? |
| [9. Diagnosis](09-diagnosis/README.md) | telemetry가 안 보일 때 어느 boundary부터 확인해야 하는가? |

## Competence map

| 능력 | 주로 개발하는 장 | 확인하는 장 |
| --- | --- | --- |
| span/trace 관계를 식별자로 복원 | 2 | 2, 6, 9 |
| 실패 의미를 status/attribute로 표현 | 3 | 3, 9 |
| Resource, Scope, API/SDK 책임 구분 | 4 | 4, 5, 9 |
| instrumentation 방식을 목적에 맞게 선택 | 5 | 5, 9 |
| Semantic Conventions의 interoperability 역할 설명 | 3, 5, 8 | 8, 9 |
| cross-process context propagation 설명 | 6 | 6, 9 |
| OTLP/Collector data path 추적 | 7 | 7, 9 |
| metric instrument 선택과 cardinality 판단 | 8 | 8, 9 |
| pipeline failure를 evidence로 좁히기 | 9 | 9 |

Semantic Conventions는 별도 암기 장으로 떼지 않는다. Unit 3의 error 의미, Unit 5의 library instrumentation, Unit 8의
metric naming/attribute 의미에서 반복해서 연결한다.

## 읽는 방법

각 장의 실습은 가능한 한 `예측 → 실행 → 관찰 → 해석 → 변형 → 적용` 순서를 따른다. 정답을 외우는 대신, 관찰한 근거를
이용해 시스템 내부의 관계를 복원하는 것이 목표다.

후반부로 갈수록 안내를 줄인다. Unit 2에서는 어떤 필드를 볼지 자세히 알려 주지만, Unit 9에서는 learner가 스스로 확인할
boundary와 evidence를 선택해야 한다.
