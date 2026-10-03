# Beginner POSIX sh Textbook Research Report

Research date: 2026-10-03

## Decision Summary

기초 `sh` scripting textbook은 Bash 문법의 축약판으로 만들지 않는다.

권장 기준은 다음과 같다.

1. **Normative language authority:** POSIX.1-2024 Shell Command Language.
2. **Runnable beginner baseline:** 현재 널리 배포된 `/bin/sh` 구현에서도 동작하기 쉬운 보수적인 POSIX subset.
3. **Central mental model:** `source → tokens → parse → word expansion → redirection → execution → exit status`.
4. **First recurring difficulty:** quoting과 expansion이 최종 `argv`를 어떻게 만드는지 추적하는 능력.
5. **Pedagogy:** command recipe보다 `predict → observe → explain → repair → transfer`를 반복한다.
6. **Portability feedback:** `sh -n`과 ShellCheck `sh` mode를 사용하되, 도구의 rule set을 표준 자체로 간주하지 않는다.
7. **Bash-specific syntax:** 비교나 migration 문맥이 아니면 core path에 섞지 않고 명시적으로 경계를 표시한다.

이 결정은 `sh`의 초급 문법을 단순히 `if`, `for`, variable 순서로 나열하는 것보다 shell 특유의 실행 의미를 먼저
이해시키기 위한 것이다.

## Research Questions

다음을 조사했다.

- 2026년 현재 `sh` 교본의 규범 기준은 무엇이어야 하는가?
- POSIX shell을 처음 배울 때 어떤 mechanism이 다른 문법의 prerequisite인가?
- Bash tutorial의 좋은 교육 방식을 어디까지 재사용할 수 있는가?
- POSIX.1-2024의 새 기능과 실제 `/bin/sh` 구현 사이에는 어떤 compatibility risk가 있는가?
- 초급자가 portability 문제를 스스로 확인할 수 있는 최소 validation loop는 무엇인가?

## Source Hierarchy

### 1. POSIX.1-2024 Shell Command Language — normative

<https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>

현재 shell command language의 기준이다. `sh` utility가 사용하는 syntax와 semantics, token recognition, quoting,
expansion, redirection, command execution, functions, exit status 등을 정의한다.

교본에서 “POSIX `sh`에서 무엇을 의미하는가”를 판단할 때 가장 높은 기술 authority로 사용한다.

### 2. GNU Bash 5.3 Reference Manual — implementation/comparison

<https://www.gnu.org/software/bash/manual/bash.html>

Bash 5.3은 POSIX shell specification의 구현이지만 기본 Bash behavior와 POSIX behavior가 다른 지점이 있다. Bash는
`--posix`, `set -o posix`, 또는 `sh` 이름으로 invocation되는 경우 POSIX behavior에 더 가깝게 동작한다.

이 자료는 Bash-specific feature를 `sh` 표준으로 오인하지 않기 위한 비교 자료로 사용한다.

### 3. dash documentation and Debian compatibility evidence — deployed implementation

<https://manpages.debian.org/unstable/dash/dash.1.en.html>

<https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=989239>

`dash`는 작고 빠른 POSIX `/bin/sh` 구현이며 Debian/Ubuntu 계열에서 중요한 실제 compatibility surface다. 현재 Debian
unstable의 dash 0.5.12-12 man page는 quoting을 traditional single quote, double quote, backslash 세 종류로 설명한다.
Debian bug history에서는 POSIX.1-2024가 새로 표준화한 dollar-single-quotes (`$'...'`) 지원이 dash 0.5.12 계열에서
뒤따라오지 않았던 사례를 확인할 수 있다.

이 자료는 **표준에 들어갔다고 해서 배포된 모든 `sh`가 즉시 같은 기능을 제공하는 것은 아니다**라는 portability 경계를
보여준다.

### 4. ShellCheck — static feedback

<https://www.shellcheck.net/>

<https://www.shellcheck.net/wiki/SC3003>

ShellCheck는 shell script에서 흔한 syntax/semantic/portability 문제를 찾는 정적 분석 도구다. 특히 POSIX `sh` 대상으로
검사할 때 Bashism을 빠르게 발견하는 데 유용하다.

