# PR #35 · 심층 리뷰

작성일: 2026-10-05  
검토 대상 revision: `eb868f5b170c1b344054e96aeb27e8ad3ffec91d`  
대상: PR #35 `feat/posix-sh-deck-foundation` → `main`

## 결론

**현재 상태는 NOT MERGE-READY다.**

PR의 연구 방향과 교본 기반은 강하다. POSIX.1-2024를 normative authority로 두면서 deployed implementation,
platform policy, static-analysis tooling을 분리한 evidence model은 적절하고, 첫 calibration slice를 ordinary argument
context의 `source text → final argv`로 좁힌 결정도 유지할 가치가 있다.

하지만 repository의 `adudeck-deck-curriculum` contract 기준으로 merge 전에 닫아야 할 material gap이 네 가지 남아 있다.

1. learning outcome → development / assessment coverage mapping이 없다.
2. `case`와 `for`의 decision mechanism을 exit-status 기반으로 분류한 설명이 아직 남아 있다.
3. POSIX word expansion의 `tilde expansion`이 recurring model과 Unit 1에서 빠져 있다.
4. `arithmetic expansion`을 scope/core model에 약속했지만 어느 unit도 명시적으로 소유하지 않는다.

이 네 항목은 전체 연구 방향을 뒤집는 문제는 아니다. **작은 curriculum repair로 닫을 수 있지만, 현재 baseline을 그대로
accepted foundation으로 간주하기에는 부족하다.**

2026-10-03 research report의 `Final Review Disposition`이 말하는 “implementation increment로 handoff할 수 있는 수준”은
이 문서의 merge-readiness 판단으로 supersede한다. 연구의 factual findings 자체를 폐기한다는 뜻은 아니다.

## Review method · mols-loops

이번 검토는 `mols-loops`의 Prepare → RPI Main Loop → Finalize envelope로 진행했다. 불필요한 반복을 채우지 않고,
새 evidence가 실제 결론을 바꾸는 동안만 loop를 이어갔다.

| Loop | Lens | Result |
| --- | --- | --- |
| 1 | repository / curriculum contract | baseline gate와 현재 README를 대조해 assessment traceability와 scope-to-unit coverage gap을 식별 |
| 2 | POSIX semantic falsification | expansion order와 `if`/`while`/`until` vs `case`/`for` decision mechanism을 normative text로 재검증 |
| 3 | evidence freshness / portability | Debian/dash, BusyBox ash, ShellCheck, POSIX.1-2024 adoption claims을 현재 evidence와 재대조 |
| 4 | pedagogy / merge readiness | concept dependency, first slice, review thread 상태, live `main` drift와 CI를 함께 검토해 blocker set을 수렴 |

네 번째 review 이후 새 curriculum redesign blocker는 나오지 않았다. 남은 작업은 아래 finding의 bounded repair다.

## What is already strong

### 1. Evidence hierarchy가 정확하다

현재 foundation은 다음을 한 층으로 섞지 않는다.

```text
POSIX language revision
→ shell implementation / build configuration
→ platform / distribution policy
→ lint / static-analysis tooling
```

이 경계는 portable `sh` 학습에서 매우 중요하다. 특히 “표준화됨”과 “현재 배포된 `/bin/sh`에서 바로 동작함”을 같은
주장으로 취급하지 않는 방향은 유지해야 한다.

### 2. 기존 deep research의 핵심 correction은 유효하다

재검증 결과 다음 판단은 유지된다.

- `pipefail`은 POSIX.1-2024에 포함되므로 Bash-only로 분류하면 안 된다.
- `$'...'` 역시 POSIX.1-2024에 들어왔지만 deployed shell adoption은 별도 문제다.
- Debian `/bin/sh` policy는 POSIX language definition과 별개의 platform contract다.
- BusyBox ash의 `pipefail`과 dollar-single-quote support는 build configuration에 영향을 받을 수 있다.
- ShellCheck 결과는 tool version에 따라 달라질 수 있으므로 normative authority가 아니다.
- command substitution의 trailing-newline loss, pipeline의 subshell/current-environment boundary, `&&`/`||`의 동일
  precedence / left associativity를 명시적으로 다루는 방향은 기술적으로 타당하다.

### 3. Mental model 중심 설계가 좋다

다음 네 model은 syntax catalog보다 shell의 실제 실행 의미를 가르치기에 적합하다.

```text
source word → expansion/context → final argv
command → exit status → control-flow result
fd connection → stream/data flow
current shell / command / subshell → state mutation boundary
```

단, 두 번째 model은 모든 control-flow construct의 **decision input**이 exit status라는 뜻으로 확장하면 안 된다. 이
구분이 Finding 2의 핵심이다.

