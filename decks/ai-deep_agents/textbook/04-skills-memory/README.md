# 교본 04 — Skills와 memory는 같은 파일이 아니다

앞선 [3단위](../03-subagent/README.md)에서는 자식 agent가 부모의 context를 자동으로 모두
받지 않는다는 점을 확인했다. 이번에는 시스템이 모델에게 건네는 **재사용 정보**를 다룬다.
두 메커니즘 모두 파일로 보관할 수 있지만 목적과 로딩 시점은 다르다.

## Instruction, tool, skill, memory 구별하기

| 구성 | 역할 | 모델에게 언제 보이는가 |
| --- | --- | --- |
| System prompt | 현재 agent의 기본 역할과 행동 지침 | 모델 요청 구성 시 |
| Tool schema | 모델이 호출할 수 있는 기능의 입력 계약 | 도구가 노출된 모델 요청 시 |
| Skill | 특정 작업 절차·전문 지식 및 필요한 자료를 묶은 단위 | 요약·설명이 먼저, 상세 `SKILL.md`는 읽을 때 |
| Memory | 이전 작업에 걸쳐 유지할 사실·선호·맥락 | 설정된 파일을 middleware가 읽고 모델 요청에 포함할 때 |

Skill은 내용을 재사용하는 **절차적 정보**이고 memory는 실행 간 남기려는 **상태성 정보**다.
실제 시스템에서는 경계가 혼합될 수 있지만, 저장 책임과 갱신 권한을 구분하면 오염을 줄일 수 있다.

예를 들어 “p95와 오류율을 함께 비교하라”는 재사용 절차는 skill에 적합하다.
“이번 프로젝트는 오류율을 먼저 논의한다”는 프로젝트 선호는 memory에 적합하다.
두 내용을 매번 모든 모델 요청에 복사하면 context가 비대해진다. Skill은 목록만 먼저 제공하고
필요할 때 전체 문서를 읽는 방법으로 이를 줄인다.

## 모델 요청에서 무엇을 볼 수 있는가?

[실습 코드](../../playground/skills_memory_lab.py)는 SDK의 `SkillsMiddleware`와
`MemoryMiddleware`가 실제로 실행되게 한다. `StoreBackend` 두 개를 서로 다른 namespace에
연결해 **`/skills/`** 와 **`/memories/`** 경로를 나눈다. 파일은 먼저 안전한
`InMemoryStore`에 짧은 가상 데이터로 채워 넣는다.

1. 시작: `/skills/compare/SKILL.md`에는 YAML frontmatter(`name`, `description`)와
   지표 비교 절차가 있고, `/memories/AGENTS.md`에는 우선 논의 순서가 있다.
2. 첫 모델 요청: memory 내용과 skill 이름·설명은 보이지만 skill의 전체 상세 절차는
   아직 모델에게 전달되지 않는다. 실험용 모델의 `prompts[0]`에서 확인한다.
3. 모델이 `read_file("/skills/compare/SKILL.md")`를 요청한다. runtime이 반환한
   `ToolMessage`에 **전체 skill 문서**가 담긴다. 다음 모델 요청의 messages에서 상세 절차가 보인다.
4. 다른 thread가 `write_file("/memories/AGENTS.md")`로 memory를 갱신한다.
   새 thread의 다음 모델 요청에는 변경된 memory가 보인다. 공유 namespace를 사용했기 때문이다.

이 실험에서 모델이 어떤 skill을 “선택”했다는 주장은 하지 않는다. scripted 모델이
`read_file`을 명시적으로 요청했고, SDK가 그 파일을 실제로 불러온 사실을 확인한다.

## 실행과 검증

```bash
uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python decks/ai-deep_agents/playground/skills_memory_lab.py

uv run --no-project --python 3.14 --with 'deepagents==0.7.40' \
  python -m unittest discover -s decks/ai-deep_agents/playground -p 'test_skills_memory_lab.py' -v
```

`model_requests` 항목은 실제 모델 요청의 내용을 실험용 fake model에서 읽은 결과다.
원문 대신 “old memory 포함 여부”, “new memory 포함 여부”, “skill 이름 포함 여부”,
“상세 절차 포함 여부”만 표시한다. **모델 내부 추론**을 관찰한 것은 아니다.

실행 전에 다음을 예상하고 확인한다.

1. 모델이 아직 `read_file`을 호출하지 않았는데도 skill의 설명이 보이는 이유는?
2. 상세 절차가 보이기 시작하는 것은 어느 모델 요청인가? 그 직전에 어떤 ToolMessage가 추가되는가?
3. 다른 thread의 memory 변경이 보이는 조건은 같은 `thread_id`인가, 같은 store namespace인가?
4. `/skills/`의 쓰기 거부 규칙은 memory 변경을 막을까? 경로 prefix와 도구 종류로 설명하라.

## 수정 및 실패 사례

`skills_memory_lab.py`에서 `SKILL_TEXT`의 `description`만 다른 문장으로 바꾸고
첫 모델 요청의 skill 목록을 관찰하라. 상세 본문은 바꾸지 않고도 무엇이 달라지는가?
그 다음 `read_file` 요청을 제거하면 “전체 skill 본문”의 노출에 어떤 변화가 생길까?

**권한 경계:** 여기서는 skill 소스에 `FilesystemPermission(... mode="deny")`로 쓰기를
막고 memory만 갱신한다. 사용자 정의 도구가 skill 내용을 직접 수정하도록 구현된다면 이
filesystem 권한 규칙만으로 그 도구의 쓰기를 막을 수 없다.

**지속성 경계:** `InMemoryStore`에서의 공유는 실험 프로세스 안에서만 성립한다.
이 결과가 외부 저장소의 장애 복구나 다중 서버의 지속성을 증명하지는 않는다.

## 독립 평가

팀 프로젝트의 비교 절차, 구성원별 선호, 단기 조사 결과가 각각 어디에 저장되어야 하는지 설계하라.
정답을 설명할 때 저장 위치뿐 아니라 로딩 시점, 갱신 권한, namespace와 thread 수명까지 연결한다.

## 참고

- [공식 Skills](https://docs.langchain.com/oss/python/deepagents/skills)
- [공식 Memory](https://docs.langchain.com/oss/python/deepagents/memory)
- [공식 Backends](https://docs.langchain.com/oss/python/deepagents/backends)