SC3003 문서는 중요한 시점 차이도 보여준다. `$'...'`는 예전에는 POSIX `sh`에서 Bash extension으로 경고되었지만
POSIX.1-2024가 Dollar-Single-Quotes를 도입하면서 해당 rule은 POSIX.1-2017까지만 적용된다고 명시한다. 즉 lint rule도
표준 revision에 따라 의미가 달라질 수 있다.

### 5. MIT Missing Semester 2026 — pedagogy, not syntax authority

<https://missing.csail.mit.edu/2026/course-shell/>

<https://missing.csail.mit.edu/2026/command-line-environment/>

Missing Semester는 shell을 command catalog가 아니라 program 실행, streams, arguments, return code, environment가
상호작용하는 환경으로 가르친다는 점에서 좋은 교육 참고 자료다.

다만 2026 material은 Bash를 사용하며 `[[ ... ]]`, `#!/usr/bin/env bash`, `pipefail` 같은 Bash-oriented 예시를 포함한다.
따라서 teaching move는 참고할 수 있지만 이 예시들을 POSIX `sh` syntax로 그대로 채택해서는 안 된다.

## Finding 1 · `sh`와 Bash를 먼저 분리해야 한다

초급자가 흔히 접하는 “shell scripting tutorial” 상당수는 실제로 Bash tutorial이다. Bash는 POSIX shell language를 많이
지원하지만 Bash-specific syntax와 behavior도 갖는다.

따라서 교본은 처음부터 다음 세 층을 분리해야 한다.

```text
POSIX shell language
        ↑
implementation: dash / Bash POSIX mode / other sh
        ↑
optional implementation-specific extensions
```

core example에 Bash feature를 섞은 뒤 나중에 “사실 portable하지 않다”고 정정하는 방식보다, portable core를 먼저 만들고
차이를 비교하는 편이 학습자의 mental model을 덜 흔든다.

초급 core에서 제외할 대표적인 Bash-oriented surface는 다음과 같다.

- `[[ ... ]]`
- arrays
- process substitution `<(...)`, `>(...)`
- `function name { ...; }` form
- `source`를 portable `.` 대신 사용하는 습관
- `${var//pattern/replacement}` 같은 Bash parameter expansion
- `set -o pipefail`

## Finding 2 · 문법의 중심은 parsing보다 “final argv”다

POSIX.1-2024는 shell operation을 대략 다음 순서로 설명한다.

```text
read input
→ recognize tokens
→ parse commands
→ perform word expansion
→ perform redirection
→ execute command/function
→ collect exit status
```

초급자가 가장 자주 틀리는 지점은 source code의 “문자열”이 그대로 program argument가 된다고 생각하는 것이다.

실제로 command 실행 전에 word expansion이 발생한다. POSIX.1-2024의 주요 expansion order는 다음과 같다.

```text
tilde / parameter / command / arithmetic expansion
→ field splitting
→ pathname expansion
→ quote removal
```

그래서 다음 두 코드는 단순히 quote 스타일만 다른 것이 아니다.

```sh
program $value
program "$value"
```

`$value` 안에 whitespace나 glob character가 있으면 최종 arguments의 개수와 값이 달라질 수 있다. 이 차이를 처음에
`argv` 관점으로 이해시키면 이후 `"$@"`, filename handling, loop, test 표현의 많은 오류를 같은 모델로 설명할 수 있다.

### Textbook implication

첫 calibration slice는 “variable 문법”이 아니라 **source word가 최종 arguments로 변하는 과정**이어야 한다.

학습자는 실행 전에 최종 arguments를 예측하고, 작은 inspector program 또는 shell function으로 실제 argument boundary를
관찰한 뒤, quote를 바꿔 다시 비교하는 방식으로 학습하는 것이 좋다.

## Finding 3 · exit status를 control flow의 공통 상태로 가르쳐야 한다

shell의 `if`는 다른 언어의 boolean expression을 평가하는 모델로 시작하면 오해하기 쉽다. shell에서는 command가 실행되고
그 exit status가 control decision에 직접 사용된다.

따라서 다음을 별도 주제로 가르치기보다 하나의 진행으로 묶는 것이 좋다.

```text
command exit status
→ $?
→ && / || / !
→ test / [ ]
→ if
→ while / until
→ function result
```

초반부터 성공/실패 status를 관찰하면 조건문과 error handling을 새 mental model로 다시 배울 필요가 없다.

## Finding 4 · redirection은 punctuation이 아니라 data flow다

