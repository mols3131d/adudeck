# 7장 · Prompt Management: Prompt Version을 실행 Evidence와 연결하기

Prompt는 단순 문자열이 아니다. Production behavior를 바꿀 수 있는 **application artifact**다.

따라서 다음 질문에 답할 수 있어야 한다.

```text
어떤 prompt를 요청했는가?
어떤 immutable version이 실제로 선택됐는가?
그 version은 어떤 label로 선택됐는가?
실제로 provider에 전달된 compiled input은 무엇인가?
그 generation의 score/latency/cost는 무엇이었는가?
```

이 장의 핵심은 prompt를 Langfuse UI에 저장하는 것이 아니다.

> **Prompt selection → immutable version → compiled runtime input → generation → evaluation evidence를 연결한다.**

## 학습 목표

이 장을 마치면 다음을 할 수 있어야 한다.

- stored template, prompt version object, compiled runtime input을 구분한다.
- immutable version과 mutable label pointer를 구분한다.
- `production`, custom label, exact version lookup의 목적을 설명한다.
- missing label이 다른 label/version으로 조용히 바뀌면 reproducibility가 깨지는 이유를 설명한다.
- prompt object와 compiled input을 generation에 함께 연결한다.
- label lookup과 exact-version lookup을 직접 비교한다.
- client-side cache와 local fallback이 availability에는 도움이 되지만 provenance에는 다른 의미를 갖는다는 것을 설명한다.
- prompt source of truth를 application/team이 명시적으로 정해야 하는 이유를 설명한다.

## 1. Prompt의 세 상태

다음 세 값을 같은 것으로 생각하지 않는다.

```text
stored template
      ↓ fetch
prompt version object
      ↓ compile variables
runtime messages/string
      ↓ provider call
generation
```

예를 들어 저장된 chat template이 다음과 같다고 하자.

```text
system: 정책상 환불 기간은 {{policy_days}}일입니다.
user:   {{question}}
```

Fetch 결과는 다음 identity를 가질 수 있다.

```text
name = support/refund-answer
version = 21
labels = ["staging"]
```

그리고:

```python
compiled = prompt.compile(
    policy_days=14,
    question="환불 기간은?",
)
```

를 실행하면 provider가 실제로 받는 runtime messages가 만들어진다.

```text
system: 정책상 환불 기간은 14일입니다.
user:   환불 기간은?
```

Debugging에서는 항상 묻는다.

> 지금 보고 있는 값은 template인가, version identity인가, compiled runtime input인가?

## 2. Version과 label은 서로 다른 문제를 푼다

Prompt 변경은 새 immutable version을 만든다.

```text
version 20
version 21
version 22
```

Label은 version을 가리키는 mutable pointer다.

```text
version 20  ← production
version 21  ← staging
version 22  ← latest version
```

Mental model:

```text
version
= historical identity
= "정확히 무엇을 실행했는가?"

label
= routing pointer
= "현재 이 이름으로 어느 version을 선택할 것인가?"
```

따라서 다음은 동시에 참일 수 있다.

```text
latest version = 22
production label = 20
staging label = 21
```

새 version이 생겼다는 사실은 production 승인을 의미하지 않는다.

## 3. 먼저 lab state를 안전하게 만든다

외부 project state가 우연히 준비되어 있다고 가정하지 않는다.

[`prompt_versioning.py`](prompt_versioning.py)는 synthetic lab prompt를 bounded하게 bootstrap할 수 있다.

Live lab에 필요한 credential/model을 설정한다.

```bash
export LANGFUSE_PUBLIC_KEY="..."
export LANGFUSE_SECRET_KEY="..."
export OPENAI_API_KEY="..."
export OPENAI_MODEL="<사용할 model>"
```

Secret은 repository에 기록하지 않는다.

그 다음 처음 한 번:

```bash
cd decks/llmops-langfuse
uv run python textbook/07-prompt-management/prompt_versioning.py \
  --bootstrap \
  --label staging
```

Bootstrap behavior:

```text
staging label이 없음
→ synthetic chat prompt 생성
→ staging label 연결

staging label이 이미 같은 synthetic prompt를 가리킴
→ 기존 prompt 재사용
→ 불필요한 새 version 생성 안 함

staging label이 다른 content를 가리킴
→ 덮어쓰지 않음
→ 실험 중단
```

