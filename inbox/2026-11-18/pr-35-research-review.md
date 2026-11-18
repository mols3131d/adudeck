# PR #35 · POSIX sh 커리큘럼 조사·수정 검증

- 조사·작성일: 2026-11-18
- 대상: [PR #35](https://github.com/mols3131d/adudeck/pull/35), `feat/posix-sh-deck-foundation` → `main`
- 시작 시점 PR head: `c6c6e7e0835383c29c2ef5a6907b1b18d536a225`; README 수정 commit:
  `f8bccc1fa8ad4a31364fe516c05d15a16a2acd01`
- 커리큘럼: [deck README](../../decks/programming-posix_sh/README.md)
- 선행 근거: [2026-10-03 심층 조사](../2026-10-03/posix-sh-textbook-research.md),
  [2026-10-05 리뷰](../2026-10-05/pr-35-deep-review.md),
  [2026-11-08 쟁점 조사](../2026-11-08/pr-35-curriculum-evidence-report.md)

## 결론

**연구 중심의 curriculum repair를 완료했다.** 네 가지 기존 semantic blocker(학습 성과 ↔ 평가 추적성, `case`/`for` 선택
입력, tilde expansion, arithmetic expansion unit owner)를 `README.md`의 learning contract에 최소 변경으로 반영했다.

이번 작업에서 교본 chapter, playground, runnable acceptance script, repository automation은 생성하지 않았다. 따라서 이는
**커리큘럼의 개념적 정합성 개선**이지 텍스트북 완성이나 실행 portability 증명이 아니다. PR의 최종 merge readiness는
review thread, 최신 HEAD의 CI, 최신 `main`과의 통합 상태가 확인된 뒤 판정해야 한다.

## 조사 범위와 증거 등급

| 증거 층위 | 확인 대상 | 주장할 수 있는 범위 |
| --- | --- | --- |
| 규범 (normative) | POSIX.1-2024 Shell Command Language §§2.6, 2.9.3, 2.9.4, 2.13 | 표준이 정의한 의미와 허용된 불확정성 |
| repository 계약 | `.rulesync/skills/adudeck-deck-curriculum/SKILL.md`, `adudeck-textbook`, `docs/VISON.md`, `docs/decks.md` | curriculum baseline·품질·scope gate |
| 교육학 자료 | UNSW/Monash의 constructive alignment | outcome, learning activity, assessment의 정렬 원칙 |
| 배포·도구 | Debian Policy, dash upstream, ShellCheck changelog | 특정 정책·구현·버전의 제한된 사실; POSIX authority 아님 |
| 로컬 관찰 | 설치된 `dash`와 `bash`의 작은 expansion probe | 이 실행 환경에 한정된 behavior |

**접근 한계:** The Open Group 공식 POSIX.1-2024 문서 URL은 이번 브라우저 요청에서 HTTP 403을 반환했다. 해당 조항의
텍스트는 **POSIX.1-2024로 식별되는 비공식 열람용 사본**에서 직접 대조했다. 공식 링크는 normative source를 가리키며,
mirror는 열람 경로로만 기록한다. 이를 공식 사이트에 직접 접속해 확인했다고 주장하지 않는다.

## 기술적 findings와 반영 결과

### F1. ordinary word expansion의 누락과 과도하게 일반화된 모델

**근거:** POSIX Shell Command Language §2.6은 적용 가능한 tilde, parameter, command, arithmetic expansions을 첫 단계에서
다루고, 이후 조건부 field splitting → pathname expansion → quote removal 순서로 정의한다. §2.6.1은 `HOME`이 unset일 때
기본 tilde expansion 결과를 unspecified로 둔다.

이 단계들은 모든 문맥에 일률 적용되는 것이 아니다. 특히 tilde expansion 결과는 field splitting과 pathname expansion을
위해 quoted된 것으로 취급된다. 따라서 `HOME="/tmp/space name"`인 경우 `~/file`을 부주의하게 두 필드로 나누는 설명도
틀리다. `"~/file"`은 tilde expansion의 예시로 사용해서는 안 된다(그대로 문자열로 남는다).

**반영:** README의 scope와 word model에 tilde를 명시하고, expansion context caveat와 tilde 결과의 quoted 취급을
추가했다. Unit 1은 `~`, `~/path`, quoting을 소유하며 assignment-specific tilde는 Unit 2에 둔다. 첫 calibration slice의
중심은 여전히 ordinary command argument → exact argv다.

### F2. arithmetic expansion이 scope만 있고 학습 책임이 없던 문제

**근거:** POSIX §2.6.4의 `$((expression))`는 arithmetic expression 결과를 word에 치환한다. `((expression))`을 독립된
portable command로 오해하지 않도록 구별해야 한다.

**반영:** Unit 1에서 작은 정수 식의 결과와 최종 argv를 예측하고, Unit 4의 counter update에서 재사용하도록
responsibility를 나눴다. 이미 존재하는 Unit 0–7 구조나 prerequisite scope는 바꾸지 않았다.

### F3. `case`와 `for`를 exit-status 기반 분기로 잘못 묶은 문제

**근거:** POSIX §2.9.4.2의 `for`는 expanded item list를 순회하고, §2.9.4.3의 `case`는 pattern matching으로 clause를
선택한다. §2.9.4.4–2.9.4.6의 `if`/`while`/`until`은 condition compound-list의 exit status가 실행 여부를 결정한다.
`&&`/`||` 역시 status가 short-circuit을 결정한다. **선택 입력**과 **construct가 반환하는 exit status**는 서로 다르다.

`case`에 매칭이 없을 때 반환 status는 0, `for`의 item이 없을 때도 0으로 정의된다. 이러한 **결과 status**가 해당
construct의 선택 입력이 된다는 뜻은 아니다.

**반영:** O7을 decision mechanism별 설명으로 교정했다. Unit 3 제목과 본문에서 status-based conditional execution과
`case` pattern matching을 분리했다. Unit 4에서 `for` item list와 `while`/`until` status condition을 대비했다. O4에서
positional argument 처리 도구로 잘못 배치된 `$?`를 빼고 Unit 3의 status topic에 남겼다.

**교육적 주의:** Unit 1의 pathname patterns와 Unit 3의 `case` shell patterns는 관련되지만
**pathname expansion 자체와 `case` matching은 같은 실행 단계가 아니다**.

### F4. Outcome → development → assessment 추적성 부재

**근거:** repository의 `adudeck-deck-curriculum` baseline은 outcome development/assessment coverage를 요구한다.
UNSW/Monash의 constructive alignment guidance도 학습 성과, 학습 활동, 평가 증거를 연결한다. 커리큘럼 주제 목록만으로
competence 획득을 검증할 수 없다.

**반영:** README에 O1–O11 각각의 develop unit과 observable assessment evidence를 작성했다. 이 표는
**평가 설계의 추적 계약**이며 아직 실제 문항, 루브릭, 실행 artifact가 존재한다는 뜻이 아니다.

**경계:** 이 PR의 목적은 학습 성과별 평가 설계의 책임을 지정하는 것이지, 사전 실습·교본 전체를 새로 생성하는 것이
아니다.

## 실행 관찰: 범위를 제한한 확인

로컬 환경의 `dash`, `bash`에서 동일한 예를 실행했다.

~~~sh
HOME='/tmp/space name'
set -- ~/x "~/x" "$((2 + 3))"
printf 'argc=%s\n' "$#"
printf '<%s>\n' "$@"
~~~

각 shell에서 `argc=3`, `</tmp/space name/x>`, `<~/x>`, `<5>` 형태의 결과를 관찰했다. 이 관찰은 해당 로컬 바이너리와 실행
설정에만 적용되며 모든 POSIX-conforming shell의 행동을 증명하지 않는다. ShellCheck와 repository validation을 이 probe로
대체하지 않는다.

## 현재 배포 지원성 관련 재확인

- [Debian Policy v4.7.4.1, Files](https://www.debian.org/doc/debian-policy/ch-files.html)은 `/bin/sh`에 대해
  **POSIX.1-2017 + 명시된 Debian additions**를 기준으로 둔다. `local`은 Debian allowance이며 portable POSIX guarantee가
  아니다.
- [dash upstream](https://kernel.googlesource.com/pub/scm/utils/dash/dash/)에서는 2026년 현재 0.5.13.x 후속 release가
  확인된다. **upstream의 버전**만으로 특정 배포판 `/bin/sh`의 기능을 단정할 수 없다.
- [ShellCheck CHANGELOG](https://github.com/koalaman/shellcheck/blob/master/CHANGELOG.md)에는 POSIX.1-2024에 표준화된
  ANSI-C quoted strings 때문에 SC3003을 제거한 기록이 있다. 정적분석 진단의 변경 속도를 language specification의 변경
  속도와 혼동하지 않는다.
- POSIX.1-2024의 `pipefail`, `$'...'`, `;&` 등의 존재는 **현장 배포 구현의 기능 지원**과 별개다. 이번 calibration
  slice에 이 표준 개정의 adoption-sensitive 기능을 필수 사용하도록 추가하지 않았다.

## Review pass / 반증 시도

| 검토 관점 | 반증 질문 | 결론 |
| --- | --- | --- |
| Normative semantics | `case`와 `for`도 status를 반환하므로 결국 status-based branch 아닌가? | 반환값과 selection input을 구별해야 한다. 종전 표현 기각 |
| Expansion fidelity | tilde 결과가 공백을 포함하면 unquoted word여도 splitting되는가? | POSIX tilde result는 quoted처럼 취급된다. context caveat 반영 |
| Curriculum dependency | arithmetic을 Unit 4만으로 미뤄도 첫 argv model이 완전한가? | Unit 1 최소 semantics + Unit 4 응용이 더 일관됨 |
| Assessment alignment | 모든 outcome에 Unit 주제만 할당하면 충분한가? | 불충분. 관찰 가능한 assess evidence 지정 필요 |
| Scope pressure | 연구 결과마다 새 unit/chapter/Playground를 만들어야 하는가? | 불필요. 현재 README 내부 최소 correction으로 처리 |
| Portability | 로컬 dash·bash 결과와 lint가 표준 호환성을 입증하는가? | 아님. 표준·실행 관찰·도구를 분리 |

두 번의 성격이 다른 확인을 수행했다: (1) 표준 의미와 커리큘럼 구조에 대한 대조, (2) 학습자가 오해하기 쉬운 예외와 증거
경계를 반증하는 검토. 추가 breadth가 새로운 blocking finding을 만들 근거는 아직 없다.

## 잔여 검증과 handoff

조사 시작 시점의 GitHub PR은 `open`, `mergeable=true`, `main` 대비 **4 commits behind**, unresolved review threads
**6개**였다. 다음 검증은 **새 HEAD**를 기준으로 수행해야 한다.

1. README O1–O11 coverage가 유지되고 정의된 4개 오류 표현이 더 이상 존재하지 않는지 확인.
2. PR review thread별로 **의미상 반영 여부**를 판단한다. 과거 `outdated`는 의미상 resolved와 다르므로 별도 검토한다.
3. 새 커밋의 `ci/validated` 완료를 확인한다. GitHub mergeability와 실제 curriculum quality를 구분한다.
4. 최신 `main`과 충돌·policy drift를 확인한다.
   **4-commit lag 자체는 이번 research-only scope에서 임의로 rebase/merge하지 않는다.**
5. 이후 작은 첫 실습(`source line → final argv`)을 만든다면 사용할 shell versions, ShellCheck version, 실제 runtime
   fixture를 그 increment에서 고정한다.

## 출처

### 언어 규범 (normative URL / 직접 대조에 사용한 2024 mirror)

- The Open Group,
  [POSIX.1-2024 Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html):
  §§2.6, 2.6.1, 2.6.4, 2.9.3, 2.9.4.
- [POSIX.1-2024 Shell Command Language 열람 사본](https://posix.fail/spec/posix/2024/utilities/V3_chap02.html): 같은
  개정판의 해당 조항을 검색·대조하기 위한 unofficial mirror.
- The Open Group,
  [POSIX.1-2024 Utility Conventions](https://pubs.opengroup.org/onlinepubs/9799919799/basedefs/V1_chap12.html), §12.2.
  Quoting은 argument boundary만 보존하며 utility가 leading-dash operand를 option으로 해석하지 않는다는 보장은 아니다.

### 설계·배포 evidence

- [UNSW, Aligning Assessment with Outcomes](https://www.teaching.unsw.edu.au/aligning-assessment-learning-outcomes).
- [Monash University, Create Constructive Alignment](https://www.monash.edu/learning-teaching/teachhq/Teaching-practices/learning-outcomes/how-to/constructive-alignment).
- [Debian Policy 4.7.4.1, 10. Files](https://www.debian.org/doc/debian-policy/ch-files.html).
- [dash upstream repository](https://kernel.googlesource.com/pub/scm/utils/dash/dash/).
- [ShellCheck changelog](https://github.com/koalaman/shellcheck/blob/master/CHANGELOG.md).
- Repository `.rulesync/skills/adudeck-deck-curriculum/SKILL.md`, `.rulesync/skills/adudeck-textbook/SKILL.md`,
  `docs/VISON.md`, `docs/decks.md` 및 PR #35 review thread.

## 2026-11-18 후속 계획과 리뷰·개선 실행 기록

현재 PR #35의 책임은 **연구와 커리큘럼 foundation**이다. textbook chapter 및 playground의 실제 구현은
이 foundation이 정리된 후 별도 소규모 increment로 진행한다. 두 작업의 acceptance를 혼동하지 않는다.

### 단계별 계획

| 단계 | 책임과 산출물 | Gate |
| --- | --- | --- |
| P1 · 조사 신뢰성 | 기존 문서의 POSIX 조항, 시간상 오래된 판단, evidence hierarchy 검토 | 잘못된 표준 분류·broken reference가 없음 |
| P2 · 커리큘럼 인계 | O1–O11 coverage와 첫 calibration slice의 예측·관찰·수정 기준 확정 | outcome, unit owner, 관찰 가능한 evidence가 연결됨 |
| P3 · 리뷰 → 개선 반복 | 발견을 증거로 검증하고 최소 수정, 같은 acceptance를 재검토 | 새로운 material blocker가 없고 변경 사항이 수렴 |
| P4 · PR 최종화 | review thread, 최신 branch status, `main` 차이 및 CI 확인 | HEAD 기준 성공·통합 위험 및 잔여 판단 명시 |
| P5 · 다음 build increment | O1/O2를 위한 첫 source → argv 학습 번들·격리된 fixture·평가 | 실제 설명/예측/관찰/repair/transfer가 완성된 뒤 merge gate 별도 적용 |

### 검토 1: 연구 문서와 출처의 정확성

- POSIX.1-2024 §2.6, §2.6.1, §2.9.4.2–2.9.4.6을 2024 표기된 열람 사본과 재대조했다.
  공식 The Open Group URL이 HTTP 403이어서 원문 열람은 mirror에 한정했다.
- 2026-11-08 조사 보고서의 섹션 번호가 ` ``2.6` ` 형식으로 깨진 구간을 확인했다.
- **개선:** 2026-11-08 보고서의 표준 조항 표기 12건과 12.2 Guideline 10 표기를 수정했다.
  해당 보고서가 현재 PR 판단이 아니라 *2026-11-08 당시의 역사적 평가*임도 명시했다.
- **재검토:** 깨진 POSIX 조항 패턴은 0건, 보고서의 상태 안내와 링크는 유지됐다.

### 검토 2: 첫 calibration slice의 평가 가능성

- 기존 README는 `predict → observe → explain → repair → transfer` 순서를 선언했지만,
  학습자에게 **어떤 입력/상태를 예측해야 하는지**에 대한 구체적인 수용 예시가 부족했다.
- **개선:** First Calibration Slice에 whitespace, empty, glob, repair/transfer 네 가지 probe class를
  명시하고, `argc/argv`를 실행 전에 예측하고 관찰하게 하는 acceptance contract를 추가했다.
  기본 `IFS`, glob fixture, 필요한 환경값과 정확한 glob 순서의 locale 경계도 명시했다.
- **재검토:** README에는 Unit 0–7 총 8개, observable outcome 11개와 coverage row 11개,
  calibration probe row 4개가 유지된다. `case`/`for` 구분과 tilde 책임도 유지했다.
- **scope 유지:** 표는 추후 작성할 textbook·playground의 수용 기준이지 해당 artefact가 이미
  구현·실행되었다는 주장이 아니다.

### 검토 3: 좁은 런타임 관찰의 추가 반증

2026-11-18 현재 사용 가능한 로컬 바이너리로 작은 probe를 실행했다.
이는 연구 evidence이며 repository CI·정적 분석과 독립적이다.

| Shell | 이 환경의 식별 정보 | 관찰 |
| --- | --- | --- |
| `dash` | Debian package 0.5.12-12 | argc 3, quoted/unquoted tilde 차이, arithmetic 5 |
| `bash --posix` | GNU Bash 5.2.37 | 동일한 세 인자 경계 및 결과 |
| `busybox ash` | BusyBox 1.37.0 | 동일한 세 인자 경계 및 결과 |

예상한 값은 `HOME='/tmp/space dir'`로 고정한 `~/x`, `"~/x"`, `"$((2 + 3))"` 세 argument였다.
세 셸 모두 `argc=3`, `</tmp/space dir/x>`, `<~/x>`, `<5>`를 보였다. 추가로
`case` no-match, `for` no-items, 실행된 branch 없는 `if`의 결과 exit status는 이 세 로컬 셸에서 모두 0이었다.

**한계:** 여기에는 모든 locale·POSIX 구현·실제 배포 `/bin/sh` 정책이 포함되지 않는다.
관찰 결과를 표준의 대체물이나 무제한 portability claim으로 해석하지 않는다.

### 다음 build increment의 인계 조건

1. Unit 1 전체를 한 번에 작성하지 않는다. ordinary command argument에서의 quoting/expansion과
   exact `argc/argv` 예측만 첫 slice로 둔다.
2. 실행 전에 whitespace, empty, glob 입력의 예상 `argc/argv`를 적고,
   실제 인자 경계를 노출하는 관찰을 배치한다. 하나의 broken quoting case를 repair하고
   다른 입력으로 transfer한다.
3. 교본은 개념·worked example·예측·오개념 반례·checkpoint를 담당하고,
   playground는 격리된 fixture 및 재현 가능한 observation을 담당한다.
4. 사용한 `sh` 구현/버전, ShellCheck 버전(사용한다면), fixture, `IFS`, locale를 기록한다.
   테스트 통과는 **그 대상 환경의 관찰**이며 universal POSIX conformance 증명이 아니다.
5. 본 PR의 acceptance를 넘어서는 새 chapter·playground 작성은 후속 incremental PR에서 관리한다.

## 최종 경계

이 문서는 공개 자료의 **독자적 분석 및 인용 링크**만 기록한다. raw third-party text, account data, credential, private
Notion URL을 복제하지 않는다. 실행 검증, 리뷰 UI 상태, GitHub CI는 각각 독립적인 증거이며 어느 하나를 다른 것의 증명으로
승격하지 않는다.
