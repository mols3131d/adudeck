# PR #33 · OpenTelemetry deck 남은 작업

2026-10-01 기준 작업 인계 메모다. Curriculum과 진행 상태의 기준은
[deck README](../../decks/systems-opentelemetry/README.md)이며, 이 문서는 후속 작업을 위한 임시 정리다.

## 현재 상태

- PR: [#33 · feat(opentelemetry): build hands-on learning deck](https://github.com/mols3131d/adudeck/pull/33)
- Branch: `feat/opentelemetry-deck-foundation` → `main`, Draft.
- 구성 변경 revision: `b838ee7bafbb225470005efa7e1e816fdd28f0b1`.
- 이전 calibration 검증 revision: `17efab608a8dfdac668689cfbcfe47d4991cbf78`.
- Unit 2 구현과 로컬 검토 완료: 첫 trace, identifier 관계, parent context 복원, context 변형, transfer 평가.
- `uv.lock` 추가. Python 3.14.6, OpenTelemetry API/SDK 1.45.0으로 실행 검증.
- 정상 실행과 context 변형을 실제 console JSON으로 검사하는 테스트 2개 통과.
- `mise run test` 전체 통과. 해당 revision의 remote CI와 `ci/validated` 통과.
- Python 3.10+ 전체 matrix, 학습자 평가, Collector 전송, backend UI는 검증하지 않았다.
- Intro와 Setup 추가 및 First Trace 이동 뒤 setup 명령, 테스트 2개, 상대 링크와 Markdown 검사를 통과했다.
  구성 revision의 remote CI와 `ci/validated`도 통과했다.
- Unit 3–9은 미구현이다. Deck 전체 완료를 선언하지 않는다.

## 언어 지침 반영

현재 텍스트북 revision: `1f51e175d058dd7a527339b888cdcbf0bbcc2da5`. 세 장의 제목과 설명을 한국어로 정리했다.
처음 등장하는 주요 용어는 영어를 병기하고 API, JSON 필드, 명령과 코드 식별자는 보존했다.
명령 블록·인라인 식별자·기존 링크 대조와 상대 링크·Markdown 검사를 통과했다.
실행 코드와 dependency는 그대로이며 이 문장 수정에 대한 로컬 runtime 검사는 재실행하지 않았다.
해당 언어 수정 revision의 remote CI와 `ci/validated`는 통과했다.

## 구성 변경

사용자 요청에 따라 `00-intro` → `01-setup` → `02-first-trace`로 시작한다.
Intro는 학습 목적과 관찰 관점, Setup은 환경 준비와 실행 확인을 담당한다. 기존 First Trace의 학습 내용은 보존하고
후속 unit은 03–09로 이동한다. 아래 구현 순서는 이 번호 체계를 따른다.

## 다음 착수 범위: Unit 3

Span data와 failure evidence를 다루는 하나의 학습 단위를 구현하고 검토한다.
기존 Unit 2의 작은 local console 환경을 활용하며, 다음 unit의 infrastructure를 먼저 도입하지 않는다.

1. Unit 2의 prerequisite에서 이어지는 학습 목표와 평가 기준을 정한다.
2. attribute, event, status, exception evidence의 역할과 관계를 설명한다.
3. 성공 operation과 통제된 실패 operation을 비교하는 작은 실행 예제를 만든다.
4. 실행 전에 예측하고, 실제 span output에서 실패 evidence와 parent 관계를 관찰하게 한다.
5. 예외 기록과 status 설정의 동작은 사용하는 SDK의 공식 문서와 실제 실행으로 확인한다.
6. 실행 성공만 확인하지 않고 output의 의미를 검사하는 회귀 검증을 추가한다.
7. 새로운 사례를 해석하는 평가와 점검 기준을 추가한다.
8. 교재·실습 품질과 Unit 2 연결을 검토하고, 필요한 보완까지 완료한다.
9. Deck README와 PR 본문에 산출물, 정확한 revision, 검증 범위와 남은 한계를 기록한다.
10. 커밋·푸시하고 해당 revision의 CI를 확인한다.

## 이후 구현 순서

| 순서 | 학습 단위 | 구현 및 검토할 내용 |
| --- | --- | --- |
| 4 | Resource + API/SDK | 발생 주체와 API, SDK, processor, exporter의 책임을 구분하는 설명과 비교 실습 |
| 5 | Instrumentation | manual과 library/zero-code instrumentation의 동작·차이·관찰 범위를 비교하는 실습 |
| 6 | Context propagation | 두 service의 span 연결과 propagation 단절을 비교하는 예제 및 검증 |
| 7 | OTLP + Collector | application → exporter → transport → Collector 경계를 관찰하는 설정과 실행 검증 |
| 8 | Metrics | Counter, UpDownCounter, Histogram의 선택 근거와 실제 관찰을 연결하는 실습 |
| 9 | Diagnosis | application → exporter → transport → Collector → backend에서 원인을 좁히는 진단 실습과 종합 평가 |

각 단위는 설명, worked example, 예측, 실행, 관찰, 해석, 평가까지 포함한다.
작은 increment마다 실제 검증과 검토를 마친 뒤 다음으로 넘어간다. 현재 실행 자료는 보존하고, 필요한 부분만 확장한다.
Curriculum 변경이 필요하면 후보와 근거를 정리하고 baseline에 반영한 뒤 의존 자료를 보완한다.

## 최종 통합 검토와 완료 조건

- [ ] 용어와 mental model이 unit 사이에서 일관적인지 확인한다.
- [ ] Prerequisite와 개념 순서를 점검하고, 설명 전에 사용하는 개념을 보완한다.
- [ ] 각 학습 목표에 충분한 설명·실습·평가가 연결되는지 확인한다.
- [ ] 교재가 독립적인 주 학습 자료로 역할을 하는지 검토한다.
- [ ] 필요한 playground의 실제 실행과 관찰 evidence를 검증한다.
- [ ] Curriculum 변경과 integration finding을 해결한다.
- [ ] 완료 주장에 필요한 검증 한계를 해결하고, 남는 한계는 명시한다.
- [ ] 최종 revision에 맞춰 전체 테스트와 CI 결과를 확인한다.
- [ ] Deck README와 PR 본문을 최종 구현 상태로 갱신한다.

Ready 전환과 merge는 별도 요청에 따라 진행한다. Deck의 완료와 storage state 변경도 별개다.

## 재개 시 확인

이 메모 작성 뒤 branch나 PR이 바뀔 수 있으므로 먼저 현재 상태를 확인한다.

```bash
git status --short --branch
gh pr view 33 --json headRefOid,isDraft,state,body
gh pr checks 33
mise run test:opentelemetry-deck
```

Repository guidance와 deck README를 읽고, 현재 head에서 미완료 범위를 재확인한 뒤 Unit 3부터 진행한다.