마지막 경우가 중요한 이유는 학습 script가 기존 project prompt를 조용히 변경하면 안 되기 때문이다.

필요하면 별도 test project나 별도 label을 사용한다.

## 4. Label lookup을 먼저 실행한다

이제 movable pointer를 사용한다.

```bash
uv run python textbook/07-prompt-management/prompt_versioning.py \
  --label staging
```

실행 전에 예측한다.

1. stdout의 `prompt_selection`은 무엇인가?
2. `staging`이 version 21을 가리킨다면 `prompt_version`은 무엇이어야 하는가?
3. provider에 전달되는 input에는 `{{policy_days}}`가 그대로 남아 있을까?
4. generation은 어느 prompt version과 연결되어야 하는가?

출력은 다음 identity를 보여 준다.

```text
prompt_selection=label=staging
prompt_name=support/refund-answer
prompt_version=...
prompt_labels=(...)
answer=...
```

Langfuse generation에서도 linked prompt identity와 compiled input/output을 확인한다.

## 5. Exact version lookup과 비교한다

Label은 움직일 수 있다. Historical experiment를 재현하려면 immutable identity가 더 적절할 수 있다.

예를 들어 label run에서 stdout에:

```text
prompt_version=21
```

을 확인했다면 같은 version을 직접 실행한다.

```bash
uv run python textbook/07-prompt-management/prompt_versioning.py \
  --version 21
```

두 실행을 비교한다.

```text
label-based
--label staging
→ staging pointer가 현재 가리키는 version

version-based
--version 21
→ immutable version 21
```

### Prediction

`staging` label을 나중에 version 22로 이동하면:

```text
--label staging
→ 22

--version 21
→ 계속 21
```

이어야 한다.

이 차이가 production routing과 experiment reproducibility의 차이다.

## 6. Prompt object와 compiled input을 함께 전달한다

핵심 코드는 다음이다.

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

두 정보는 역할이 다르다.

```text
compiled
→ provider가 실제로 처리한 runtime input

langfuse_prompt
→ 그 input을 만든 Langfuse prompt version identity
```

둘이 함께 있어야 다음 evidence chain을 만들 수 있다.

```text
prompt version
→ compiled input
→ generation
→ output
→ score
```

Compiled input만 있으면 "어느 managed version에서 왔는가?"를 잃는다.

Version만 있으면 "어떤 variable 값이 실제 input을 만들었는가?"를 잃는다.

## 7. Missing label은 성공처럼 바꾸지 않는다

다음 실험을 생각한다.

```text
요청: staging
실제 staging label: 없음
```

이때 application이 조용히 `production`을 사용하면 command는 성공할 수 있다.

하지만 experiment 질문은 바뀌었다.

```text
우리가 검증하려던 것
= staging candidate

실제로 검증한 것
= production
```

그래서 이 lab의 label lookup은 missing label을 실패로 유지한다.

실행 성공보다 **selection identity의 정직성**이 중요하다.

## 8. Cache는 version identity와 다른 문제를 푼다

Prompt cache는 remote fetch 비용과 availability를 다룬다.

개념적으로:

```text
fresh cache
→ cached prompt 반환

stale cache
→ SDK policy에 따라 stale value + refresh path

empty cache
→ remote fetch 필요
```

이것은 다음 질문과 다르다.

```text
어떤 version을 사용했는가?
```

Cache가 있어도 label이 어느 version을 가리키는지는 selection semantics의 문제다.

Offline experiment에서 reproducibility가 중요하면 exact version pinning을 고려한다.

## 9. Local fallback은 availability와 provenance의 trade-off다

Langfuse prompt fetch에는 local fallback을 사용하는 패턴도 있다.

Fallback은 remote prompt를 얻지 못해도 application이 계속 실행되게 할 수 있다.

하지만 중요한 차이가 있다.

Langfuse Python SDK는 fallback prompt client를 `is_fallback=True`로 표시하고, prompt name/version tracing context를 만들
때 fallback이면 remote prompt identity를 기록하지 않는다.

따라서:

```text
remote Langfuse prompt object
→ Langfuse prompt name/version provenance를 generation에 연결 가능

local fallback
→ availability를 유지할 수 있음
→ 같은 remote prompt-version provenance는 없음
```

이것은 버그가 아니라 서로 다른 evidence 의미다.

Fallback을 사용했다면 application metadata나 별도 telemetry로 그 사실을 추적할 필요가 있는지 결정한다.

