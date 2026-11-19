# Deep Agents

LangChain 생태계의 **Deep Agents SDK**를 활용하여 복잡한 작업에서 계획·파일 기반 context·subagent 위임을 다루는 agent harness를 이해하고 검증하기 위한 학습 덱이다. 일반적인 '깊은 추론' 기법이나 Managed Deep Agents 운영 전체가 아니라 open-source SDK의 동작을 주제로 한다.

현재는 후속 학습을 준비하는 **backlog**다. 교본과 실행 코드는 아직 작성하지 않았다.

## 목표와 선행 지식

학습을 마치면 다음을 할 수 있어야 한다.

- `create_deep_agent`와 기본 `create_agent`의 책임 경계를 설명한다.
- planning, tool 실행, filesystem/context 관리, subagent 위임 시 어떤 정보와 제어권이 이동하는지 추적한다.
- skill·memory·backend 선택이 context와 persistence에 미치는 영향을 비교한다.
- 파일·도구·subagent가 접근할 수 있는 권한과 사람이 승인해야 할 작업의 경계를 설계한다.
- 단순 agent로 충분한 일과 Deep Agents harness가 필요한 일을 근거를 들어 구분하고 실패 사례를 검증한다.

**선행 지식:** Python 함수·패키지·테스트, LLM의 tool calling과 agent loop. LangChain의 agent 개념과 LangGraph의 state·persistence를 먼저 이해하면 유익하다. 둘 모두의 완전한 학습 완료를 필수로 가정하지는 않는다.

## 학습 범위와 순서

| 단계 | 핵심 질문 | 완료 확인 |
| --- | --- | --- |
| 1. Harness 계약 | 모델·agent loop·Deep Agents가 각각 맡는 일은? | 단순 agent와 `create_deep_agent`의 데이터 흐름을 비교한다 |
| 2. Planning과 작업 분해 | 계획은 어떤 상태로 유지되고 갱신되는가? | 단기 작업 계획과 실제 도구 실행을 구별한다 |
| 3. Filesystem과 context | 파일·대화·큰 결과가 어디에 보관되고 다시 읽히는가? | backend와 context 이동의 범위를 설명한다 |
| 4. Subagent 위임 | 위임 시 instruction, tool, context, 결과의 경계는? | 상위 agent와 subagent 사이의 전달 데이터를 추적한다 |
| 5. Skills·memory | 재사용 지침과 장기 상태는 언제 로드·저장되는가? | 일회성 실행과 지속 상태의 차이를 설명한다 |
| 6. 권한·검증 | 어떤 실행은 격리하거나 승인받아야 하는가? | 권한 거부·도구 실패·부분 결과를 시험한다 |

**첫 제작 단위:** 범위가 좁은 조사·요약 agent를 대상으로 단일 도구와 제한된 임시 filesystem에서 실행 흐름을 관찰한다. provider credential을 요구하는 실습은 별도로 분리하고, 도구 응답을 고정해 harness의 데이터·권한 경계를 먼저 확인한다. Planning이나 subagent가 실제로 사용되는지는 관찰한 trace와 결과로 판단한다.

## 완료 기준과 범위 밖

어느 기능이 harness에서 제공되고 어느 기능을 개발자가 설정·보호해야 하는지 설명하며, planning·context·delegation의 정상·실패 경로를 재현할 수 있으면 목표를 충족한다.

LangChain 일반 agent의 API 전반, LangGraph runtime의 세부 구현, Deep Agents Code(`dcode`) CLI 사용법, Managed Deep Agents 및 production infrastructure 운영은 이 덱의 기본 범위가 아니다.

## 작성 시 확인할 사항

- 최신 Deep Agents SDK 문서와 소스의 지원 계약을 대조하고, 기능별 안정성·버전을 확인한 뒤 의존성을 고정한다.
- 기본 실행에 unrestricted host filesystem 또는 임의 명령 실행 권한을 부여하지 않는다.
- credential, 개인 데이터, 외부 자료 원문, 장기 memory를 예제 결과 그대로 Git에 저장하지 않는다.
- 첫 실습이 검증된 뒤 작은 단위로 기능을 확장하며 교본·실습·평가의 경계를 유지한다.

## 공식 자료

- [Deep Agents Python 개요](https://docs.langchain.com/oss/python/deepagents/overview)
- [Deep Agents Quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart)
- [Deep Agents SDK 소스](https://github.com/langchain-ai/deepagents)
