# 교본 01 — Agent loop와 Deep Agents harness

이 장의 목표는 **같은 모델 응답과 도구 결과**를 주었을 때 기본 LangChain agent와 Deep Agents가
각각 무엇을 실행하는지 설명하고, 모델이 사용할 수 있는 도구와 실제 호출한 도구를 분리해 관찰하는 것이다.

Python 함수와 LLM의 tool calling을 알고 있다고 가정한다. LangGraph 내부 구현을 알 필요는 없다.

## 왜 agent loop와 harness를 분리해야 할까?

LLM은 다음에 사용할 도구를 요청하는 **메시지**를 만들 수 있지만, 그 도구를 실행하거나 파일을 저장하는
실행 주체는 아니다. 예를 들어 모델이 `lookup_fixture(service="alpha")`를 요청하면 모델이 직접 Python 함수를
실행한 것이 아니다. agent runtime이 그 호출의 인자와 도구 이름을 읽고 도구를 실행한 다음 결과를
`ToolMessage`로 대화에 추가한다. 모델은 그 결과를 다음 턴의 입력으로 받는다.

이 구분이 없는 학습자는 “모델이 알고 있는 파일”과 “runtime에 실제로 기록된 파일”을 같은 것으로 오해하기 쉽다.
Deep Agents는 기존 agent loop를 대체하는 추론 엔진이 아니라, 그 주변에 filesystem 도구, subagent 위임,
context 관리 등 여러 실행 능력을 조합한 **harness**다. SDK 0.7부터 구조화된 planning은 선택적으로 추가한다.

여기서는 다음 세 층을 구별한다.

| 층 | 입력 | 책임 | 결과 |
| --- | --- | --- | --- |
| 모델 | 지금까지의 messages, 제공된 tool schema | 텍스트 또는 tool call 제안 | `AIMessage` |
| agent runtime | AIMessage의 tool call, 등록된 tools | 도구 실행과 결과 전달, loop 제어 | `ToolMessage`, 갱신된 messages |
| harness/middleware | runtime state, model 요청, tool 목록 | 추가 도구 제공, 상태·컨텍스트·권한 처리 | 모델에게 보이는 도구 및 변경된 runtime state |

`create_agent`도 middleware와 checkpoint를 조합할 수 있다. 위 표는 “Deep Agents만 middleware를 사용한다”
라는 뜻이 아니라 **이번 실험에서 선택한 구성의 차이**를 읽는 기준이다.

## 예제: 두 서비스의 지표를 조회하는 한 번의 loop

가상의 `alpha`와 `beta` 서비스가 있다. 실제 서비스나 API는 호출하지 않는다.
`lookup_fixture`는 `alpha`에 `p95=120ms, errors=1%`, `beta`에
`p95=260ms, errors=4%`라는 가상 지표를 반환한다. p95는 관측된 응답 시간의 95번째 백분위수다.
값이 클수록 요청 중 느린 편에 속하는 응답도 오래 걸렸음을 나타낸다.

다음은 고정된 모델 응답이 만들어 내는 예상 실행 순서다.

1. 사용자가 두 서비스를 비교하라고 요청한다. 이때 messages에는 `HumanMessage`가 있다.
2. 모델이 `lookup_fixture("alpha")`와 `lookup_fixture("beta")` 두 건을 `AIMessage.tool_calls`에 담는다.
   아직 어떤 fixture도 조회하지 않았다.
3. runtime이 등록된 함수로 두 호출을 전달한다. 반환 문자열이 각각 `ToolMessage`에 담긴다.
4. 두 ToolMessage가 messages에 추가된 상태에서 모델이 다시 호출되어 최종 `AIMessage`를 낸다.
5. 마지막 AIMessage는 beta의 p95와 오류율이 더 크다는 문장을 담는다. 이 문장은 **scripted 응답**으로
   준비되어 있다. 도구 결과에 대한 모델의 추론 능력을 검증한 것이 아니다.

각 단계에서 “모델 출력”과 “runtime state 변경”은 같지 않다. 도구 요청을 생성한 뒤에도 도구가 실패하면
성공한 측정값을 얻었다고 주장할 수 없다. 도구가 성공했어도 모델의 최종 문장은 별도로 검토해야 한다.

## 실습 설계: A → B → C → 실패 경로