```text
availability success
≠ provenance success
```

## 10. Prompt ownership을 명시한다

가능한 정책은 여러 개다.

```text
A. Langfuse가 prompt source of truth
B. Git이 source of truth, Langfuse는 distribution/tracing surface
C. prompt 종류별 owner를 명시적으로 분리
```

문제는 선택 자체가 아니다.

```text
Git version A
Langfuse version B
둘 다 canonical이라고 주장
```

하면 incident/debugging에서 어느 artifact를 복원해야 하는지 모호해진다.

이 deck은 하나의 universal policy를 강제하지 않는다. 대신 **owner와 synchronization responsibility를 명시하라**고
요구한다.

## 11. Prompt version을 experiment condition으로 만든다

Unit 6의 comparison contract에 prompt identity를 넣는다.

```text
same dataset name + version
same model
same retrieval
same evaluator
same application revision

baseline
prompt version 20

candidate
prompt version 21
```

이제 result를 다음 순서로 조사할 수 있다.

```text
aggregate
→ changed item
→ item trace
→ generation
→ linked prompt version
→ compiled input/output
```

"prompt v21이 좋아졌다"는 말은 이 chain이 있을 때 훨씬 강한 engineering claim이 된다.

## 12. `propagate_attributes(prompt=...)`와 direct linkage

여러 auto-instrumented generation이 같은 prompt context를 공유해야 할 때는 `propagate_attributes(prompt=prompt)` 같은
context propagation이 유용할 수 있다.

반대로 특정 generation 하나에 정확한 prompt object를 연결할 수 있으면 direct linkage가 더 좁고 읽기 쉽다.

```text
specific generation
→ direct prompt linkage

여러 downstream auto-instrumented generations
→ propagated prompt context가 유용할 수 있음
```

편의 기능이 ownership을 모호하게 만들게 두지 않는다.

## 13. Credential-free contract test

실행:

```bash
python textbook/07-prompt-management/test_prompt_versioning.py
```

Test는 다음 contract를 확인한다.

```text
compile result와 prompt object가 generation call에 함께 전달됨
label lookup은 label을 사용
exact-version lookup은 version을 사용
둘을 동시에 지정할 수 없음
bootstrap은 같은 lab prompt를 재사용
missing lab prompt만 생성
다른 existing content는 덮어쓰지 않음
```

검증하지 않는 것:

```text
remote prompt API 성공
Cloud cache behavior
실제 generation prompt link rendering
OpenAI provider call
```

이것들은 live evidence tier다.

## 14. Assessment: staging → experiment → production

상황:

```text
production label → version 20
staging label    → version 21
latest version  → version 22
```

요구사항:

- historical refund dataset snapshot 하나로 version 21을 검증한다.
- version 22는 아직 candidate가 아니다.
- production traffic은 version 20을 계속 사용한다.
- experiment trace에서 실제 prompt version을 확인할 수 있어야 한다.

설계한다.

1. Candidate experiment는 `--label staging`과 `--version 21` 중 무엇을 쓰겠는가? 왜인가?
2. Dataset version은 어떻게 고정할 것인가?
3. Model/retrieval/evaluator 중 무엇을 고정할 것인가?
4. Generation에서 prompt provenance를 어떻게 확인할 것인가?
5. Version 21이 통과하면 어떤 pointer를 이동할 것인가?
6. Rollback은 immutable version을 삭제하는가, label pointer를 바꾸는가?
7. Remote fetch가 실패해 local fallback을 사용했다면 그 run을 같은 provenance quality로 취급할 수 있는가?

## 다음 장

마지막 장에서는 trace, score, dataset version, experiment, prompt version을 하나의 evidence-preserving improvement
loop로 묶고 **release decision**까지 만든다.

## References

- [Prompt Management Overview](https://langfuse.com/docs/prompt-management/overview)
- [Prompt Management Concepts](https://langfuse.com/docs/prompt-management/data-model)
- [Prompt Version Control](https://langfuse.com/docs/prompt-management/features/prompt-version-control)
- [Prompt Caching](https://langfuse.com/docs/prompt-management/features/caching)
- [Link Prompts to Traces](https://langfuse.com/docs/prompt-management/features/link-to-traces)
- [Langfuse Python SDK v4.16.0 source](https://github.com/langfuse/langfuse-python/tree/v4.16.0)
