# PR #35 · POSIX sh 커리큘럼 보완 조사 보고서

- 조사일: 2026-11-08 (Asia/Seoul)
- 대상: [PR #35](https://github.com/mols3131d/adudeck/pull/35), `feat/posix-sh-deck-foundation` → `main`
- 조사 기준 head: `bc2180889ef068801dc92b12545c65cdf3dc657c` (보고서 추가 전)
- 대상 baseline: [deck README](../../decks/programming-posix_sh/README.md)
- 선행 자료: [2026-10-03 조사](../2026-10-03/posix-sh-textbook-research.md),
  [2026-10-05 심층 리뷰](../2026-10-05/pr-35-deep-review.md)
- 범위: **조사와 최소 curriculum repair 권고**. 기존 교본/README 수정, 실습 작성, 리뷰 스레드 resolve, 병합은 수행하지
  않음.

## 판정

**조사 결과: 네 가지 merge blocker가 여전히 유효하다. 수정 후 짧은 재검증이 필요하며, 현 시점에는 NOT MERGE-READY다.**

1. 11개 observable learning outcome의 개발 위치와 평가 근거가 연결되지 않는다.
2. `case`와 `for`를 exit-status가 분기를 선택하는 구조로 묶은 설명이 POSIX 실행 의미와 다르다.
3. ordinary-word expansion model/Unit 1에 tilde expansion 책임이 없다.
4. scope에서 약속한 arithmetic expansion `$((...))`에 명시적 unit owner가 없다.

이 항목들은 초급 교본의 큰 구조를 바꿀 이유가 아니라 **기존 baseline 내부의 작은 수정**으로 해결할 사안이다. 선행 연구의
POSIX.1-2024와 deployed shell을 구분하는 방침, argv/status/fd/state mental model, 첫 `source → argv` calibration slice는
유지한다.

## 증거와 판단 기준

### Authority 경계

- **언어 의미의 기준**:
  [The Open Group POSIX.1-2024, Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html),
  특히 ``2.6` 및 ``2.9.4`.
- **검색 가능한 동일 개정판 참고 사본**:
  [posix.fail, 2024 Shell Command Language](https://posix.fail/spec/posix/2024/utilities/V3_chap02.html),
  [Utility Conventions](https://posix.fail/spec/posix/2024/basedefs/V1_chap12.html). 이 호스트는 공식 발행처가 아니라
  열람용 mirror다. 공식 URL을 normative authority로 유지한다.
- **교육과정 운영 근거**: repository canonical `.rulesync/skills/adudeck-deck-curriculum/SKILL.md`의 outcome
  development/assessment coverage 및 baseline gate. 교육적 정합성의 보조 자료는
  [UNSW: Aligning Assessment with Outcomes](https://www.teaching.unsw.edu.au/aligning-assessment-learning-outcomes),
  [Monash: Constructive Alignment](https://www.monash.edu/learning-teaching/teachhq/Teaching-practices/learning-outcomes/how-to/constructive-alignment)다.
- **구현 지원 여부**: language 표준과 별개의 증거가 필요하다. 이번 보고서는 특정 `dash`/`ash`/ShellCheck release의 현재
  지원 행렬을 재확정하지 않으며, 구현 테스트를 실시하지 않았다.

### 방법 및 한계

기존 deck README, 심층 리뷰, unresolved thread를 대조하고, 네 가지 쟁점을 POSIX.1-2024의 해당 조항과 대조했다. 이후
scope → concept dependency → unit → assessment 연결을 점검하고 가장 작은 수정안을 도출했다. 교육 평가 예시는
**권고안**이지 이미 작성된 문항이나 통과된 테스트가 아니다. 브랜치 HEAD, CI, 스레드 수치는 보고서 작성 전 GitHub 조회
기준이다.

## 발견 1 — Learning outcome의 평가 추적성 (Blocker)

현재 README의 O1–O11은 관찰 가능한 능력을 기술하지만, 어느 unit에서 학습하고 어디에서 그 능력을 검증할지 연결하지
않는다. `adudeck-deck-curriculum` baseline gate와 부합하지 않는다. 주제 목록만으로 결과 성취를 증명할 수 없다. 교육학의
constructive alignment도 학습 목표·활동·평가를 연결하도록 권고한다.

### 제안: 작고 명시적인 coverage map

`README.md`의 Planned Learning Units 뒤에 아래 정도의 표를 추가한다. O번호는 현재 Learning Outcomes의 순서이며, 각
평가의 구체적인 문항/채점 설계는 textbook authoring 단계에 맡긴다.

| Outcome | Develop | Assess: 관찰 가능한 증거 |
| --- | --- | --- |
| O1 source → exact argv | Unit 1 | quoting·expansion 사례의 `argc/argv` 예측과 결과 추적 |
| O2 quoting/field boundary | Unit 1 | empty·whitespace·glob 입력을 바꾼 뒤 argument 보존 오류 수정 |
| O3 assignment/environment | Unit 2 | ordinary argument vs assignment와 export/temporary env 상태 추적 |
| O4 positional arguments | Unit 2, 4; function transfer는 Unit 5 | `"$@"`, `$#`, `shift`를 사용한 wrapper의 argument-vector 보존 |
| O5 fd/redirection/pipeline | Unit 2 | 순서가 다른 redirection의 fd 0/1/2 연결과 status 추적 |
| O6 current shell/subshell | Unit 2, 4 | pipeline 안의 변수 변경이 유실되는 사례의 원인 설명·수정 |
| O7 control-flow mechanism | Unit 3, 4 | `if`/`while`/`until`의 status, `case`의 pattern, `for`의 item list를 구분한 trace |
| O8 POSIX functions | Unit 5 | positional parameter 복원, shared state, `return` 결과 추적·수정 |
| O9 validation evidence | Unit 6 | `sh -n`/lint/runtime/표준 문서가 증명하는 범위 분류 |
| O10 portability repair | Unit 6, 7 | Bash/platform assumption 제거와 bounded claim + evidence |
| O11 independent synthesis | Unit 7 | input/output/status/state/cleanup 계약 → 구현 → 증거 제시 |

**수용 조건:** 11개 outcome 모두에 최소 하나의 develop/assess 경로가 있고, assess 칸의 행동이 outcome에서 요구하는
능력을 직접 관찰할 수 있어야 한다. 해당 표는 평가문항 대량 생성의 근거가 아니다.

## 발견 2 — `case`/`for`의 선택 입력과 exit status를 혼동 (Blocker)

POSIX.1-2024 Shell Command Language ``2.9.4.2–2.9.4.6`는 다음을 구분한다.

| Construct | 다음 실행 경로를 결정하는 입력 | 실행 결과로서의 status |
| --- | --- | --- |
| `if`, `while`, `until` | 조건 `compound-list`의 exit status | 실행한 body/branch 결과 등에 의해 결정 |
| `&&`, `||`, `!` | command/pipeline status | 마지막으로 실행된 대상 또는 negation에 따라 결정 |
| `case` | 확장된 word와 shell pattern의 비교 | 실행한 clause의 결과. 불일치 시 0 |
| `for` | `in` 뒤 확장된 item list; 없으면 `"$@"` | 마지막 body 결과. item이 없으면 0 |

`case`와 `for`도 status를 **반환**하지만 status로 pattern/item을 **선택**하지는 않는다. 기존 outcome 7은 이 차이를
지우고, Unit 3의 `Decisions Are Exit Status`도 `case`를 같은 이유로 오해하게 한다. 이는 단순한 용어 문제가 아니라
학습자가 잘못된 실행 모델을 갖게 되는 오류다.

### 권고 문안

- **O7**: “`if`, `while`, `until`, `&&`, `||`에서 command exit status가 실행 경로에 미치는 영향, `case`에서 pattern
  matching, `for`에서 item-list iteration을 구분하고 각 construct의 결과 status를 추적한다.”
- **Unit 3**: status-based conditional execution과 `case` pattern selection을 구별해 명시한다. 제목은
  `Decisions and Resulting Status` 등으로 좁힐 수 있다. Unit 1의 pathname pattern과 `case`의 shell pattern은
  **관련되지만 서로 동일한 확장 과정이 아님**을 짧게 선행 설명한다.
- **Unit 4**: `for`의 item-list iteration 책임을 유지한다.
- **O4**: `$?`는 positional argument 보존 도구가 아니므로 O4에서 빼고 O7/Unit 3 status model에서 다룬다.

**검증 예**: 학습자가 “`case`는 string-pattern match로 branch를 결정한다”와 “`for`는 확장된 item list를 순회한다”를 실행
결과 status와 별개의 두 열로 설명할 수 있어야 한다.

## 발견 3 — Tilde expansion의 누락 (Blocker)

POSIX.1-2024
``2.6`의 ordinary word expansion 첫 단계에는 **tilde, parameter, command, arithmetic** 확장이 함께 명시된다. 그 뒤 적용 가능한 field splitting, pathname expansion, quote removal로 이어진다. 현재 README의 반복 model은 tilde를 제외하므로 `~/file`
같은 흔한 사례를 모델로 설명할 수 없다.

권고하는 **입문자용 개념도**:

```text
ordinary source word (quote/context controls applicability)
→ [tilde / parameter / command / arithmetic expansion as applicable]
→ field splitting, where applicable
→ pathname expansion, where applicable
→ quote removal
→ final fields / argv
```

이는 **모든 shell grammar context에서 무조건 실행되는 파이프라인이 아니다**. `case`의 word, assignment, redirection,
special parameter `"$@"` 등은 서로 다른 경계를 갖는다. 특히 POSIX.1-2024 ``2.6`은 특정 unquoted brace 구문에 대해 구현
정의의 추가 expansion 가능성도 열어 놓으므로, 위 그림은 학습을 위한 대표 모델로 기술하고 exhaustive algorithm이라
주장하지 않는다.

### 최소 학습 책임

Unit 1에 unquoted word 시작 위치의 기본 `~`와 `~/path`, quoting이 확장을 막는 경우를 추가한다. `HOME`이 unset일 때의
결과를 보장한다고 쓰지 않는다. assignment의 colon-delimited tilde 등 복잡한 문맥은 Unit 2로 미룬다.

**검증 예**: `~/file`과 `"~/file"`을 비교하고 두 word가 왜 다른 argument가 되는지 설명한다. `HOME`을 명시한 고립된
fixture와 실제 사용자 홈 경로를 구분한다.

## 발견 4 — Arithmetic expansion의 unit owner 부재 (Blocker)

README Learning Scope와 mental model은 `$((expression))`을 포함하지만 Planned Units 어디에서도 이를 가르칠 책임을
지정하지 않았다. POSIX.1-2024 ``2.6.4`에서 arithmetic expansion은 값을 계산해 결과를 대체한다. 특히 Unit 4의
counter/iteration 설명에서 선행 개념 없이 사용될 위험이 있다.

가장 작은 수정은 두 단계 소유권이다.

- **Unit 1**: `$((1 + 2))` 같은 간단한 정수 연산을 word expansion 단계로 인식하고 결과가 argv에 어떻게 전달되는지
  예측한다. 전체 arithmetic grammar를 다룰 필요는 없다.
- **Unit 4**: counter/iteration 등 자연스러운 응용에서 다시 사용하며 선행 Unit 1과 연결한다.

**검증 예**: `printf '%s\n' "$((2 + 3))"`가 전달하는 단일 인자를 예측하고 반복문의 counter update를 설명한다. 비표준
`(( ... ))` command syntax를 portable 기본으로 혼동하지 않는다.

## 인접 발견 — Leading dash pathname과 utility option parsing (주의, 현재 신규 blocker 아님)

기존 review는 “quoting이면 임의 filename을 안전하게 utility에 전달할 수 있다”는 과장에 주목했다. 현재 outcome 2는
argument **boundary 보존** 쪽으로 좁혀져 큰 부분이 해결됐다. 다만 차후 예제는 다음 두 단계를 혼동하지 않아야 한다.

1. Shell은 `"$path"`를 하나의 argument로 보존한다.
2. **받는 utility**는 `-file`을 option으로 해석할 수 있다.

POSIX.1-2024 XBD `12.2 Utility Syntax Guidelines`의 Guideline 10은 `--`를 option 종결자로 권장하지만,
**모든 utility가 모든 guideline을 따르는 것은 아니다**. 따라서 “무조건 `--`를 붙이면 안전하다”도 피한다. 해당 utility의
OPTIONS/OPERANDS 계약을 확인하거나, 현재 디렉터리의 상대 파일명처럼 적절한 상황에서는 `./-file` 형태의 pathname prefix를
사용한다.

**후속 반영 시점**: Unit 4/5의 filename/CLI 실습을 실제 작성할 때. 이 항목을 이유로 먼저 범위를 전역 Unix utility 강의로
넓히지 않는다.

## Issue 8 / 배포 지원성의 추가 경계

POSIX.1-2024
``2.9.4.3`의 `case`는 `;&` terminator도 정의한다. 하지만 이번 초급 curriculum의 교정은 `case`의 **pattern-based selection** 이해에 필요한 수준이므로, 기존 `;;` 중심으로 시작한다. 새 문법을 가르친다는 이유만으로 최초 runnable baseline의 지원성을 가정하지 않는다. 이는 기존 `pipefail`, `$'...'`의
“표준 소속과 deployed feature adoption을 분리한다”는 원칙과 일치한다.

## 현재 GitHub 리뷰 상태와 잔여 작업

보고서 추가 전 조회 기준 PR #35는 `open`, `draft=false`, `mergeable=true`이며, head는 `bc218088...`다. unresolved review
thread는 **6개**다. GitHub의 `outdated`와 semantic resolution은 동일하지 않다.

| 과거 지적 | 내용 기준 disposition |
| --- | --- |
| `pipefail` Bash-only 분류 | 기존 조사/README에서 POSIX.1-2024 + adoption-sensitive로 교정됨. thread는 별도 정리 필요 |
| `case` / `for` status-based decision | **미해결** |
| leading-dash argument/filename | shell argv 보존으로 scope가 좁혀짐; utility option 경계는 후속 실습에서 확인 |
| tilde expansion | **미해결** |
| arithmetic expansion owner | **미해결** |
| outcome → assessment mapping | **미해결** |

최종 head의 `ci/validated` status가 성공했는지도 **수정 후 새 commit에서 재확인**해야 한다. 보고서 전 head의 기존 CI
success는 새 head의 성공을 보장하지 않는다.

## 권고 수정 순서 및 수용 게이트

1. README O4/O7과 Unit 3의 decision input vs resulting status 구분을 고친다.
2. Unit 1에 tilde와 arithmetic expansion 책임을 명시하고 Unit 4 counter 응용으로 연결한다. scope/diagram의 context
   caveat를 유지한다.
3. O1–O11 development/assessment coverage map을 README에 추가한다.
4. 선행 조사 보고서의 `Final Review Disposition`, 새 결과와 모순되는 PR 설명을 최신 상태에 맞게 갱신한다.
5. Review thread 6개의 내용과 실제 patch를 대조해 의미상 닫힌 항목만 resolve한다.
6. 마지막 head에서 repository deterministic validation, `ci/validated`, `main` 통합 상태를 재확인한다.
7. 이후 first calibration slice(ordinary words → final argv)부터 교본/Playground를 **별도 작은 increment**로 구현한다.

**최종 acceptance**: 네 가지 curriculum blocker가 README 본문과 coverage map에서 명시적으로 해소되고, 리뷰 의견의
semantic disposition이 정리되고, final-head CI와 integration 증거가 확보되어야 PR을 merge-ready로 판정한다.

## 재조사 필요 조건

- shell implementation·package version·build configuration에 관한 **실행 가능성 주장**을 새로 하게 될 때
- `;&`, `$'...'`, `pipefail` 같은 adoption-sensitive 기능을 실제 예제의 기본 가정으로 승격할 때
- Unit 2의 과부하 때문에 실제 chapter 경계를 조정하게 될 때(단, 본래 Unit 책임은 유지)
- parser/lint/runtime matrix를 통과했다는 이유로 범용 portability를 단정하려 할 때

## 출처

### 규범 / 기술

- [POSIX.1-2024 Shell Command Language — 공식](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html):
  ``2.6`, ``2.6.1`, ``2.6.4`, ``2.9.3`, ``2.9.4`.
- [POSIX.1-2024 Utility Conventions — 공식](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap12.html):
  `12.2 Guideline 10 및 utility별 예외 경계.
- [동일 개정판 열람용 사본: Shell](https://posix.fail/spec/posix/2024/utilities/V3_chap02.html),
  [Utility](https://posix.fail/spec/posix/2024/basedefs/V1_chap12.html). *Unofficial mirror; 공식 규범의 대체물은 아님.*

### Curriculum / 프로젝트

- [UNSW — Aligning Assessment with Outcomes](https://www.teaching.unsw.edu.au/aligning-assessment-learning-outcomes).
- [Monash — Create constructive alignment](https://www.monash.edu/learning-teaching/teachhq/Teaching-practices/learning-outcomes/how-to/constructive-alignment).
- Repository `.rulesync/skills/adudeck-deck-curriculum/SKILL.md`, `.rulesync/skills/adudeck-textbook/SKILL.md`,
  `docs/VISON.md`, `docs/decks.md`.
- PR #35의 현재 `decks/programming-posix_sh/README.md`, 기존 조사와 심층 리뷰, GitHub review thread.

## 결과물 경계

이 보고서는 공개 표준과 공개 교육 자료를 참조한 **독자적 요약·판단·수정 권고**다. 외부 자료 본문을 복제하지 않았고,
credential·개인 정보·사적 Notion URL을 포함하지 않는다. 본 문서는 curriculum change의 근거이지, 그 변경이 이미
실행되었다는 증거가 아니다.
