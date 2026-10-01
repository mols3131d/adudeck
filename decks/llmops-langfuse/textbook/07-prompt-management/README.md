# 7장 · Prompt를 Versioned Artifact로 다루기

Prompt가 application code에 hard-code되어 있으면 문장 하나를 바꾸는 것도 code deploy와 묶인다.
Langfuse Prompt Management는 prompt를 versioning하고 label로 선택해 runtime에서 가져오는 기능을 제공한다.

하지만 prompt ownership을 어디에 둘지는 project policy의 문제다.
이 장에서는 Langfuse 기능을 이해하되 “모든 prompt를 무조건 UI로 옮겨야 한다”고 가르치지 않는다.

## 학습 목표

- prompt version과 label을 구분한다.
- `production`, `latest`, custom label의 의미 차이를 설명한다.
- prompt variable을 compile하는 흐름을 설명한다.
- 실행 generation과 실제 사용한 prompt version을 연결하는 이유를 설명한다.
- prompt management가 application correctness contract를 대신하지 않는다는 점을 설명한다.

## 1. Prompt의 세 단계

```text
stored prompt template
      ↓ fetch
prompt version object
      ↓ compile variables
runtime prompt/messages
      ↓
LLM generation
```

이 셋을 같은 것으로 생각하면 debugging이 어려워진다.

## 2. Prompt 가져오기

```python
from langfuse import get_client

langfuse = get_client()

prompt = langfuse.get_prompt("support/refund-answer")
compiled = prompt.compile(policy_days=14, question="환불 기간은?")
```

Langfuse prompt variable syntax는 `{{variable}}` 형식을 사용한다.

예:

```text
정책상 환불 기간은 {{policy_days}}일입니다.
질문: {{question}}
```

Compile 이후 실제 runtime string/message가 만들어진다.

## 3. Version과 Label

Prompt를 수정하면 version이 생긴다.
Label은 특정 version을 의미 있는 이름으로 가리킨다.

```text
version 12  ← staging
version 13  ← production
version 14  ← latest
```

`latest`와 `production`은 같은 뜻이 아니다.
가장 최근에 만든 version이 production으로 승인됐다는 보장은 없다.

현재 기본 fetch는 production label이 붙은 version을 사용한다.
명시적으로 version이나 label을 선택할 수도 있다.

```python
production_prompt = langfuse.get_prompt("support/refund-answer")
staging_prompt = langfuse.get_prompt("support/refund-answer", label="staging")
version_12 = langfuse.get_prompt("support/refund-answer", version=12)
```

## 4. Prompt version을 실제 generation에 연결한다

Experiment에서 “prompt v21이 더 좋았다”고 말하려면 실제 generation이 어떤 prompt version을 사용했는지 추적할 수 있어야
한다. Prompt를 fetch하고 compile만 해서는 그 관계가 자동으로 명확해지는 것이 아니다. LLM call과 prompt object를
연결한다.

OpenAI Responses API를 사용하는 예:

```python
import os

from langfuse import get_client
from langfuse.openai import OpenAI

langfuse = get_client()
client = OpenAI()

prompt = langfuse.get_prompt(
    "support/refund-answer",
    type="chat",
    label="production",
)

response = client.responses.create(
    model=os.environ["OPENAI_MODEL"],
    input=prompt.compile(
        policy_days=14,
        question="환불 기간은?",
    ),
    langfuse_prompt=prompt,
)

print(response.output_text)
```

여기서 서로 다른 세 값이 연결된다.

```text
prompt.name
+ prompt.version
        ↓
compiled runtime messages
        ↓
actual generation observation
```

그 결과 output을 조사할 때 “이 응답을 만든 prompt version은 무엇이었나?”를 trace에서 따라갈 수 있다.

직접 generation observation을 만들 때는 observation의 `prompt=` argument로 연결할 수 있고, 여러 자동 계측 generation에
같은 prompt를 전파해야 한다면 Python SDK 4.14+의 `propagate_attributes(prompt=prompt)`를 사용할 수 있다.

```python
from langfuse import propagate_attributes

with propagate_attributes(prompt=prompt):
    # 이 context에서 자동 계측으로 생기는 generation에
    # 같은 prompt version linkage를 전파할 수 있다.
    call_model()
```

Explicit `prompt` linkage와 context propagation은 같은 목적을 다른 instrumentation surface에서 해결한다.

## 5. Cache와 failure boundary

Prompt fetching을 runtime critical path로 만들 때는 external dependency가 하나 늘어난다. Langfuse SDK는 prompt
cache/fallback 기능을 제공하지만 application이 어떤 stale/fallback behavior를 허용할지는 별도로 결정해야 한다.

중요한 질문:

- Langfuse가 잠시 unavailable이면 application은 실패해야 하는가?
- cached production prompt를 계속 사용해도 되는가?
- 첫 fetch부터 실패했을 때 explicit fallback을 허용할 것인가?
- 특정 version pin이 필요한 batch experiment인가?

기술 기능이 business policy를 자동으로 결정하지 않는다.

## 6. Git과 Langfuse의 ownership

가능한 policy는 여러 개다.

```text
A. Langfuse가 prompt source of truth
B. Git이 source of truth, Langfuse는 runtime distribution/trace link
C. prompt 종류에 따라 owner 분리
```

이 deck은 하나를 universal best practice라고 선언하지 않는다.
중요한 것은 **두 곳을 동시에 canonical owner로 만들어 drift시키지 않는 것**이다.

## 7. Experiment와 연결

Prompt Management의 진짜 학습 가치는 UI에서 문장을 편집하는 데 있지 않다.

```text
same dataset
├─ prompt version A
└─ prompt version B
      ↓
same evaluators
      ↓
experiment comparison
```

이렇게 실행과 evaluation에 연결되어야 prompt versioning이 engineering evidence가 된다.

## 연습

다음 상황을 설계한다.

- production은 prompt version 20을 사용한다.
- 새 version 21을 만들었다.
- 전체 user에게 바로 deploy하고 싶지 않다.
- historical refund dataset에서 먼저 검증하고 싶다.

어떤 label/version을 fetch하고 어떤 experiment metadata를 남길지 설명한다.
또 experiment trace에서 실제 prompt version linkage를 어떤 evidence로 확인할지도 정한다.

## 다음 장

마지막 장에서는 지금까지 배운 trace, score, dataset, experiment, prompt를 하나의 개선 loop로 연결한다.

## References

- [Prompt Management Overview](https://langfuse.com/docs/prompt-management/overview)
- [Prompt Management Get Started](https://langfuse.com/docs/prompt-management/get-started)
- [Prompt Version Control](https://langfuse.com/docs/prompt-management/features/prompt-version-control)
- [Link Prompts to Traces](https://langfuse.com/docs/prompt-management/features/link-to-traces)
