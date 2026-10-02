# 7장 · Prompt Management: Prompt Version을 실행 Evidence와 연결하기

Prompt는 단순 문자열이 아니다.

Production behavior를 바꿀 수 있는 **application artifact**다. 따라서 "현재 코드가 어떤 prompt를 사용했는가?"뿐 아니라
다음 질문에 답할 수 있어야 한다.

```text
어떤 prompt version을 사용했는가?
그 version은 어떤 label로 선택됐는가?
실제로 model에 전달된 compiled prompt는 무엇인가?
그 version에서 품질/latency/cost가 어떻게 달라졌는가?
```

이 장의 핵심은 prompt를 UI로 옮기는 것이 아니다.

> **Prompt identity → compiled runtime input → generation → evaluation evidence를 연결한다.**

## 학습 목표

- prompt template, prompt version object, compiled runtime prompt를 구분한다.
- immutable version과 mutable label pointer의 관계를 설명한다.
- `production`, `latest`, custom label을 구분한다.
- missing label이 production/latest로 조용히 fallback되지 않는 이유를 설명한다.
- 실제 사용한 prompt object를 generation에 연결한다.
- client-side cache/fallback의 availability semantics를 설명한다.
- Git과 Langfuse 중 prompt ownership을 명시적으로 정해야 하는 이유를 설명한다.

## 1. Prompt의 세 상태

다음 세 값을 같은 것으로 생각하지 않는다.

```text
stored template
      ↓ fetch
prompt version object
      ↓ compile variables
runtime messages/string
      ↓
model call
```

예를 들어 저장된 template이:

```text
정책상 환불 기간은 {{policy_days}}일입니다.
질문: {{question}}
```

라면 fetch한 prompt object는 다음 identity를 가질 수 있다.

```text
name = support/refund-answer
version = 21
labels = ["staging"]
```

그리고 compile 결과는 실제 provider input이다.

```text
"정책상 환불 기간은 14일입니다.
 질문: 환불 기간은?"
```

Debugging에서는 **어느 단계의 값을 보고 있는가**가 중요하다.

## 2. Version과 label은 서로 다른 문제를 푼다

현재 Langfuse Prompt Management에서 prompt update는 새 immutable version을 만든다.

```text
version 20
version 21
version 22
```

Label은 version을 가리키는 pointer다.

```text
version 20  ← production
version 21  ← staging
version 22  ← latest
```

중요한 invariant:

```text
latest
= 가장 최근에 생성된 version

production
= production label이 가리키는 version
```

둘은 같은 뜻이 아니다.

새 version을 만들었다고 production으로 승인됐다는 뜻은 아니다.

## 3. Default fetch와 explicit fetch

기본 fetch:

```python
prompt = langfuse.get_prompt("support/refund-answer")
```

현재 Langfuse는 label/version을 지정하지 않으면 `production` label을 사용한다.

Explicit label:

```python
prompt = langfuse.get_prompt(
    "support/refund-answer",
    label="staging",
)
```

Explicit version:

```python
prompt = langfuse.get_prompt(
    "support/refund-answer",
    version=21,
)
```

### 중요한 failure semantic

요청한 label이 존재하지 않으면 Langfuse는 `production`이나 `latest`로 조용히 fallback하지 않는다. Missing label은
실패한다.

이 동작은 production safety에 중요하다.

```text
"staging"을 요청했는데 없음
→ production을 몰래 사용
```

한다면 experiment가 실제로 어떤 prompt를 검증했는지 잃어버리기 때문이다.

## 4. Prompt를 fetch하는 것만으로는 generation linkage가 완성되지 않는다

다음 코드만으로는 application이 prompt를 가져와 compile했다는 것은 알 수 있다.

```python
prompt = langfuse.get_prompt(...)
compiled = prompt.compile(...)
```

하지만 evaluation 관점의 질문은 더 구체적이다.

> **이 generation이 정확히 어느 prompt version으로 만들어졌는가?**

Prompt object를 generation과 연결해야 한다.