### 4. 첫 calibration slice는 적절하게 작다

전체 Unit 1을 한 번에 구현하지 않고 ordinary argument context에서 exact argv boundary를 예측·관찰·수정하게 만드는
slice는 information gain이 높다.

```text
predict
→ observe
→ compare
→ explain
→ vary
→ repair
→ transfer
```

이 pattern은 이후 environment, fd, exit status, subshell state에도 재사용할 수 있다.

## Findings

### Finding 1 · Outcome development / assessment coverage가 없다 — MERGE BLOCKER

`adudeck-deck-curriculum`은 curriculum baseline에 substantial outcome이 어디에서 개발되고 어디에서 평가되는지의
coverage를 요구한다. 현재 README에는 11개의 observable learning outcome과 unit architecture, generic practice model은
있지만 이 둘을 연결하는 map이 없다.

이 상태에서는 모든 unit을 작성해도 다음 competence가 실제로 평가되는지 추적하기 어렵다.

- validation evidence의 한계를 구분하는 능력
- platform/Bash assumption을 portable target으로 repair하는 능력
- bounded portability claim을 제시하는 능력
- 작은 automation script를 독립적으로 설계하는 synthesis outcome

**Required repair:** README의 curriculum baseline에 compact outcome coverage map을 추가한다. 개별 exercise 문항까지
설계할 필요는 없고, 각 outcome의 development owner와 assessment owner를 명시하면 된다.

최소 형태 예시는 다음과 같다.

| Outcome | Develop | Assess |
| --- | --- | --- |
| O1–O2 argv / quoting | Unit 1 | argv prediction + broken quoting repair |
| O3 variables / environments | Unit 2 | context/state tracing |
| O4 argument preservation | Unit 2 + Unit 4 | wrapper/function argv transfer |
| O5 fd / pipeline | Unit 2 | fd redirection tracing |
| O6 shell/subshell mutation | Unit 2 + Unit 4 | pipeline-state bug repair |
| O7 control flow | Unit 3 + Unit 4 | mechanism-aware execution tracing |
| O8 functions | Unit 5 | function state/status tracing + modification |
| O9 validation evidence | Unit 6 | evidence classification / claim boundary |
| O10 portability repair | Unit 6 + Unit 7 | Bash/platform assumption repair + bounded claim |
| O11 synthesis | Unit 7 | capstone contract → implementation → evidence |

이 table은 review 제안이며 exact wording은 baseline owner가 결정하면 된다.

### Finding 2 · `case`와 `for`를 exit-status decision으로 묶고 있다 — MERGE BLOCKER

현재 outcome 7은 `if`, `case`, `for`, `while`, `until`, `&&`, `||`를 모두 “exit-status 기반 control flow”로 묶는다.
Unit 3도 `case`를 `Decisions Are Exit Status` 안에서 같은 status model로 소개한다.

하지만 decision mechanism은 다르다.

```text
if / while / until
→ command list 실행
→ exit status가 다음 path를 결정

&& / || / !
→ command/pipeline status가 실행/negation을 결정

case
→ expanded word와 shell pattern을 비교
→ matching clause를 선택
→ 선택된 clause 실행 결과로 case 자체의 exit status가 생김

for
→ expanded item list를 순회
→ 각 item을 variable에 대입
→ body 실행 결과로 for 자체의 exit status가 생김
```

즉 `case`와 `for`도 **결과 exit status는 갖지만**, branch/iteration을 고르는 input이 exit status는 아니다.

이 지적은 이전 Codex thread가 diff 이동 때문에 `outdated`로 표시되었지만 **semantic issue는 현재 README에도 남아 있다.**
GitHub의 outdated 상태를 resolved disposition으로 해석하면 안 된다.

추가로 outcome 4에서 `$?`를 `$#`, `"$@"`, `shift`와 함께 argument processing 도구처럼 묶은 것도 정리하는 편이 좋다.
`$?`는 argument preservation보다 status model의 책임이다.

**Required repair:**

- outcome 7을 “control-flow construct의 decision input과 resulting status를 구분한다”는 방향으로 교정한다.
- Unit 3에서 `case`를 status-based selection으로 설명하지 않는다.
- `case`에 필요한 최소 shell pattern-matching semantics를 Unit 1 pathname pattern 또는 Unit 3의 명시적 prerequisite로
  연결한다.
- `for`는 Unit 4의 item-list iteration model로 유지한다.
- `$?`는 argument-processing outcome이 아니라 status/control-flow outcome으로 이동한다.

### Finding 3 · recurring word-expansion model에서 tilde expansion이 빠져 있다 — MERGE BLOCKER