`>`, `<`, `2>`, `2>&1`, pipeline을 symbol catalog처럼 외우게 하면 redirection order와 stderr 문제에서 쉽게 무너진다.

교본에서는 적어도 다음 상태를 분리해야 한다.

```text
process
├── stdin  (fd 0)
├── stdout (fd 1)
└── stderr (fd 2)
```

그리고 redirection이 **command가 실행되기 전에 file descriptor 연결을 바꾸는 단계**라는 점을 실행 순서와 연결한다.

pipeline은 stdout/stdin 연결과 exit status를 동시에 가진다. Bash의 `pipefail`을 초급 POSIX core 해결책처럼 제시하지
않고, 먼저 POSIX pipeline status와 명시적 error handling을 이해시키는 편이 적절하다.

## Finding 5 · script arguments에서는 `"$@"`가 핵심 invariant다

POSIX의 special parameter `@`는 positional parameters를 표현하며, double quote 안에서 사용할 때 각각의 parameter
boundary를 보존하는 중요한 동작을 가진다.

따라서 `for x in "$@"`, helper function forwarding, wrapper script 등의 예제로 **원래 argument vector를 보존한다**는
invariant를 반복하는 것이 좋다.

단순히 `$1`, `$2`를 순서대로 소개한 뒤 암기시키는 방식보다 다음 질문이 더 학습 가치가 높다.

- 빈 argument는 보존되는가?
- space를 포함한 filename은 한 argument로 남는가?
- wildcard가 caller 의도와 다르게 다시 expansion되는가?
- function에 arguments를 forwarding할 때 boundary가 유지되는가?

## Finding 6 · predictable output에는 `printf`를 기본으로 둔다

POSIX `echo`는 historical implementation 차이가 크다. 특히 첫 operand가 `-n`이거나 operand에 backslash가 들어가는 경우의
behavior는 portability problem이 될 수 있다.

따라서 단순한 고정 문자열을 빠르게 보여주는 정도를 제외하면, teaching script의 predictable formatted output은
`printf`를 기본으로 두는 것이 낫다.

이 선택은 학습자에게 쓸데없이 긴 command를 요구하려는 것이 아니라, escape와 option interpretation의 implementation
차이를 output lesson에 끌고 들어오지 않기 위한 것이다.

## Finding 7 · POSIX.1-2024와 “widely portable today”는 완전히 같지 않다

POSIX.1-2024는 Dollar-Single-Quotes (`$'...'`)를 shell language에 추가했다. 따라서 이것을 무조건 “Bash-only syntax”라고
가르치는 것은 2024 standard 기준으로는 더 이상 정확하지 않다.

하지만 deployed shell support는 동시에 갱신되지 않는다. dash 0.5.12 계열의 documentation과 Debian bug history는 이
implementation lag를 보여준다.

### Recommended policy

교본에서는 두 기준을 동시에 명시한다.

```text
normative explanation = POSIX.1-2024
runnable beginner core = conservative widely implemented subset
```

`$'...'` 같은 새 Issue 8 surface는 “현재 POSIX이지만 older/deployed implementation에서 확인 필요”로 표시한다. 이런
feature를 core exercise에 의존하게 만들기 전에는 실제 target shell matrix에서 검증한다.

이 원칙은 표준을 과거 버전에 고정하는 것보다 정확하고, 새 표준 문법 때문에 학습자의 script가 흔한 `/bin/sh`에서 바로
깨지는 문제도 피한다.

## Finding 8 · shebang은 shell grammar와 execution mechanism을 구분해 설명해야 한다

POSIX.1-2024 Shell Command Language는 shell command file의 첫 줄이 `#!`로 시작하면 그 shell-language 관점의 결과를
unspecified로 둔다.

실제 Unix-like 환경에서는 executable script가 `#!/bin/sh`를 사용해 interpreter를 선택하는 관례가 매우 흔하다. 따라서
교본에서 shebang을 빼는 것도 현실적이지 않다.

정확한 설명은 다음처럼 경계를 나누는 것이다.

```text
#!/bin/sh        → executable file을 어떤 interpreter로 시작할지 정하는 OS-facing convention
shell body       → sh가 해석하는 shell command language
```

그리고 다음 두 실행 형태가 왜 같은 경로가 아닐 수 있는지 비교한다.

```sh
./script.sh
sh script.sh
```

