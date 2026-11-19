# 교본 02 — Filesystem, thread state와 공유 memory

이 단위에서는 “agent가 파일에 썼다”라는 말을 세 부분으로 나눈다. **어떤 backend가 파일을
받았는가**, **어떤 상태나 저장소에 기록되는가**, **다음 요청에서 누가 볼 수 있는가**가 서로 다르다.
[1단위](../01-agent-loop/README.md)에서 모델의 tool call과 runtime의 실행을 구별했다면,
이제 도구가 성공했을 때 실제 상태가 어디에 남는지 추적한다.

## 파일 도구는 파일 시스템이 아니다

`create_deep_agent`는 `read_file`, `write_file`, `ls` 등 가상 filesystem 도구를 제공한다.
이 이름만으로 Python 프로세스의 디스크나 프로젝트 디렉터리가 열리는 것은 아니다. 파일 도구는
**backend**에 요청을 전달한다. backend가 저장 위치와 파일 수명을 결정한다.

- `StateBackend`: LangGraph의 `files` state에 저장한다. 동일 thread의 실행에서
  checkpoint로 다시 읽을 수 있지만, 다른 thread에 자동 공유하지 않는다.
- `StoreBackend`: LangGraph store의 namespace에 기록한다. 동일 namespace를 공유하면
  *서로 다른 thread*도 파일을 읽을 수 있다.
- `CompositeBackend`: 경로 prefix에 따라 backend를 라우팅한다.
  예를 들어 `/scratch/`는 `StateBackend`, `/memories/`는 `StoreBackend`로 보낸다.

여기서 thread는 OS thread가 아니라 LangGraph의 **대화 실행 식별자**다.
`thread_id`를 그대로 재사용하면 저장된 graph 상태를 이어받을 수 있다.
다른 thread ID는 독립된 checkpoint 계보를 만든다. 경로가 같아도 저장 공간이 같다는 뜻은 아니다.

## 한 예제로 흐름 추적하기

[실습 코드](../../playground/context_lab.py)는 실제 `StateBackend`, `StoreBackend`,
`CompositeBackend`, `InMemorySaver`, `InMemoryStore`로 세 번의 agent 호출을 수행한다.
모델은 고정된 tool call을 요청하지만 실제 backend의 읽기·쓰기는 SDK가 수행한다.
가상 메모리만 쓰므로 OS 파일은 만들지 않는다.

1. **A의 첫 실행:** `/scratch/local.md`에 "only thread A",
   `/memories/shared.md`에 "shared across threads"를 쓴다.
   첫 파일은 A의 graph state에, 두 번째는 공유 store의 namespace에 들어간다.
2. **새 thread B:** `/memories/shared.md`는 읽히고 `/scratch/local.md`는 찾지 못한다.
   B는 A의 state를 이어받지 않았기 때문이다. **동일한 그래프 인스턴스**를 썼다는 사실도
   A의 thread state를 자동 공유하지는 않는다.
3. **A 재방문:** 동일한 `thread_id`와 `InMemorySaver`로 재개하면
   `/scratch/local.md`가 여전히 읽힌다.

여기서는 in-memory checkpoint와 store를 사용한다. **프로세스가 종료된 뒤 지속성**을
검증한 것이 아니다. 데이터베이스나 durable store를 선택하기 전까지 재실행 후 보관을
약속하면 안 된다.

## 실습: 먼저 예측하고 세 번의 호출을 관찰하라

```bash
uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python decks/ai-deep_agents/playground/context_lab.py

uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python -m unittest discover -s decks/ai-deep_agents/playground -p 'test_context_lab.py' -v
```

다음 세 질문에 실행 전에 답을 적는다. 실행 후 `written`, `thread_a_files`,
`thread_b_files`, `thread_b_reads`, `thread_a_revisit`을 찾아 근거로 표시한다.

1. B가 A의 `/scratch/local.md`를 읽지 못하는 이유는 “파일 경로가 달라서”인가,
   “thread state가 달라서”인가?
2. `/memories/shared.md`는 `InMemoryStore`의 어느 namespace를 쓰는가?
   서로 다른 namespace를 지정하면 무엇이 달라질까?
3. `InMemorySaver`를 제거하거나 thread A의 마지막 조회에 새로운 ID를 넣으면
   어떤 관찰이 달라질지 예측하라. 실제 변경을 했다면 되돌리고 다시 테스트한다.

## 오개념과 고장 경계

**오개념:** “메모리 backend이니 항상 오래 남는다.” — 저장 *범위*와 저장 *내구성*은 별도다.
`StoreBackend`는 cross-thread namespace를 제공하지만 `InMemoryStore`는 이 Python
프로세스가 종료되면 사라진다. 반대로 `StateBackend`는 체크포인터가 있으면 같은 thread에서
여러 번 관찰할 수 있다.

**오개념:** “`read_file`이 호출됐으면 파일을 읽었다.” — 없는 파일도 호출은 발생한다.
그 결과 문자열과 status를 함께 확인해야 성공과 실패를 구별한다.

**보안 경계:** 공유 namespace를 고정하면 의도하지 않은 다른 thread도 해당 메모리를 읽는다.
실서비스에서는 identity 기반 namespace, 접근 통제, 보존·삭제 정책을 별도로 설계해야 한다.

## 숙달 점검

“같은 agent 객체와 같은 파일 경로를 이용하되, A와 B가 서로 다른 데이터를 보게 하는 구성”을
설명하라. 관찰하는 `thread_id`, 경로 prefix, checkpoint, store namespace가 어떤 책임을
지는지 네 요소를 모두 연결해야 정답이다.

이 단위를 통과하면 다음 [subagent 위임](../03-subagent/README.md)에서 왜 부모와 자식의
대화 기록을 분리해야 하는지 이해할 수 있다.

## 참고

- [공식 Backends](https://docs.langchain.com/oss/python/deepagents/backends)
- [공식 Context engineering](https://docs.langchain.com/oss/python/deepagents/context-engineering)