README의 ordinary-word model은 다음을 반복 모델로 제시한다.

```text
source word
→ parameter / command / arithmetic expansion
→ field splitting
→ pathname expansion
→ quote removal
→ final argv fields
```

POSIX.1-2024의 word-expansion order에는 첫 단계에 **tilde expansion**이 함께 있다. 따라서 `~/file`처럼 흔한 word가 현재
learner-facing model에서는 설명되지 않는다.

이 문제는 “모든 POSIX expansion을 반드시 Unit 1에서 깊게 가르쳐야 한다”는 뜻은 아니다. 선택지는 둘이다.

1. Unit 1에 basic tilde expansion을 최소 범위로 포함한다.
2. tilde expansion을 명시적으로 defer/out-of-scope하고, 위 diagram이 complete ordinary-word expansion pipeline처럼
   읽히지 않도록 scope를 좁힌다.

현재 deck의 beginner goal과 `~/...`의 빈도를 고려하면 **basic tilde expansion을 Unit 1에서 소유하는 쪽이 더 단순하다.**

### Finding 4 · arithmetic expansion이 scope에는 있지만 unit owner가 없다 — MERGE BLOCKER

`arithmetic expansion`은 현재 세 곳에서 core promise로 등장한다.

- Learning Scope에 포함됨
- recurring Source-to-Arguments model에 포함됨
- research report의 conservative portable core에 포함됨

하지만 Unit 1은 parameter expansion과 command substitution만 나열하고 `$((...))`를 배정하지 않는다. 이후 unit에도
arithmetic expansion을 학습 책임으로 명시한 곳이 없다.

이대로 구현을 시작하면 Unit 4의 counter/loop 예시에서 `$((...))`가 **선행 설명 없이 사용되는 prerequisite leak**가 생길
가능성이 높다.

**Required repair:** arithmetic expansion의 owner를 명시한다. 가장 자연스러운 형태는 다음 중 하나다.

- Unit 1: expansion stage로서 최소 semantics와 argv 결과를 인식 → Unit 4: counter/iteration에서 실제 사용
- 또는 Unit 4에 완전한 책임을 주되 Unit 1 model에서 “later unit에서 상세화”라는 dependency를 명시

어느 방식을 택하든 scope → concept dependency → unit responsibility가 traceable해야 한다.

## Review-thread disposition

검토 시점 GitHub에는 unresolved review thread가 6개 있다.

- 3개는 현재 diff에 그대로 붙어 있는 active thread다: tilde expansion, arithmetic expansion, outcome-assessment map.
- 3개는 `outdated` 상태다: `pipefail` classification, control-flow mechanism, leading-dash/filename safety.

의미상 disposition은 다음처럼 구분해야 한다.

| Prior thread | Semantic disposition |
| --- | --- |
| `pipefail` classification | **Resolved in content** — POSIX.1-2024 + adoption-sensitive로 수정됨 |
| `case` / `for` control-flow mechanism | **Still open** — thread는 outdated지만 현재 outcome/Unit wording에 문제 잔존 |
| leading-dash filename safety | **Mostly resolved / narrowed** — current outcome은 shell-level argument preservation 중심. utility option parsing은 future example에서 별도 boundary 필요 |
| tilde expansion | **Open** |
| arithmetic expansion ownership | **Open** |
| outcome → assessment mapping | **Open** |

merge 전에는 thread UI 상태가 아니라 **semantic disposition을 기준으로 수정·resolve**해야 한다.

## Evidence / freshness review

이번 deep pass에서 version-sensitive claim을 다시 확인했다.

### POSIX.1-2024

Normative source:
<https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>

재확인한 핵심:

- word expansion에는 tilde / parameter / command / arithmetic expansion이 포함된다.
- `if`, `while`, `until`은 command-list exit status를 decision input으로 사용한다.
- `case`는 pattern matching으로 clause를 고른다.
- `for`는 expanded list item을 순회한다.
- `pipefail`은 Issue 8 / POSIX.1-2024 pipeline semantics에 포함된다.
- multi-command pipeline의 subshell/current-environment portability boundary를 현재 research가 올바르게 다룬다.

### Debian / dash

- Debian Policy 4.7.4.1은 `/bin/sh` baseline을 POSIX.1-2017 + Debian-specific additions로 유지한다.
- Debian stable/unstable의 dash 0.5.12 line과 upstream/newer dash line 사이의 adoption lag를 구분한 research 방향은
  유지 가능하다.
- `$'...'`와 `pipefail`을 feature-by-feature adoption 문제로 다루는 판단은 타당하다.

### BusyBox ash