Langfuse의 direct generation API에서는 `prompt=`를 사용해 연결하는 것이 권장된다. OpenAI integration에서는 wrapper가
`langfuse_prompt=` argument를 지원한다.

## 5. Worked example: compiled input과 prompt identity를 함께 전달한다

[`prompt_versioning.py`](prompt_versioning.py)는 다음 패턴을 사용한다.

```python
compiled = prompt.compile(
    policy_days=14,
    question="환불 기간은?",
)

response = openai_client.responses.create(
    name="answer-generation",
    model=model,
    input=compiled,
    langfuse_prompt=prompt,
)
```

서로 다른 두 정보가 함께 이동한다.

```text
compiled
→ provider가 실제로 받는 input

langfuse_prompt
→ 그 input을 만든 Langfuse prompt version identity
```

그 결과 generation을 조사할 때 다음 chain을 만들 수 있다.

```text
prompt name/version
→ compiled runtime messages
→ generation
→ output
→ score
```

이 chain이 prompt experiment의 핵심 evidence다.

## 6. 실행 전에 예측한다

Live lab 전에 적는다.

1. `staging` label이 version 21을 가리키면 stdout에 어떤 version이 나와야 하는가?
2. `latest`가 version 22여도 `production`이 version 20을 가리킬 수 있는가?
3. `staging` label이 존재하지 않으면 어떤 behavior가 안전한가?
4. prompt version은 같지만 variable `question`이 다르면 generation input은 같은가?
5. compiled input만 기록하고 prompt version link를 남기지 않으면 어떤 debugging 정보가 사라지는가?

## 7. Credential-free contract test

실행:

```bash
python textbook/07-prompt-management/test_prompt_versioning.py
```

Fake prompt는:

```text
name = support/refund-answer
version = 21
labels = staging
```

을 가진다.

Test는 다음을 검증한다.

```text
prompt.compile()
→ runtime messages

responses.create()
→ compiled input 전달
→ 동일한 prompt object를 langfuse_prompt로 전달

returned evidence
→ prompt name/version/label 보존
```

이 test는 remote prompt fetch나 Langfuse UI linkage를 증명하지 않는다. 그 부분은 live lab에서 관찰한다.

## 8. Live lab

필요한 credential과 model을 설정한 뒤:

```bash
uv run python textbook/07-prompt-management/prompt_versioning.py --label staging
```

stdout:

```text
answer=...
prompt_name=support/refund-answer
prompt_version=...
prompt_labels=(...)
```

Langfuse UI에서 generation을 열고 실제 linked prompt version을 확인한다.

### Triangulation

```text
surface A: stdout
prompt version

surface B: prompt page
label → version mapping

surface C: generation observation
linked prompt version
compiled input/output
```

세 surface가 같은 prompt execution을 설명해야 한다.

## 9. Prompt cache는 "network를 완전히 없애는 기능"이 아니다

Langfuse Python SDK는 prompt를 client-side cache한다.

현재 caching model의 핵심은 다음이다.

```text
fresh cache
→ 즉시 반환

TTL이 지난 stale cache
→ stale 값을 즉시 반환하고 background revalidation

cache가 비어 있음
→ API fetch 필요
```

Default cache TTL은 현재 SDK에서 60초다.

여기서 중요한 availability question은 **첫 fetch**다.

Cache가 비어 있고 Langfuse API에 접근할 수 없다면, application은 별도 fallback policy가 없다면 prompt를 얻을 수 없다.
SDK는 explicit fallback prompt를 제공하는 방식도 지원한다.

따라서 다음 문장은 너무 단순하다.

```text
"cache가 있으니 Langfuse 장애는 절대 application에 영향이 없다"
```

대신 application policy를 명시한다.

```text
startup prefetch를 할 것인가?
stale prompt를 얼마나 허용할 것인가?
empty-cache failure 때 fallback을 허용할 것인가?
batch experiment는 version을 pin할 것인가?
```

## 10. Cache와 experiment reproducibility는 다른 목표다

Production에서는 label + cache가 좋은 availability trade-off일 수 있다.

