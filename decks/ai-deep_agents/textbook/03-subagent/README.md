# 교본 03 — Subagent에게 위임하면 무엇이 이동하는가?

앞선 단위에서 thread 상태와 공유 store를 분리했다. 이번에는 같은 대화 안에서
**상위 agent(supervisor)**가 **자식 agent(subagent)**에게 일을 맡길 때 어떤 정보가 넘어가는지 살펴본다.
여기서 위임은 Python 함수 호출을 복잡하게 포장한 말이 아니다. supervisor의 모델이 `task`를
요청하면 runtime이 자식 agent loop를 별도로 실행하고 그 **결과**를 supervisor에게 돌려준다.

## 위임의 필요와 비용

특정 조사 작업이 수십 개의 자료를 조회한다고 하자. 하나의 agent가 모든 자료와 중간 메시지를
계속 가지고 있으면 supervisor의 context가 불어나고 중요한 판단에 필요한 정보가 묻힐 수 있다.
자식 agent는 조회와 정리를 담당하고, 상위 agent는 필요한 **최종 요약만** 돌려받도록 나눈다.

이득은 context 격리와 다른 도구·지침의 선택적 부여다. 대가로 별도의 모델 호출, latency,
실패 경계, 평가 비용이 생긴다. 짧고 단순한 한 번의 조회라면 subagent를 쓰지 않는 것이
더 단순할 수 있다.

## Task tool을 중심으로 control flow 읽기

[실습 코드](../../playground/subagent_lab.py)는 실제 `create_deep_agent`에
`subagents=[{"name": "researcher", ...}]`를 넘긴다. 자식에게는 `inspect_fixture`라는
read-only 도구를 부여하고 부모에게는 부여하지 않는다.

1. supervisor는 사용자에게서 “alpha 서비스를 조사하라”는 요청을 받는다.
2. supervisor 모델의 `AIMessage.tool_calls`에 `task(subagent_type="researcher",
   description="...")`가 생긴다. 아직 자식은 실행되지 않았다.
3. runtime의 task tool이 `researcher`를 선택한다. 자식 모델이 자신에게만 등록된
   `inspect_fixture("alpha")`를 요청한다.
4. 자식 runtime은 도구 반환값 `alpha: p95=120ms, errors=1%`을 자식의 메시지에 기록한다.
5. 자식 모델은 짧은 요약을 출력한다. 부모는 `ToolMessage(name="task")`로 그 결과를 받는다.
   기본 격리 모드의 부모 messages에는 자식의 개별 `inspect_fixture` ToolMessage가 복제되지 않는다.

실습에서 tool 실행은 진짜 SDK graph가 수행하지만 모델의 의사결정은 미리 고정했다.
따라서 “subagent가 자발적으로 더 좋은 답을 찾았다”는 결론을 내릴 수 없다.

## 위임 입력과 결과를 구별하는 이유

`description`은 자식에게 전달되는 작업 설명이지, 부모의 모든 대화 기록을 자동으로 복사한 것이 아니다.
기본 isolated subagent는 별도의 context에서 시작한다. 자식이 사용할 tool은 `tools`로 제한할 수
있으며, 다른 subagent나 사용자 정의 tool에도 자동으로 같은 권한이 부여되는 것은 아니다.
부모가 가진 전체 정보를 자식이 보아야 한다면 반드시 무엇을 전달할지 설계해야 한다.

이 실습은 **부모에게 노출된 tool 목록**과 **자식에게 노출된 tool 목록**을 별도로 출력하고,
자식이 실행한 `inspect_fixture`의 호출 횟수를 계측한다. 부모의 `parent_tool_messages`에는
`task`만 나타나는지 확인한다.

## 실습: 정상 위임과 잘못된 대상

```bash
uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python decks/ai-deep_agents/playground/subagent_lab.py

uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python -m unittest discover -s decks/ai-deep_agents/playground -p 'test_subagent_lab.py' -v
```

두 시나리오 중 `delegated`는 등록된 `researcher`로 위임한다.
`unknown_subagent`는 의도적으로 존재하지 않는 subagent 이름을 요청한다.
각각의 `parent_offered_tools`, `child_fixture_calls`, `task_result`를 비교한다.

**실행 전 예측:** 이름이 잘못된 경우 자식의 `inspect_fixture`는 몇 번 호출될까?
그 실패는 Python 예외, 오류 ToolMessage, 모델의 오답 중 무엇으로 관찰할 수 있을까?
실행 후 실제 반환된 결과의 문구와 status를 근거로 답한다.

## 수정 문제와 평가

`subagent_lab.py`에서 자식 model의 요약 문장만 "No useful data."로 바꿔 본다.
tool 결과의 내용은 그대로인데 부모의 `task_result`는 어떻게 달라지는가?
이 변화가 자식의 **도구 실행 결과**와 자식의 **모델 응답** 중 어느 것 때문인지 설명하라.

또는 `inspect_fixture`를 자식의 `tools`에서 제거해 보고, 자식이 여전히 tool call을
출력한다면 runtime이 어떻게 반응하는지 추적하라. 항상 원래 코드로 복구하고 테스트를 재실행한다.

학습 완료 기준은 부모·자식의 모델 요청, 도구 실행, 두 context의 격리, supervisor가
수신한 최종 결과를 *서로 다른 단계*로 설명할 수 있는 것이다.
Subagent의 잠재적 비용과 이득을 근거 없이 “항상 더 좋다”로 단순화하지 않는다.

## 참고

- [공식 Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)
- [공식 Context engineering](https://docs.langchain.com/oss/python/deepagents/context-engineering)