현재 BusyBox ash source에서도 `BASH_PIPEFAIL`과 `BASH_DOLLAR_SQUOTE`가 `ENABLE_ASH_BASH_COMPAT`에 연결되어 있다.
따라서 “BusyBox라는 implementation 이름만으로 capability를 단정하지 않는다”는 research disposition은 적절하다.

### ShellCheck

stable release와 master rule-set이 POSIX.1-2024 adoption을 같은 시점에 반영하지 않을 수 있다는 research 경계도 유지된다.
expected warning을 학습 evidence로 고정할 때 version을 기록하겠다는 방침은 적절하다.

### Pedagogy references

MIT Missing Semester 2026은 현재도 Bash-oriented material이며, 좋은 exercise structure와 POSIX dialect authority를
분리해서 평가해야 한다는 결론을 지지한다. 따라서 external tutorial은 pedagogy source로만 사용하고 core code semantics는
POSIX source에서 다시 검증하는 현재 정책을 유지한다.

## Non-blocking risks for implementation

### Unit 2 cognitive load

Unit 2는 assignment/environment, positional parameters, fd/redirection, pipeline, execution-environment boundary를 한
unit에 모은다. Concept dependency상 같은 integration zone에 둘 수는 있지만 실제 textbook chapter를 작성할 때 한
chapter로 압축하면 cognitive load가 커질 수 있다.

**Disposition:** curriculum blocker는 아니다. `adudeck-textbook-write` 단계에서 chapter/bundle을 여러 개로 나누더라도
Unit 2 responsibility는 유지할 수 있다.

### `mktemp` utility boundary

research의 utility-portability open question에 `mktemp`가 예로 등장한다. 향후 Unit 6/7 cleanup example에서 temporary
resource를 만들기 위해 `mktemp(1)`을 사용하려면 POSIX core utility라고 암묵적으로 취급하지 말고 해당 platform/tool
boundary를 따로 검증·표시해야 한다.

**Disposition:** 현재 curriculum blocker는 아니다. 실제 cleanup example을 작성할 때 resolve한다.

### Branch freshness

검토 시점 PR branch는 current `main`보다 1 commit 뒤이고 compare state는 `diverged`다. 다만 PR은 mergeable하며,
`adudeck-deck-curriculum`과 `adudeck-textbook` Skill content는 PR head와 current `main`에서 동일했다.

**Disposition:** 현재 finding의 원인은 branch drift가 아니다. 최종 merge 전 latest `main`과 integration status를 다시
확인한다.

## CI / repository state

검토 대상 revision `eb868f5b170c1b344054e96aeb27e8ad3ffec91d`에는 `ci/validated = success` status가 있었다.
이것은 repository tree validation이 통과했다는 evidence이지 curriculum semantic correctness의 proof는 아니다.

이 review report 자체와 후속 repair가 branch를 변경하므로 merge gate에서는
**새 final head의 CI/status를 다시 확인해야 한다.**

## Minimal repair sequence

현재 방향을 유지하면서 가장 작은 repair 순서는 다음이 적절하다.

1. outcome 4/7과 Unit 3의 control-flow semantics를 교정한다.
2. tilde expansion과 arithmetic expansion의 scope/unit ownership을 닫는다.
3. 11개 outcome의 development / assessment coverage map을 추가한다.
4. 2026-10-03 research report의 final disposition을 최신 review 상태에 맞게 명시적으로 supersede하거나 갱신한다.
5. 기존 review thread를 semantic disposition에 맞게 resolve한다.
6. final head에서 `ci/validated`, PR mergeability, latest `main` integration을 다시 확인한다.

이 순서는 textbook chapter나 playground 구현을 시작하는 것보다 먼저 수행하는 것이 낫다. Curriculum baseline이 바뀌는
작은 문제를 먼저 닫아야 downstream material을 다시 고치는 비용을 피할 수 있다.

## Final gate

검토 revision 기준:

- [x] repository / deck guidance loaded
- [x] current POSIX normative semantics rechecked
- [x] implementation / platform / tooling evidence boundaries rechecked
- [x] pedagogy / textbook foundation reviewed
- [x] current CI status inspected
- [ ] outcome → development / assessment mapping complete
- [ ] `case` / `for` decision mechanism accurately represented
- [ ] tilde expansion coverage resolved
- [ ] arithmetic expansion unit ownership resolved
- [ ] material review threads semantically resolved
- [ ] final post-repair head revalidated

최종 verdict는 **NOT MERGE-READY · small curriculum repair required**다.

PR의 핵심 연구 방향은 유지한다. 위 네 merge blocker를 닫은 뒤에는 전체 research를 다시 시작할 이유가 없고, 짧은
post-fix review + final CI 확인으로 first calibration slice 구현 단계에 handoff할 수 있다.
