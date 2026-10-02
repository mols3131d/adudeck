# 5장 · Dataset: Production Failure를 재사용 가능한 Test Case로 바꾸기

Production에서 오류 하나를 발견하고 수정했다. 이것만으로는 학습 loop가 닫히지 않는다.

다음 prompt, model, retriever, parser 변경에서 같은 문제가 다시 생길 수 있기 때문이다.

Dataset의 역할은 production log를 복사하는 것이 아니다.

> **다시 만나고 싶은 중요한 조건을 작고 평가 가능한 test case로 보존한다.**

이 장에서는 trace evidence를 dataset item으로 "승격"하는 판단을 연습한다.

## 학습 목표

- dataset과 raw trace archive의 목적 차이를 설명한다.
- dataset item의 `input`, `expected_output`, `metadata` 책임을 구분한다.
- production trace/observation에서 dataset item으로 provenance를 연결한다.
- expected output을 evaluator가 사용하기 좋은 contract로 설계한다.
- privacy와 재현성을 함께 고려해 최소한의 test input을 만든다.
- dataset version이 experiment 비교의 통제 조건인 이유를 설명한다.

## 1. Dataset은 production 로그의 복사본이 아니다

다음 전략은 데이터가 많지만 학습 가치가 불분명하다.

```text
production trace 100,000개
→ 전부 dataset으로 복사
```

좋은 dataset은 질문을 가진다.

```text
이 변경이 과거의 critical failure를 다시 만들지 않는가?
boundary condition을 여전히 만족하는가?
대표적인 정상 case에서도 품질을 유지하는가?
```

그래서 dataset item은 **선택된 test case**다.

Langfuse Academy도 dataset을 application change를 production에 보내기 전에 같은 입력 집합에서 반복 검증하기 위한
offline loop의 기반으로 설명한다.

## 2. Trace에서 바로 복사하지 말고 먼저 failure를 이해한다

예를 들어 production trace가 다음과 같다고 하자.

```text
question
"상품을 받은 지 10일 됐는데 환불할 수 있나요?"

retrieval
"구매 후 14일 이내 환불 가능"

answer
"환불 기간이 지났습니다."
```

중요한 것은 transcript 문자열 자체가 아니다.

Failure contract를 추출한다.

```text
input fact
days_since_delivery = 10

expected domain property
eligible = true

policy invariant
policy_days = 14

failure mode
refund-eligibility
```

이렇게 바꾸면 다음 이점이 있다.

- customer PII를 불필요하게 복사하지 않는다.
- evaluator가 structured field를 검사할 수 있다.
- wording variation과 domain expectation을 분리한다.
- "왜 이 사례가 있는가?"를 metadata/provenance로 남길 수 있다.

## 3. Dataset item의 세 필드

가장 중요한 구조는 다음이다.

```text
input
= application에 다시 넣을 조건

expected_output
= evaluator가 참고할 expected contract

metadata
= case를 설명하거나 grouping할 context
```

예:

```json
{
  "input": {
    "days_since_delivery": 10
  },
  "expected_output": {
    "eligible": true,
    "policy_days": 14
  },
  "metadata": {
    "failure_mode": "refund-eligibility",
    "source": "production-review"
  }
}
```

`expected_output`은 반드시 정답 문장 전체일 필요가 없다.

LLM wording이 자유로운데 golden answer를 문자 단위로 비교하면 실제 contract보다 훨씬 좁은 test가 될 수 있다.

## 4. Worked example: 최소 reproducible case를 만든다

[`dataset_case.py`](dataset_case.py)의 핵심 함수는 production transcript를 받지 않는다.

```python
case = build_refund_regression_case(
    case_id="refund-day-10",
    days_since_delivery=10,
    source_trace_id="trace-production-1",
    source_observation_id="obs-generation-1",
)
```

생성되는 핵심 payload는 다음과 같다.

```text
input
{"days_since_delivery": 10}

expected_output
{"eligible": true, "policy_days": 14}

metadata
{"failure_mode": "refund-eligibility", ...}

source_trace_id
원래 production execution
```

이 설계가 모든 application에 정답이라는 뜻은 아니다.

핵심 원리는 다음이다.

```text
재현에 필요한 정보는 보존
불필요한 raw production data는 제거
expected behavior는 명시
원본 evidence로 돌아갈 provenance는 유지
```

## 5. Source trace / observation 연결은 "왜 이 case가 존재하는가?"에 답한다

Langfuse의 dataset item은 `source_trace_id`와 `source_observation_id`를 연결할 수 있다.

이 linkage가 있으면 regression case를 보다가 원래 production evidence로 돌아갈 수 있다.

```text
dataset item
→ source trace
→ source observation
→ 당시 retrieval / generation / metadata
```

하지만 provenance link가 있다고 해서 raw sensitive content를 dataset에 복사해도 된다는 뜻은 아니다.

```text
provenance
= 원본 evidence를 추적할 link

dataset input
= 반복 실행에 필요한 최소 test contract
```

둘의 책임을 분리한다.

## 6. Dataset을 한 번 만들고 item을 추가한다

Dataset 자체는 목적이 분명한 이름을 사용한다.

```python
langfuse.create_dataset(
    name="support/refund-policy",
    description="환불 정책 regression cases",
)
```

그 다음 item을 추가한다.

```python
langfuse.create_dataset_item(
    dataset_name="support/refund-policy",
    input={"days_since_delivery": 10},
    expected_output={"eligible": True, "policy_days": 14},
    metadata={
        "source": "production-review",
        "failure_mode": "refund-eligibility",
    },
    source_trace_id="...",
    source_observation_id="...",
)
```