하지만 offline experiment는 재현성이 더 중요할 수 있다.

```text
production
label="production"

experiment
version=21
```

같은 방식으로 explicit version을 pin하면 "experiment를 실행하는 중 label pointer가 바뀌었다" 같은 ambiguity를 줄일 수
있다.

어떤 선택이 맞는지는 workload에 따라 다르다.

## 11. Prompt ownership을 분명히 한다

가능한 policy는 여러 개다.

```text
A. Langfuse가 prompt source of truth
B. Git이 source of truth, Langfuse는 distribution / tracing surface
C. prompt 종류별로 owner를 명시적으로 분리
```

문제는 선택 자체보다 **두 곳을 동시에 canonical owner라고 부르는 것**이다.

```text
Git version A
Langfuse version B
둘 다 "정답"
```

이면 incident/debugging에서 어떤 artifact를 복원해야 하는지 모호해진다.

이 deck은 universal ownership policy를 강제하지 않는다. 대신 owner가 명시되어 있어야 한다고 가르친다.

## 12. Prompt version을 experiment condition으로 만든다

이제 6장의 comparison contract에 prompt identity를 넣을 수 있다.

```text
same dataset version
same model
same retrieval
same evaluator

baseline
prompt version 20

candidate
prompt version 21
```

Experiment metadata에는 최소한 실제 version identity를 남긴다.

그 다음 결과를 읽는다.

```text
aggregate score
→ changed items
→ item trace
→ generation
→ linked prompt version
```

"prompt v21이 좋아졌다"는 주장은 이 evidence chain이 있을 때 훨씬 강해진다.

## 13. `propagate_attributes(prompt=...)`는 언제 유용한가?

여러 자동 계측 generation에 같은 prompt context를 전달해야 할 때 Python SDK의 `propagate_attributes(prompt=prompt)`를
사용할 수 있다.

```python
from langfuse import propagate_attributes

with propagate_attributes(prompt=prompt):
    call_instrumented_components()
```

하지만 특정 generation에 정확히 연결할 수 있다면 explicit linkage가 더 좁고 읽기 쉽다.

```text
specific generation
→ direct prompt linkage

넓은 current context 아래 여러 auto-instrumented generation
→ propagated prompt context
```

Context propagation은 편의 기능이지 ownership을 모호하게 만들라는 의미가 아니다.

## 14. 연습: staging → experiment → production

상황:

```text
production label → version 20
staging label    → version 21
latest label     → version 22
```

요구사항:

- version 21만 historical refund dataset으로 검증한다.
- version 22는 아직 실험 대상이 아니다.
- production traffic은 version 20을 계속 사용한다.
- experiment trace에서 실제 prompt version을 확인할 수 있어야 한다.

설계한다.

1. 어떤 label/version으로 fetch할 것인가?
2. 왜 `latest`를 쓰지 않는가?
3. experiment metadata에 무엇을 남길 것인가?
4. generation linkage를 어떻게 확인할 것인가?
5. version 21이 통과하면 어떤 pointer를 이동할 것인가?
6. 문제가 생기면 rollback은 무엇을 바꾸는가?

## 다음 장

마지막 장에서는 trace, score, dataset, experiment, prompt version을 하나의 **evidence-preserving improvement loop**로
묶는다. 최종 목표는 dashboard 사용법이 아니라 release decision을 설명할 수 있는 engineering chain을 만드는 것이다.

## References

- [Prompt Management Overview](https://langfuse.com/docs/prompt-management/overview)
- [Prompt Management Concepts](https://langfuse.com/docs/prompt-management/data-model)
- [Prompt Version Control](https://langfuse.com/docs/prompt-management/features/prompt-version-control)
- [Prompt Caching](https://langfuse.com/docs/prompt-management/features/caching)
- [Link Prompts to Traces](https://langfuse.com/docs/prompt-management/features/link-to-traces)
- [Langfuse Python SDK v4.16.0 source](https://github.com/langfuse/langfuse-python/tree/v4.16.0)
