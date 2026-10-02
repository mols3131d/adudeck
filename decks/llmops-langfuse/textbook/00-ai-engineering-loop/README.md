# 0장 · Langfuse와 AI Engineering Loop

LLM application을 만들고 응답 하나가 이상하다는 사실을 발견했다고 하자.

```text
질문
→ retrieval
→ prompt 구성
→ model call
→ output validation
→ 최종 응답
```

최종 응답만 보면 “틀렸다”는 것은 알 수 있지만 **어디에서 왜 틀렸는지**는 알기 어렵다.
반대로 trace만 잘 남겼다고 해서 다음 버전이 더 좋아졌는지도 자동으로 알 수 없다.

Langfuse를 배우는 첫 질문은 그래서 “trace를 어떻게 찍지?”가 아니다.

> **관찰한 실행을 어떻게 반복 가능한 개선 근거로 바꿀 것인가?**

## 1. 관찰과 평가를 분리한다

LLM system에는 서로 다른 두 질문이 있다.

```text
관찰 질문
무슨 일이 실행되었는가?

평가 질문
그 실행은 우리가 원하는 기준을 만족했는가?
```

예를 들어 답변이 잘못됐다면 trace는 다음을 보여 줄 수 있다.

- 어떤 input이 들어왔는가
- 어떤 model이 호출됐는가
- 어떤 retrieval 결과를 사용했는가
- 얼마나 오래 걸렸는가
- 어떤 output이 생성됐는가

하지만 “정답은 반드시 `Paris`여야 한다” 같은 domain rule은 application이나 evaluator가 소유한다.
Langfuse는 그 rule의 실행 결과를 **score**로 연결하고 비교하는 역할을 할 수 있다.

## 2. AI Engineering Loop

Langfuse Academy는 AI application 개선을 연속적인 loop로 설명한다.
이 deck에서는 다음과 같이 단순화해서 사용한다.

```text
production execution
      ↓
trace
      ↓
inspect / score
      ↓
failure case 발견
      ↓
dataset
      ↓
experiment
      ↓
change 비교
      ↓
deploy
      └────────→ 다시 production execution
```

각 단계의 data ownership을 구분한다.

| 단계 | 핵심 data | 질문 |
| --- | --- | --- |
| Trace | observations | 실제로 무엇이 실행됐나? |
| Score | evaluation result | 이 실행은 기준을 만족했나? |
| Dataset | reusable cases | 다시 시험할 사례는 무엇인가? |
| Experiment | outputs + scores | 변경 전후가 어떻게 달라졌나? |
| Prompt Management | prompt versions | 어떤 prompt가 실행됐나? |

## 3. Langfuse는 LLM application의 database가 아니다

초급자가 하기 쉬운 오해는 모든 application state를 Langfuse에 넣으려는 것이다.

예를 들어 주문 시스템이라면:

```text
주문 진짜 상태
→ application database

LLM이 주문 문의를 처리한 실행 기록
→ Langfuse trace
```

Langfuse는 observability/evaluation system이다. application의 authoritative business state를 대신하지 않는다.

같은 이유로 다음도 구분한다.

```text
validator code
→ correctness rule의 owner

Langfuse score
→ validator가 낸 결과의 관찰·비교 surface
```

## 4. 왜 trace가 loop의 시작인가

Dataset과 experiment를 먼저 만들 수도 있다. 하지만 실제 application을 개선하려면 무엇이 실패하는지 알아야 한다.
좋은 production trace는 다음 질문을 가능하게 한다.

- 실패가 model 때문인가?
- retrieval 때문인가?
- prompt construction 때문인가?
- tool call 때문인가?
- application validation 때문인가?

그 뒤에야 “이 실패를 다시 발생시키는 test case로 보존할 가치가 있는가?”를 판단할 수 있다.

그래서 이 deck은 trace부터 시작한다.

## 5. Worked example

간단한 support assistant가 있다고 하자.

```text
user: 환불 기간이 며칠이야?

application
├─ search_policy
├─ call_model
└─ validate_answer
```

최종 답이 틀렸다면 단순 로그는 다음처럼 보일 수 있다.

```text
answer=30일
```

구조화된 trace라면 다음처럼 생각할 수 있다.

```text
support-turn
├─ search-policy
│  └─ output: "구매 후 14일 이내..."
├─ answer-generation
│  └─ output: "30일 이내 가능합니다."
└─ validate-answer
   └─ output: failed
```

이제 최소한 문제 위치를 좁힐 수 있다.
retrieval은 올바른 근거를 가져왔지만 generation이 잘못 사용했다.

다음 단계에서는 이 실행을 dataset item으로 보존하고 새 prompt가 같은 실수를 반복하는지 experiment로 확인할 수 있다.

## 6. 생각해 보기

다음 항목을 `application truth`, `observation`, `evaluation evidence` 중 어디에 둘지 분류한다.

1. 결제 transaction의 실제 성공 여부
2. LLM call의 latency
3. 답변이 정책 문서와 일치하는지 계산한 Boolean 결과
4. 사용한 prompt version
5. 사용자의 실제 계정 잔액
6. 특정 request에서 model이 반환한 text

정답을 외우는 것보다 **Langfuse가 무엇을 소유하면 안 되는지** 설명할 수 있어야 한다.

## 다음 장

다음 장에서는 model API 없이 작은 Python 실행을 직접 instrument한다.
먼저 trace와 observation이 실제로 어떤 관계인지 확인한 뒤 LLM integration으로 넘어간다.

## References

- [Langfuse Academy](https://langfuse.com/academy)
- [Academy: Tracing](https://langfuse.com/academy/tracing)
- [Evaluation Overview](https://langfuse.com/docs/evaluation/overview)