[`dataset_case.py`](dataset_case.py)는 dataset이 이미 준비되어 있다고 가정하고 item promotion만 담당한다. Dataset
lifecycle과 case extraction을 한 함수에 섞지 않아 학습할 state transition을 더 분명하게 한다.

## 7. 실행 전에 예측한다

Live upload 전에 다음을 답한다.

1. 이 case를 다시 실행하는 데 원래 customer 이름이 필요한가?
2. evaluator가 `eligible`을 판정하려면 어떤 expected field가 필요한가?
3. `policy_days`를 input에 둘까, expected output에 둘까? 왜?
4. source trace link가 끊겨도 test 자체는 실행 가능한가?
5. source trace가 삭제되면 provenance와 reproducibility 중 무엇이 남는가?

정답은 application contract에 따라 달라질 수 있다. 중요한 것은 각 필드의 **owner와 목적**을 설명하는 것이다.

## 8. Credential-free contract test

실행:

```bash
python textbook/05-datasets/test_dataset_case.py
```

Test는 다음을 확인한다.

- structured input/expected output이 만들어진다.
- source trace/observation linkage가 payload에 남는다.
- 예제 case가 raw customer transcript를 필요로 하지 않는다.
- upload helper가 `create_dataset_item()` contract로 전달한다.

이 test가 검증하지 않는 것:

- Langfuse server에 item이 실제 저장되는가?
- source trace link가 UI에서 정상 navigation되는가?
- dataset version이 server에서 증가하는가?

그것은 live Langfuse behavior다.

## 9. Live lab

먼저 Langfuse에서 `support/refund-policy` dataset을 한 번 만든다. UI를 사용하거나 SDK로 만들어도 된다.

그 다음 실제로 **학습 가치가 있다고 판단한** trace ID를 사용한다.

```bash
export SOURCE_TRACE_ID="<selected-trace-id>"
export SOURCE_OBSERVATION_ID="<optional-observation-id>"
export LANGFUSE_DATASET="support/refund-policy"

uv run python textbook/05-datasets/dataset_case.py
```

실행 후 확인한다.

```text
dataset item
├─ input
├─ expected output
├─ metadata
└─ source trace / observation link
```

### 관찰 질문

- item만 읽어도 regression intent를 이해할 수 있는가?
- 원본 trace를 열면 왜 이 case가 추가됐는지 더 자세히 알 수 있는가?
- 원본 trace 없이도 task/evaluator를 실행할 수 있는가?
- dataset에 저장하지 않아도 되는 production detail은 무엇인가?

## 10. Dataset version은 비교 조건이다

Dataset이 바뀌면 experiment의 조건도 바뀐다.

현재 Langfuse는 item의 add/update/delete/archive 같은 변경을 dataset version으로 추적한다. Version은 특정 시점의 dataset
상태를 가리키며, SDK에서 특정 version을 가져와 experiment를 실행할 수 있다.

따라서 다음 비교는 confounded되어 있다.

```text
Experiment A
application v1
dataset version X

Experiment B
application v2
dataset version Y
```

결과 차이가 application change 때문인지 test cases change 때문인지 분리하기 어렵다.

더 좋은 비교:

```text
baseline
application v1
dataset version X
evaluator definition E

candidate
application v2
dataset version X
evaluator definition E
```

### 중요한 nuance

Dataset item content versioning과 dataset schema는 같은 개념이 아니다. 현재 Langfuse의 dataset versioning 문서에서는
item change history를 version으로 다루고, schema 자체는 같은 방식으로 versioned snapshot이 되지 않는다고 설명한다.

즉 "같은 dataset version"이라는 말만으로 evaluator/schema contract까지 자동으로 고정된다고 가정하지 않는다.

## 11. 어떤 production case를 넣어야 하는가?

모든 trace를 넣지 않는다. 다음 세 질문을 사용한다.

### 재현 가치

```text
이 failure가 다시 생기면 중요한가?
향후 변경에서 회귀할 가능성이 있는가?
```

### 판정 가능성

```text
expected behavior를 설명할 수 있는가?
evaluator가 관찰할 evidence가 있는가?
```

### 안전한 보존

```text
PII / secret / confidential data를 제거하거나 synthetic form으로 바꿀 수 있는가?
원본을 복사하지 않고도 failure condition을 보존할 수 있는가?
```

처음 dataset은 작아도 된다.

```text
대표 정상 case
+ historical failure
+ 중요한 boundary case
```

Production에서 실제 failure mode를 발견할 때 점진적으로 추가한다.

## 12. 연습: promote / do not promote

다음 production 사건을 dataset item 후보로 분류하고 이유를 적는다.

1. 한 번 발생한 provider timeout
2. 반복적으로 틀리는 환불 기간 질문
3. raw customer email과 전화번호가 포함된 transcript
4. candidate parser가 자주 틀리는 JSON boundary case
5. CPU saturation으로 발생한 infrastructure incident
6. 사용자는 불만족했지만 무엇이 잘못됐는지 아직 모르는 trace

6번은 특히 중요하다. "나쁜 trace"라는 사실만으로 바로 expected output을 만들지 말고, **failure를 이해한 뒤** dataset
contract를 정의해야 한다.

## 다음 장

Dataset은 반복 가능한 문제 집합이다. 다음 장에서는 **같은 cases를 같은 evaluator로 baseline과 candidate에 실행**해
변경의 효과와 regression을 비교한다.

## References

- [Langfuse Academy · Datasets](https://langfuse.com/academy/datasets)
- [Langfuse Datasets](https://langfuse.com/docs/evaluation/experiments/datasets)
- [Dataset Versioning](https://langfuse.com/docs/evaluation/experiments/dataset-versioning)
- [Evaluate with Datasets](https://langfuse.com/docs/evaluation/get-started/offline)
- [Langfuse Python SDK Reference](https://python.reference.langfuse.com/)