[실습 코드](../../playground/first_loop.py)는 실제 `create_agent` / `create_deep_agent` graph를 실행한다.
다만 `FakeMessagesListChatModel`은 사람이 써 놓은 `AIMessage`들을 순서대로 반환하므로 API key는 필요 없다.
실험을 제어하기 위한 장치이며 일반 모델의 실제 선택이나 품질을 재현하지 않는다.

같은 입력과 fixture, 같은 순서의 scripted 조회 요청을 유지하면서 구성을 다음과 같이 바꾼다.

| 실험 | 변화시키는 설정 | 실행 전에 예측할 것 |
| --- | --- | --- |
| A: `basic` | `create_agent` + `lookup_fixture` | 사용자 정의 도구는 제공되지만 filesystem 도구는 없다 |
| B: `deep` | `create_deep_agent` + `StateBackend()` | 내장 `write_file`, `read_file`, `task` 등이 추가로 보이지만 호출되지 않는다 |
| C: `planned` | B에 `TodoListMiddleware()` 추가 | `write_todos`가 추가되고 scripted 호출 뒤 `todos` state가 갱신된다 |
| D: `denied` | B의 filesystem `write_file` 호출 시도 | deny 규칙으로 파일 기록은 실패하지만 독립적인 `lookup_fixture` 호출은 성공한다 |

C는 A/B와 **모델 응답 시나리오 자체가 다르다**. 따라서 C에서 관찰한 `write_todos` 사용을
“middleware만 추가하니 일반 LLM이 알아서 계획을 세웠다”라는 인과 결론으로 해석하지 않는다.
확인할 수 있는 것은 사용 가능한 도구가 달라졌고 *scripted model의 명시적 요청에 따라*
그 도구가 실행되었다는 사실이다.

D는 B와 동일한 권한 정책을 사용한다. B에서도 모든 built-in filesystem **write**를 거부하지만,
B의 모델은 쓰기를 요청하지 않는다. D의 모델만 `write_file` 호출을 시도해 실패 경로를 노출한다.
이처럼 **도구를 보여 주는 것**, **실행하는 것**, **성공하는 것**은 각각 독립된 사건이다.

## 실제 실행과 관찰

저장소 루트에서 Python 3.14와 uv를 사용한다. 첫 패키지 설치에는 인터넷이 필요하다.
실습 실행 자체는 네트워크 API나 provider credential을 사용하지 않는다.

```bash
uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python decks/ai-deep_agents/playground/first_loop.py

uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python -m unittest discover -s decks/ai-deep_agents/playground -p 'test_first_loop.py' -v
```

네 가지 실행의 출력에서 다음 필드를 찾아 기록한다.

- `timeline`: user → model(tool call) → tool(동일 call ID) → model의 실제 발생 순서를 담는다.
  두 조회의 반환 순서는 실행 환경에 따라 달라질 수 있으므로 `tool_call_id`로 대응시킨다.
- `offered_tools`: 모델의 `bind_tools`에 건네진 도구 이름(실험용 계측). **호출 사실이 아니다.**
- `calls`: `AIMessage.tool_calls`로 기록된 호출. 도구 실행 전의 모델 요청이다.
- `tool_results`: 실제 실행된 도구의 이름·status·반환값. 성공/거부를 여기서 판별한다.
- `state_keys`, `files`, `todos`: 반환된 runtime state의 일부. 파일 목록이 비었다고 해서
  모든 backend나 thread의 파일이 비어 있다고 결론 내리지는 않는다.
- `final_message`: 마지막 assistant 응답. fixture 값을 읽지 않고도 scripted 모델이 쓸 수 있다.

이 도구 목록 계측은 실험 모델의 `bind_tools`를 override한 것으로, 안정적인 Deep Agents 공식
introspection API가 아니다. 버전이 바뀌면 테스트를 다시 검증해야 한다.

기본 `StateBackend`는 host directory를 직접 노출하지 않는다. 본 실습은 전체 디스크를 읽는
`FilesystemBackend`나 명령을 실행하는 sandbox backend를 사용하지 않는다. 쓰기 거부는
`FilesystemPermission(operations=["write"], paths=["/**"], mode="deny")`로 설정한다.
이 규칙은 built-in filesystem 도구에만 적용되며, `lookup_fixture` 같은 사용자 정의 도구에
전파되지 않는다. 사용자 정의 도구의 안전성은 개발자가 별도로 책임져야 한다.

