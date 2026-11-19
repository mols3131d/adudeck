# 교본 05 — 권한, 승인과 실패 후 재개

앞선 [4단위](../04-skills-memory/README.md)에서는 공유 memory와 읽기 전용 skill을 구분했다.
이제 agent가 **할 수 있는 일**, **시도한 일**, **허용된 일**, **실제로 실행된 일** 사이의
차이를 다룬다. 도구를 아예 제공하지 않는 방법, filesystem 권한 규칙으로 제한하는 방법,
사람의 결정을 요구하는 HITL(human-in-the-loop)은 서로 다른 경계에서 동작한다.

## 1. 도구가 노출됐다는 것은 허가가 아니다

`create_deep_agent`의 filesystem 도구에는 `FilesystemPermission` 규칙을 줄 수 있다.
규칙은 선언 순서대로 검사되어 **첫 번째 일치하는 규칙**이 적용된다.
규칙과 일치하지 않는 경로·작업은 기본적으로 허용된다.

[실습](../../playground/permissions_hitl_lab.py)은 다음 순서로 규칙을 선언한다.

1. `/reports/approved/**` 아래의 write는 `allow`.
2. `/reports/**` 아래의 write는 `deny`.

모델이 `write_file`로 세 경로에 각각 쓰기를 요청한다고 가정해 보자.

| 경로 | 최초 일치 규칙 | 예측 |
| --- | --- | --- |
| `/reports/approved/summary.md` | 좁은 allow | 쓰기 성공 |
| `/reports/private/summary.md` | 넓은 deny | 쓰기 거부 |
| `/scratch/free.md` | 일치 없음 | 기본 허용 |

**deny는 성공한 tool call이 아니다.** 요청은 AIMessage에 남지만 실제 파일 데이터는
쓰기 성공 사례에만 생겨야 한다. 실습의 `responses`는 각 요청의 성공·실패 상태를,
`files`는 가상 backend에 최종 저장된 경로를 보여 준다.

주의할 점은 이 권한이 **내장 filesystem 도구**에 적용된다는 사실이다. 사용자가 직접
구현한 Python 함수나 외부 MCP 도구가 파일을 수정한다면 그 코드는 자체적인 접근 통제가
필요하다. `StateBackend`는 host 파일을 직접 노출하지 않으므로 이 단위의 성공한 쓰기도
Python 프로세스의 임시 graph state에만 기록된다.

## 2. HITL의 상태 전이: 실행 전에 멈춘다

안전성은 파일 경로만의 문제가 아니다. 예를 들어 실제로 사람에게 알림을 보내는 custom tool이
있다면, 실행하기 *전에* 사용자의 승인을 받아야 한다. `interrupt_on`은 특정 tool call을
가로채고 human decision을 요구한다. 승인 없이 실행한 뒤 사과하는 방식과 다르다.

이 단위에서는 외부 알림 대신 Python list에 `"ready"`를 기록하는
`record_local_change` 도구를 사용한다. 실제 효과는 이 일회성 list에만 생긴다.

1. 모델이 `record_local_change("ready")`를 요청한다.
2. runtime의 HITL middleware가 tool 실행 전에 중단한다.
   결과에 `__interrupt__`와 검토할 `action_requests`가 나타난다.
   이때 `effects_at_pause`는 반드시 빈 list여야 한다.
3. 같은 `thread_id`로 `Command(resume={"decisions": [...]})`을 전달한다.
   승인(`approve`)이면 도구가 실행되어 `effects_after_resume=["ready"]`가 된다.
   거부(`reject`)이면 도구를 실행하지 않으므로 list는 여전히 비어 있다.
4. model loop는 도구 결과 또는 거부 통지를 포함한 메시지로 계속 진행한다.

이 재개를 위해 `InMemorySaver` checkpointer를 구성한다. 중단된 실행 상태가 없으면
어느 tool call을 재개할지 판단할 수 없다. **원래 사용한 thread ID**를 재개 시에도
사용해야 한다.

## 실습 — 예측, 승인, 거부, 원인 설명

```bash
uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python decks/ai-deep_agents/playground/permissions_hitl_lab.py

uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python -m unittest discover -s decks/ai-deep_agents/playground -p 'test_permissions_hitl_lab.py' -v
```

출력은 `permissions`, `approved`, `rejected` 세 가지로 나뉜다.
실행 전에 아래를 예상하고, 실행 후 적합한 증거 필드를 지목한다.

- 모델의 `write_file` 요청은 세 건인데 실제 `files`는 몇 개인가? 왜 그런가?
- `effects_at_pause`는 승인/거부 여부와 무관하게 왜 비어 있어야 하는가?
- 승인과 거부 중 어떤 경로에 `record_local_change`의 실제 부작용이 존재하는가?
- `interrupt_on`을 없애면 안전에 어떤 차이가 생길까? `FilesystemPermission`만으로
  이 사용자 정의 도구를 보호할 수 있을까?

### 실패를 설계하는 연습

규칙 둘의 선언 순서를 바꾸면 `/reports/approved/summary.md`의 결과가 어떻게 달라지는가?
실제로 바꾸어 보고 테스트가 실패하는 이유를 **첫 번째 일치 규칙**으로 설명하라.
그 뒤 원래 순서로 되돌린다.

거부된 작업을 “실행 완료”라고 표시하는 UI나 로그가 있다면 어디가 잘못됐는지도
설명하라. `AIMessage.tool_calls`는 실행 *요청*을 의미하므로 완료 기록으로 쓰면 안 된다.

## 종합 평가: 01~05단위 연결

가상의 조사 agent가 서비스를 비교하고 공유 기록을 갱신하기 전 사람의 승인을 받는다고 하자.

1. 비교값 조회는 어떤 단계에서 Python 함수 호출이 되는가? model·runtime을 구분한다.
2. thread에만 남길 scratch 결과와 다른 thread가 읽을 기록을 어디에 보관할까?
3. 자료 조회를 subagent에 맡기면 부모가 보게 되는 것은 어떤 결과인가?
4. 결과 정리 절차는 skill, 이전 사용자의 선호는 memory 중 어디에 둘까?
5. 마지막 기록이 권한 거부/중단/승인/실행 중 어디에 있는지 어떤 state와 message로 판별할까?

완료 기준은 해당 기능명을 나열하는 것이 아니라, **실행 순서와 증거 위치, 접근 제어와
남는 데이터**를 하나의 흐름으로 연결하는 것이다.

## 검증 경계와 보안

실습은 실제 LangChain/Deep Agents runtime을 실행하되, model output은 scripted이다.
승인자는 실제 사람이 아니라 테스트가 제공한 `Command(resume=...)`이며, 신뢰할 수 있는
사용자 인증·권한 위임 UI까지 검증하지 않는다. `InMemorySaver`는 프로세스 종료 후 내구성을
보장하지 않는다. 외부 실행·호스트 파일 수정·개인 정보 전송은 일어나지 않는다.

## 참고

- [공식 Permissions](https://docs.langchain.com/oss/python/deepagents/permissions)
- [공식 Human-in-the-loop](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop)
- [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
