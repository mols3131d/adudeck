# Unit 0 · Intro

Checkout이 느려졌다고 하자. 전체 소요 시간만으로는 cart validation이 오래 걸렸는지, payment가 오래 걸렸는지
구분하기 어렵다. 각 operation의 시작과 끝을 관찰하고, 같은 checkout에 속한 operation을 연결해야 원인을 좁힐 수 있다.
이 deck은 그 evidence를 어떻게 만들고 읽는지부터 시작한다.

## 무엇을 배우는가

실행 중인 system이 자신의 동작을 설명하기 위해 내보내는 data를 telemetry라고 부른다.
이번 deck에서는 먼저 한 operation의 실행을 기록하는 span과, 관련 span을 연결하는 trace를 다룬다.
이후에는 반복 실행에서 횟수나 분포 같은 상태를 관찰하는 metrics를 다룬다.

예를 들어 checkout 한 번에서 validation과 payment가 실행됐다면, trace를 통해 그 operation 사이의 관계를 조사할 수 있다.
여러 checkout의 소요 시간 분포를 보고 싶다면 개별 trace만 읽기보다 metric으로 관찰하는 편이 질문에 맞는다.
둘은 같은 system을 보더라도 답하려는 질문과 data의 형태가 다르다.

OpenTelemetry는 이런 telemetry를 만들고 수집·전송하는 데 사용하는 API, SDK와 도구를 제공한다.
Data를 생성하는 것, 다른 process로 보내는 것, 저장된 data를 검색하고 화면에서 해석하는 것은 각각 다른 책임이다.
처음에는 console에 출력해 생성된 data를 직접 읽는다. 이후 service와 전송 경계를 추가하면서 어디서 관계가 이어지고
어디서 data가 끊겼는지 관찰한다.

## 학습하는 방식

이 deck에서는 실행 전에 예상되는 관계를 적고, 실행 후 실제 evidence와 대조한다.
명령이 성공했다는 것만으로 telemetry의 의미를 이해했다고 판단하지 않는다.

첫 실습은 다음 세 operation을 다룬다.

```text
checkout
├─ validate_cart
└─ charge_payment
```

세 operation의 이름을 아는 것만으로는 같은 checkout에 속하는지 확정할 수 없다.
First Trace에서 identifier와 parent 관계를 읽고, 호출 하나의 current context를 바꿔 연결이 달라지는지 확인한다.
정확한 identifier 값을 암기하는 대신 관계가 만들어지는 이유를 설명하는 것이 목표다.

## 시작 전 점검

Python 함수와 `with` block을 읽고, terminal에서 program을 실행할 수 있으면 시작할 수 있다.
후속 service 실습에서는 process, environment variable, HTTP request/response의 기본 개념이 필요하다.
Backend 운영 경험은 필요하지 않다.

다음 두 질문에 답해 보자.

1. Checkout 한 번의 내부 operation 관계와 여러 checkout의 소요 시간 분포는 각각 어떤 evidence가 필요한가?
2. Console에 span이 보이는 것만으로 다른 process로의 전송이나 backend 저장까지 확인했다고 할 수 있는가?

점검 기준은 질문에 맞는 data를 구분하고, 관찰한 경계까지만 결론을 내리는 것이다.
이제 [Setup](../01-setup/README.md)에서 첫 실습 환경을 준비한다.