## Finding 9 · `set -e`를 초급 error-handling magic으로 시작하지 않는다

많은 Bash tutorial은 `set -euo pipefail` 같은 recipe를 매우 이르게 제시한다. 하지만 `pipefail`은 POSIX core가 아니고,
`set -e`의 효과도 shell grammar와 command context에 따라 단순한 “오류가 나면 항상 종료”보다 복잡하다.

기초 교본은 먼저 다음을 확립하는 편이 낫다.

- command는 exit status를 만든다.
- caller는 어떤 failure를 fatal로 볼지 결정한다.
- `if`, `&&`, `||`, explicit `exit`로 의도를 표현할 수 있다.
- cleanup이 필요한 경우 `trap`과 resource lifetime을 생각해야 한다.

그 다음 `set -e`를 convenience option과 failure case 분석 대상으로 소개하면, option이 control-flow reasoning을 대체하는
것을 막을 수 있다.

## Finding 10 · validation을 syntax / lint / runtime으로 나눈다

초급 실습의 validation은 한 도구에 의존하지 않는 편이 좋다.

### Syntax

```sh
sh -n script.sh
```

POSIX `sh`의 `-n`은 command를 실행하지 않고 parsing하는 syntax check에 사용할 수 있다.

### Static feedback

```sh
shellcheck -s sh script.sh
```

quoting 문제와 Bashism을 찾는 데 유용하다. 다만 ShellCheck의 개별 rule은 특정 POSIX revision이나 도구 버전에 의존할 수
있으므로 standard authority로 승격하지 않는다.

### Runtime behavior

portable claim이 중요한 exercise는 가능하면 둘 이상의 실제 shell implementation에서 실행한다. 예를 들어 Linux 환경이라면
system `/bin/sh`와 Bash POSIX mode를 비교할 수 있다.

```sh
sh script.sh
bash --posix script.sh
```

이것이 모든 POSIX implementation을 증명하지는 않는다. 목적은 syntax success를 portability proof로 오해하지 않고,
implementation-sensitive assumption을 실제 evidence로 드러내는 것이다.

## Recommended Curriculum Architecture

### Unit 0 · Script execution and simple commands

- interpreter/execution boundary
- comments
- simple commands
- `printf`
- first exit status observation

### Unit 1 · Words, quoting, and expansion

- tokens vs words vs final arguments
- single/double/unquoted forms
- parameter expansion
- command substitution with `$(...)`
- field splitting
- pathname expansion
- argument-boundary observation

### Unit 2 · Variables, parameters, redirection, pipelines

- assignment and environment
- positional/special parameters
- stdout/stderr
- redirection order
- pipelines and command lists

### Unit 3 · Conditional execution

- exit status model
- `test` / `[ ]`
- `if`
- `case`
- `&&`, `||`, `!`

### Unit 4 · Iteration and argument processing

- `for`, `while`, `until`
- `break`, `continue`
- `"$@"`, `$#`, `shift`
- filenames and empty arguments

### Unit 5 · Functions and small CLI structure

- POSIX function form
- positional parameters inside functions
- shared shell state
- `export`
- function status
- `getopts`

### Unit 6 · Failure, cleanup, debugging, portability

- explicit failure handling
- `trap`
- `sh -n`
- `set -x`
- ShellCheck
- Bashism repair
- implementation differences
- `set -e` limitations after the base status model is established

### Unit 7 · Capstone

- requirements → inputs/outputs/failure conditions
- incremental implementation
- final argument-boundary and stream checks
- cleanup/error scenarios
- portability checks

## First Calibration Slice

첫 slice는 **“source text가 final argv로 변하는 과정”**을 추천한다.

이 slice는 이후 거의 모든 unit에서 반복할 teaching pattern을 검증할 수 있다.

```text
1. 작은 command를 보여준다.
2. 실행 전에 argument 개수와 값을 예측한다.
3. argument boundaries를 보이는 관찰 도구로 실행한다.
4. variable value에 space / empty string / wildcard를 하나씩 넣는다.
5. quoted / unquoted form을 비교한다.
6. 왜 달라졌는지 expansion pipeline으로 설명한다.
7. 깨진 script를 최소 변경으로 고친다.
8. 새로운 filename/argument case에 transfer한다.
```

이 방식이 성공하면 variables, `"$@"`, tests, loops에서도 학습자가 syntax를 외우기보다 실제 execution state를 추적할 수
있다.