## 예측 → 실행 → 설명

실습을 실행하기 전에 다음 질문에 짧게 답한 후, 출력에서 확인한다.

1. B의 `offered_tools`에 `write_file`이 있는데 `calls`에는 왜 없을 수 있는가?
2. C의 `todos`가 `completed`가 되는 순간은 모델이 계획을 *제안*한 때인가,
   `write_todos`가 실행돼 상태를 갱신한 때인가?
3. D의 파일 쓰기는 거부되었는데 `lookup_fixture`는 성공한다. 같은 permissions 설정이
   있는데도 결과가 다른 이유는 무엇인가?
4. A와 B의 final_message가 같다면, 그것만으로 두 harness의 실행 비용·안전성·필요성을
   같다고 판단할 수 있는가?

### 수정 실험

`first_loop.py`의 `scripted_messages("deep")`에 `read_file` 호출을 추가해 보라.
요청한 가상 경로가 존재하지 않는 상황에서 어떤 `ToolMessage`가 만들어지는가?
파일 읽기 실패와 `write_file`의 접근 거부를 구분해 기록한다.
수정 전 코드를 되돌린 뒤 다시 계약 테스트를 실행하면 초기 상태로 돌아갈 수 있다.

힌트: 도구별 `name`, `args`, `status`, `content` 및 `files`를 함께 확인한다.
함수 호출이 노출되었다고 해서 성공했다고 가정하지 않는다.

### 자기 평가 기준

정답 문장을 암기하는 대신 다음을 모두 설명할 수 있어야 한다.

- messages에 남는 `AIMessage`와 `ToolMessage`의 책임·순서가 무엇인가.
- A/B/C 사이의 **구성 차이**와 scripted 응답 때문에 생긴 **행동 차이**를 구분하는가.
- D에서 접근 제어가 적용되는 정확한 도구 범위를 말하고, custom tool까지 보호된다고 주장하지 않는가.
- 테스트 성공이 모델 추론 품질이나 장기 persistence까지 검증한 것은 아님을 설명하는가.

## 실제 provider 모델로 비교하기 (선택)

지금까지는 scripted model의 의사결정은 고정하고 **실제 SDK runtime**만 검사했다.
실제 tool-calling 모델을 연결하려면 [선택적 실습](../../playground/live_provider.py)을 실행한다.
이 경로는 외부 OpenAI API에 요청을 보내므로 **API 사용료**가 발생할 수 있다.
모델과 계정 접근 권한을 확인하고, `OPENAI_API_KEY`를 개인 환경 변수로 제공한다.

```bash
uv run --no-project --python 3.14 --with 'deepagents==0.7.40'   --with 'langchain-openai>=1,<2'   python decks/ai-deep_agents/playground/live_provider.py   --model gpt-4.1-mini --case basic --run-paid-api
```

`--case basic`부터 실행하고 필요하면 `deep` 또는 `planned`로 바꾼다. 응답의
`requested_tools`는 모델이 요청한 도구, `executed_tools`는 runtime에서 실행한 도구다.
모델이 지시대로 tool을 호출하지 않을 수도 있으며, 이를 실패한 관찰로 그대로 기록한다.
실험은 한 번에 한 variant만 실행해 과금과 비교의 경계를 유지한다. 실행 횟수와 모델
버전이 달라지면 결론의 근거도 달라진다. 본 PR의 CI는 credential 없이 fake 모델을
이 경로에 넣어 그래프 구성까지만 검증한다. **실제 외부 호출 성공은 검증되지 않았다.**

## 여기서 검증하지 않은 것

이 단위는 provider LLM의 tool 선택, prompt injection 저항성, 비용·latency, subagent 내부
context 격리, checkpointer 재개, store 기반 memory를 검증하지 않는다. 그것들은 뒤 단위의
독립적인 관찰·평가 대상이다. 버전은 첫 실습의 SDK를 `deepagents==0.7.40`으로 고정했으며,
transitive dependency 전체의 lockfile을 만들지는 않았다.

## 참고

- [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)
- [Tools](https://docs.langchain.com/oss/python/deepagents/tools)
- [Backends](https://docs.langchain.com/oss/python/deepagents/backends)
- [Filesystem permissions](https://docs.langchain.com/oss/python/deepagents/permissions)
- [Deep Agents changelog](https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/CHANGELOG.md)
