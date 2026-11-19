# Deep Agents SDK

LangChain 생태계의 **Deep Agents SDK**로 복잡한 작업을 수행하는 agent harness의 동작을 이해하고 검증하는 학습 덱이다.
핵심은 모델의 추론 능력을 높이는 방법이 아니라, agent loop에 filesystem, context 관리, 위임, 선택적 planning을
조합했을 때 **상태·데이터·권한이 어디서 바뀌는지** 추적하는 것이다.

현재는 후속 학습을 준비하는 **backlog**다. 이 README는 학습 계약과 첫 검증 단위를 정한다.
교본과 실행 가능한 playground는 아직 작성하지 않았다.

## 목표와 선행 지식

학습 후에는 다음을 관찰 가능한 근거로 설명할 수 있어야 한다.

- LangChain의 `create_agent`와 `create_deep_agent`의 공통 agent loop 및 추가 harness 책임을 구분한다.
- 도구 호출, planning, 파일 읽기·쓰기, subagent 위임 전후의 입력·상태·결과를 추적한다.
- thread-scoped 상태, checkpoint, cross-thread memory, skill 로딩의 수명과 공유 범위를 구분한다.
- 내장 filesystem 도구와 사용자 정의 도구의 권한 경계를 구분하고 거부·승인·실패 경로를 검증한다.
- 단순 agent로 충분한 문제와 Deep Agents가 유리한 문제를 복잡도·context·위임 비용으로 비교한다.

**선행 지식:** Python 함수·패키지·테스트, LLM tool calling과 agent loop의 기본 실행 흐름.
LangChain agent와 LangGraph state·checkpointer를 알면 도움이 되지만, 둘의 교본을 모두 마쳤다고 가정하지 않는다.

## 현재 SDK 계약과 학습 범위

다음은 2026-11-19 기준 공식 Python 문서와 SDK changelog를 대조한 학습 전제다.
실습 구현 때 사용하는 버전에서 다시 확인한다.

- `create_deep_agent`는 LangChain의 agent 구성 요소와 LangGraph runtime 위에 filesystem·subagent 등 harness 기능을
  조합한다. **도구가 제공된다는 사실과 모델이 그 도구를 실제로 호출한다는 사실은 다르다.**
- 구조화된 task planning(`write_todos`)은 **`deepagents>=0.7`부터 기본 활성화되지 않는다.**
  `TodoListMiddleware`를 명시적으로 추가한 경우를 비교해야 한다.
- 기본 filesystem은 `StateBackend`로, host의 임의 파일 경로를 그대로 노출하는 것이 아니다.
  파일은 thread-scoped state에 속하며 실행 간 지속 여부는 checkpointer 등 저장 설정에 달려 있다.
  cross-thread memory는 별도 지속 backend/store의 책임이다.
- `permissions`의 경로 규칙은 **내장 filesystem 도구**에 적용된다. 첫 일치 규칙을 사용하며
  일치하지 않는 작업은 허용된다. 사용자 정의 도구·MCP 도구나 sandbox의 `execute`까지
  자동으로 보호하지 않는다. 권한 규칙, 도구 노출 제한, backend 격리를 구별해야 한다.
- 사람 승인이 필요한 도구에는 `interrupt_on` 같은 별도 human-in-the-loop 구성을 사용한다.
  중단 후 재개 흐름에는 checkpointer가 필요하다.

Deep Agents Code(`dcode`) CLI, Managed Deep Agents 운영, LangChain 일반 API 전체,
LangGraph runtime 내부 구현과 production infrastructure는 기본 범위에서 제외한다.

## 학습 순서와 검증 지점

| 순서 | 학습 단위와 개념 의존성 | 관찰·설명할 증거 |
| --- | --- | --- |
| 1. Agent loop와 harness | 모델 응답 → tool call → tool result → 다음 응답을 먼저 이해한다 | 동일한 도구를 쓰는 기본 agent와 Deep Agent의 노출 도구·실행 흐름을 비교한다 |
| 2. 선택적 planning | agent 실행과 상태의 차이를 이해한 후 `TodoListMiddleware`를 추가한다 | `write_todos` 도구의 노출 및 호출 여부, 계획 상태와 실제 실행 결과의 차이를 구분한다 |
| 3. Filesystem·context | 도구 반환값과 thread 상태를 이해한 후 backend를 바꾼다 | `StateBackend`의 파일 수명, 큰 결과의 offloading, checkpoint·store의 범위를 추적한다 |
| 4. Subagent 위임 | context 경계를 이해한 후 `task` 위임을 다룬다 | 부모의 요청, 자식의 독립 context·tools, 부모에게 돌아온 결과를 구분한다 |
| 5. Skills·memory | 파일 수명과 위임 경계를 이해한 후 지식 로딩을 다룬다 | skill의 지연 로딩과 memory의 지속·공유·수정 권한을 비교한다 |
| 6. 권한·실패·선택 | 앞 단계의 state/data flow 위에 통제 수단을 얹는다 | 파일 접근 거부, 사용자 승인 중단·재개, tool 실패와 부분 결과를 검증하고 단순 agent와 비교한다 |