## Practice Types to Prefer

- **Prediction:** 이 line이 program에 몇 arguments를 전달하는가?
- **Tracing:** expansion 각 단계에서 field가 어떻게 변하는가?
- **Comparison:** `$*`, `$@`, `"$*"`, `"$@"`가 어떤 input에서 달라지는가?
- **Debugging:** space가 들어간 filename에서 실패한 이유는 무엇인가?
- **Repair:** Bashism을 POSIX form으로 최소 수정한다.
- **Modification:** stdout은 file로 보내고 diagnostic은 terminal에 유지한다.
- **Transfer:** 같은 helper function이 empty argument와 wildcard argument를 보존하도록 만든다.
- **Synthesis:** input, output, failure, cleanup 조건을 정의하고 작은 script를 설계한다.

단순히 완성된 script를 타이핑하는 과제는 competence evidence로 사용하지 않는다.

## Validation Plan for Future Textbook Slices

각 runnable slice는 필요한 수준에서 다음을 적용한다.

1. example source가 learner-facing scope와 일치하는지 review한다.
2. `sh -n`으로 syntax를 검사한다.
3. ShellCheck `sh` mode로 common semantic/portability issue를 확인한다.
4. portability claim이 중요한 example은 둘 이상의 relevant shell behavior를 비교한다.
5. expected stdout만 보지 않고 argument boundaries, stderr, exit status 등 해당 concept의 evidence를 관찰한다.
6. standard-new feature를 사용하는 경우 실제 implementation support를 별도 확인한다.
7. validation하지 않은 platform/implementation까지 “portable everywhere”라고 확대 주장하지 않는다.

## Risks and Open Questions

### Issue 8 adoption lag

가장 중요한 현재 risk다. POSIX.1-2024를 normative source로 사용하는 것은 맞지만, 실행 실습이 새 표준 surface에 너무 빨리
의존하면 common `/bin/sh`에서 실패할 수 있다.

**Disposition:** core executable path는 conservative subset으로 두고 새 Issue 8 feature는 compatibility note와 검증을
동반한다.

### `local` variable convention

여러 실제 shell에서 지원되지만 POSIX core language로 기대하면 안 된다. 초급 function unit에서는 global/shared shell
state를 먼저 정확하게 가르치고, implementation extension으로 필요할 때만 비교한다.

**Disposition:** core curriculum에서 portable guarantee로 사용하지 않는다.

### Exact shell matrix

미래 playground가 Linux-only인지 macOS까지 포함하는지에 따라 실제 implementation matrix가 달라진다.

**Disposition:** deck curriculum은 implementation-neutral하게 유지하고, first runnable slice를 만들 때
repository/runtime에서 검증 가능한 최소 matrix를 정한다.

## Research Conclusion

기초 `sh` textbook의 가장 중요한 선택은 chapter 수가 아니라 **어떤 mental model을 먼저 고정하느냐**다.

가장 재사용 가치가 높은 모델은 다음 두 가지다.

```text
source → expansion → final argv
command → exit status → control flow
```

여기에 file-descriptor data flow를 결합하면 quoting, variables, arguments, tests, loops, functions, error handling을
서로 독립적인 문법 항목이 아니라 하나의 실행 언어로 배울 수 있다.

따라서 첫 구현은 전체 textbook을 한꺼번에 채우지 않고 `source text → final argv` calibration slice를 완성한 뒤 설명
깊이, 관찰 방식, practice 난이도, portability validation을 검토하는 것이 적절하다.

## Public References

- The Open Group, POSIX.1-2024, Shell Command Language:
  <https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>
- GNU, Bash Reference Manual 5.3: <https://www.gnu.org/software/bash/manual/bash.html>
- Debian, dash(1) manual: <https://manpages.debian.org/unstable/dash/dash.1.en.html>
- Debian Bug #989239, dash Dollar-Single-Quotes support history:
  <https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=989239>
- ShellCheck: <https://www.shellcheck.net/>
- ShellCheck SC3003 history: <https://www.shellcheck.net/wiki/SC3003>
- MIT Missing Semester 2026, Introduction to the Shell: <https://missing.csail.mit.edu/2026/course-shell/>
- MIT Missing Semester 2026, Command-line Environment: <https://missing.csail.mit.edu/2026/command-line-environment/>
