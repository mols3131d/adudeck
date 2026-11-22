# 05. 실제 provider와 연결하기: 옵션 실습과 검증의 경계

지금까지의 네 교본에서는 LangChain `create_agent`가 실제로 실행됐지만 모델 응답은
`GenericFakeChatModel`이 사전에 결정했다. 이는 control flow와 실패 정책을 검증하는
**강한 deterministic 테스트**지만, 실제 LLM이 사용자의 요청에 따라 도구를 선택하는지
검증한 것은 아니다.

이 실습은 같은 구조를 실제 **OpenAI provider**의 `ChatOpenAI`로 바꿔 실행한다. 유료 API
사용 권한이 있어야 하며 외부 호출·비용·비결정성이 발생할 수 있다. 실행은 선택 사항이고,
무키(no-key) 테스트의 완료 여부에 영향을 주지 않는다.

## 1. 무엇이 새로 달라지는가?

- Fake 모델: 미리 적은 `AIMessage(tool_calls=...)`를 순서대로 재생한다.
- 실제 모델: 네트워크 요청을 받아 실행 시점에 tool call 여부·인자·최종 답변을 결정한다.
- 두 방식의 공통 부분: `create_agent`가 등록한 `double` 도구를 호출하고
  `ToolMessage.tool_call_id`로 대응 관계를 확인한다.

따라서 도구 **실행 자체**는 이전과 동일하지만, 도구 **선택**과 답변 생성은 실제 LLM의 판단으로
바뀐다. 성공 여부는 마지막 문장이 `14`인지 하나만 확인하지 않고,
`AIMessage.tool_calls`, `ToolMessage`, 마지막 응답을 함께 검토한다.

## 2. 실행 조건과 비용

이 코드는 `OPENAI_API_KEY`가 없거나 `--execute`를 명시하지 않은 경우 **외부 요청 전에 중단**한다.
계정·워크스페이스·모델은 사용자 환경에서 직접 정해야 한다. API key를 코드, GitHub,
터미널 기록에 저장하지 않는다. 가능한 경우 OS의 보호된 secret store나 일회성 환경에서 주입한다.

Python 3.11+, `uv`, 인터넷, OpenAI API 사용 권한이 필요하다.
선택적 의존성은 [`pyproject.toml`](../../pyproject.toml)의 `live` extra와 [`uv.lock`](../../uv.lock)에
고정되어 있다. 실제 사용 가능한 모델 이름과 가격·지원 기능은 호출 전에 확인한다. 이 교본은 모델을
임의로 선택하지 않는다.

핵심 안전 게이트와 호출 경계는 다음과 같다.

```python
def require_live_permission(*, execute: bool, api_key: str | None) -> None:
    if not execute:
        raise SystemExit("No API call made. Pass --execute after reviewing provider costs.")
    if not api_key or not api_key.strip():
        raise SystemExit("No API call made. Set OPENAI_API_KEY outside the repository.")

agent = create_agent(model=ChatOpenAI(model=model_name), tools=[double], ...)
agent.invoke(..., config={"recursion_limit": 8})
```

```bash
# 먼저 API key를 안전하게 환경 변수로 제공하고, 해당 모델을 실제로 사용할 수 있는지 확인한다.
# YOUR_MODEL은 실제 계정에서 사용할 수 있는 모델 식별자로 바꾼다.
uv run --project decks/ai-langchain --locked --extra live \
  python decks/ai-langchain/playground/05-live-provider/live_agent.py \
  --model YOUR_MODEL --execute
```

이 실행은 provider가 여러 번 model call을 수행할 수 있고 API 사용료가 발생할 수 있다.
코드에서는 `recursion_limit=8`로 runaway loop를 제한하지만, 이 숫자는 "비용 상한"이
아니다. 도구가 호출되지 않거나 결과 ID가 맞지 않으면 `RuntimeError`를 표시한다.
실패해도 모델 호출 비용은 발생할 수 있다.

## 3. 실습에서 얻을 증거

실행 전에 다음 세 가지를 예측한다.

1. `model_tool_requests`와 `tool_results`는 각각 몇 개여야 하는가?
2. 모델이 올바른 최종 문장을 생성했더라도 도구를 한 번도 실행하지 않았다면
   이 실습의 검증 조건을 충족하는가?
3. 네트워크 오류·잘못된 API key·도구 선택 오류는 어느 단계에서 관찰되는가?

실행 후 `requests == results`라는 수치 조건과 **각 요청 ID ↔ 결과 ID의 대응**을
동시에 검사한다. 숫자만 같아도 서로 다른 요청을 바꿔 붙인 결과는 인정하면 안 된다.
또한 구조적으로 연결됐다는 사실이 답변의 사실성을 보장하지는 않는다.

실제 provider가 도구를 선택하지 않으면 이 실습은 실패한다. 이는 반드시 LangChain
구현의 결함이라는 뜻이 아니라 모델의 tool-use 결정과 prompt가 다를 수 있음을 나타낸다.
다른 모델/지시문과 비교한다면 한번에 한 조건만 바꾸고 결과를 기록한다.

## 4. API 없이 실행 가능한 사전 검증

provider를 호출하지 않고 인증 승인 게이트와 결과 ID invariant를 검사한다.

```bash
uv run --project decks/ai-langchain --locked python \
  decks/ai-langchain/playground/05-live-provider/test_live_agent.py
```

이 테스트는 **실제 provider에 연결하지 않는다**. `--execute` 없이 실행했을 때 비용이
발생하지 않도록 구성한 경계와, 도구 요청·결과가 맞지 않으면 실패하는 조건을 검사한다.
반면 `ChatOpenAI` 네트워크 호출은 사용자 측 승인·인증 상태 없이는 성공 여부를 판정할 수 없다.

## 5. 독립 평가

다음 상황을 각각 "모델 선택 실패", "실행 실패", "검증 실패", "환경/권한 실패"로 분류하고
그 분류를 정당화한다: (a) API key 없음, (b) 최종 문장은 맞지만 tool call이 없음,
(c) tool call과 result ID가 다름, (d) tool 결과는 있었지만 잘못된 최종 값,
(e) provider가 timeout을 반환함.

**평가 기준:** fake와 live 실험의 인과적 차이를 설명하고, 실제 모델 결과를 학습용
결정론적 테스트의 성공으로 대체하지 않으며, 외부 호출 권한·비용·실패 조건을 구분한다.

## 공식 근거

- [OpenAI integration reference](https://reference.langchain.com/python/langchain-openai/langchain_openai)
- [Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [Unit testing](https://docs.langchain.com/oss/python/langchain/test/unit-testing)