각 단위에서 **어떤 기능이 구성만 되어 있는지**, **실제로 호출되었는지**, **결과가 저장·공유되었는지**를
별개로 기록한다. 특히 planning이나 subagent가 반드시 사용된다고 가정하지 않는다.

## 첫 제작 단위: 좁은 조사 agent의 실행 경계

첫 calibration slice는 **도구 하나를 가진 조사·요약 agent**로 제한한다.
질문은 “동일한 입력과 고정된 도구 결과에서 기본 agent와 Deep Agent가 어떤 도구·상태 경계를 노출하는가?”다.

1. **계약 조사(credential 불필요):** 설치 대상 SDK 버전을 결정하고 `create_agent`,
   `create_deep_agent`, `TodoListMiddleware`, `StateBackend`, filesystem 권한 API의 지원 여부와
   기본 구성을 문서·소스에서 확인한다. 그 결과를 구현 전제와 분리해 남긴다.
2. **통제된 입력·도구:** 예를 들어 “두 가상 서비스의 응답 특성을 비교해 요약하라”는 입력과
   `lookup_fixture(service: str)`라는 단일 read-only 도구를 사용한다. 서비스별 응답은
   코드에 적은 짧은 가상 데이터로 고정하며 외부 네트워크 호출이나 실데이터를 사용하지 않는다.
3. **점진 비교:** 같은 모델·입력·도구로 (A) 기본 `create_agent`, (B) 기본 `create_deep_agent`,
   (C) `TodoListMiddleware`를 추가한 Deep Agent를 비교한다. tool schema 노출은 구성 검사로,
   tool 호출·계획 변경은 실제 event/trace로 확인한다.
4. **실패 경계:** `StateBackend`로 host 파일 접근을 피하고, 내장 filesystem 도구의 쓰기 거부를
   작은 음성 사례로 확인한다. 사용자 정의 도구에 동일 규칙이 적용된다고 주장하지 않는다.
5. **해석과 평가:** 어떤 실행에서 tool이나 planning이 호출되지 않으면 그 자체를 관찰로 기록한다.
   모델의 선택을 결정론적인 계약으로 해석하지 않으며, state snapshot과 trace에서만 결론을 낸다.

SDK 객체 생성·도구 노출에 대한 정적 검증과 **실제 LLM 호출 기반 실행 검증**을 구분한다.
실행 검증에는 tool-calling 지원 모델 및 provider credential(또는 동등하게 검증된 대체 모델)이 필요하다.
credential을 repository에 기록하지 않으며, 사용 가능한 환경이 마련되기 전에는 실행 성공을 주장하지 않는다.
첫 단위가 검증되기 전에는 subagent·memory·sandbox 실행으로 범위를 넓히지 않는다.

## 수용 기준과 안전 경계

- 학습 목표마다 위 순서 안에 설명·실습·확인 지점이 있고, 선행 개념을 사용하기 전에 소개한다.
- 기본/추가 middleware의 차이, thread 상태/장기 저장의 차이, 도구 노출/실제 호출의 차이를 구분한다.
- 정상 실행뿐 아니라 권한 거부 또는 도구 실패의 관찰과 해석이 있어야 한다.
- 기본 실습에는 unrestricted host filesystem, 임의 shell 실행, 외부 쓰기 권한을 주지 않는다.
- 인증 정보, 개인 데이터, 외부 자료 원문, 실행 중 생성한 장기 memory를 Git에 저장하지 않는다.
- 버전과 dependency는 첫 실행 코드 작성 시 실제 테스트한 조합으로 결정·기록한다. 이 README만으로는
  실행 가능성이나 전체 덱 완성을 주장하지 않는다.

## 공식 자료

- [Deep Agents Python overview](https://docs.langchain.com/oss/python/deepagents/overview)
- [Quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart)
- [Tools 및 선택적 planning](https://docs.langchain.com/oss/python/deepagents/tools)
- [Backends](https://docs.langchain.com/oss/python/deepagents/backends)
- [Filesystem permissions](https://docs.langchain.com/oss/python/deepagents/permissions)
- [Subagents](https://docs.langchain.com/oss/python/deepagents/subagents)
- [Skills](https://docs.langchain.com/oss/python/deepagents/skills) ·
  [Memory](https://docs.langchain.com/oss/python/deepagents/memory)
- [Human-in-the-loop](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop)
- [Deep Agents SDK source/changelog](https://github.com/langchain-ai/deepagents/tree/main/libs/deepagents)
