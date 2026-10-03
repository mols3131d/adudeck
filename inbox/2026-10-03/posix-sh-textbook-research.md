# Beginner POSIX sh Textbook Research Report

Research date: 2026-10-03
Research mode: deep iterative review

## Decision Summary

기초 `sh` scripting textbook은 Bash 문법의 축약판이나 syntax catalog로 만들지 않는다.

권장 기준은 다음과 같다.

1. **Normative authority:** POSIX.1-2024 Shell Command Language를 현재 언어 의미의 기준으로 삼는다.
2. **Runnable baseline:** 초급 core example은 POSIX.1-2024 전체가 아니라 현재 흔한 `/bin/sh`에서도 검증하기 쉬운
   보수적인 공통 부분을 우선한다.
3. **Central execution model:**
   `source → token recognition → parsing → expansion → redirection → execution → exit status`를 반복해서 사용한다.
4. **Central data invariant:** source의 word와 program이 받는 final argument vector는 같은 것이 아니다. quoting과
   expansion이 argument boundary를 결정한다.
5. **Central control invariant:** shell의 조건과 반복은 command가 만드는 exit status를 중심으로 이해한다.
6. **Environment model:** current shell environment, command environment, subshell environment를 구분한다. 특히
   pipeline에서 state mutation이 parent shell에 남는다고 가정하지 않는다.
7. **Portability model:** `표준 여부`, `배포 구현 지원`, `배포판 정책`, `lint tool 판단`을 서로 다른 층으로 유지한다.
8. **Pedagogy:** `predict → observe → explain → vary → repair → transfer`를 syntax transcription보다 우선한다.
9. **Validation:** syntax, static feedback, runtime behavior, implementation comparison을 구분하고 어느 하나도
   portability proof로 과장하지 않는다.
10. **Scope discipline:** shell이 작고 투명한 glue/automation에 적합한 범위를 가르치되, 큰 application architecture를
    shell로 확장하는 것을 목표로 삼지 않는다.

가장 중요한 연구 결론은
**“POSIX.1-2024 compliant”와 “오늘 여러 `/bin/sh`에서 바로 동작한다”는 동일한 주장도, 동일한 evidence도 아니라는 것**이다.

## Corrections Discovered During Deep Review

이번 심층 검토에서 기존 보고서의 중요한 오류와 불완전한 설명을 수정했다.

### Correction 1 · `pipefail`은 더 이상 Bash-only가 아니다

기존 보고서는 `set -o pipefail`을 Bash 전용으로 분류했다. 이는 POSIX.1-2024 기준으로 잘못되었다.

POSIX.1-2024는 pipeline exit status를 `pipefail` option과 함께 정의하며, Rationale은 Austin Group Defect 789를 통해
`pipefail`이 추가되었다고 명시한다.

하지만 이 사실이 곧 모든 현재 `/bin/sh`가 같은 support를 제공한다는 뜻은 아니다. Debian dash는 0.5.12-7에서 upstream
`pipefail` patch를 받아들였지만, BusyBox ash source에서는 `pipefail` support가 build-time Bash compatibility option에
묶여 있는 상태다.

**Revised disposition:**

```text
pipefail
├── normative status: POSIX.1-2024
└── beginner runnable status: implementation/build support 확인 후 사용
```

따라서 `pipefail`을 “Bashism”으로 가르치지 않는다. 동시에 초급 core error handling을 `pipefail`에 의존시키지도 않는다.

### Correction 2 · dash의 `$'...'` 지원 상태를 deployment와 upstream으로 분리한다

POSIX.1-2024는 Dollar-Single-Quotes (`$'...'`)를 표준화했다. Debian unstable의 dash 0.5.12 계열 문서/패키지에서는 이
기능이 늦게 반영되었지만, Debian bug #989239 기록상 upstream dash 0.5.13.1에서는 2026-02-28 기준 수정이 확인되었다.

따라서 “dash는 `$'...'`를 지원하지 않는다”는 현재 일반화도 부정확하다.

정확한 설명은 다음과 같다.

```text
POSIX.1-2024: standardized
upstream dash 0.5.13.1: support confirmed
older/deployed dash 0.5.12 line: support may be absent
Debian /bin/sh policy today: POSIX.1-2017 + Debian-specific additions
```

이 사례는 Issue 8 adoption이 shell별 한 번의 전환이 아니라 **feature-by-feature, release-by-release**로 진행된다는 좋은
evidence다.

### Correction 3 · ShellCheck 결과도 versioned evidence다

ShellCheck latest tagged release는 v0.11.0(2025-08-03)이고, 현재 master changelog에는 POSIX.1-2024가 `$'...'`를
표준화했기 때문에 SC3003을 제거한다는 unreleased change가 기록되어 있다.

즉 같은 POSIX script라도 ShellCheck version에 따라 warning이 달라질 수 있다.

**Revised disposition:** future lab이 특정 ShellCheck output을 expected evidence로 사용한다면 version을 기록하거나
pin한다.

## Research Questions

이번 deep pass에서는 다음 질문을 검토했다.

- 2026년 현재 portable `sh` 교본의 normative 기준은 무엇인가?
- POSIX.1-2024에서 새로 표준화된 surface와 deployed `/bin/sh` 사이의 lag를 어떻게 다뤄야 하는가?
- quoting/expansion을 어떤 mental model로 설명해야 정확하면서도 초급자에게 과도하게 복잡하지 않은가?
- assignment, ordinary argument, redirection처럼 expansion context가 달라질 때 한 개의 단순 pipeline 모델이 어디까지
  유효한가?
- pipeline과 subshell이 variable state에 미치는 영향을 언제 가르쳐야 하는가?
- exit status, `&&`/`||`, `if`, loop, function, `set -e`, `pipefail`을 어떤 순서로 연결해야 하는가?
- function에서 `local`을 쓰지 않는 portable core는 어떻게 설명해야 하는가?
- syntax check, lint, multiple-shell execution은 각각 무엇을 증명하고 무엇을 증명하지 못하는가?
- 유명한 beginner material의 teaching pattern은 무엇을 재사용하고 어떤 dialect assumption은 버려야 하는가?

## Evidence Model

이 보고서는 source를 같은 authority로 취급하지 않는다.

### Tier A · Normative language authority

#### POSIX.1-2024 Shell Command Language

<https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>

shell operation, token recognition, quoting, expansion, redirection, simple commands, pipelines, lists, functions,
execution environment, exit status를 판단하는 최우선 source다.

#### POSIX.1-2024 Rationale

<https://pubs.opengroup.org/onlinepubs/9799919799/xrat/V4_xcu_chap01.html>

왜 특정 historical behavior가 유지되었는지, Issue 8에서 무엇이 추가되었는지, portability choice가 왜 그렇게
정의되었는지를 해석할 때 사용한다.

### Tier B · Deployed implementation and platform policy

#### Debian Policy 4.7.4.1

<https://www.debian.org/doc/debian-policy/ch-files.html>

Debian `/bin/sh` script가 현재 기대할 수 있는 baseline은 POSIX.1-2017에 Debian-specific additions를 더한 것이다. 그
additions에는 `local`, 특정 `echo -n`, `test -a/-o` behavior 등이 포함된다.

이것은 **Debian policy이지 cross-platform POSIX definition이 아니다**.

#### dash documentation and Debian bug history

<https://manpages.debian.org/unstable/dash/dash.1.en.html>

<https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=989239>

<https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1071238>

`$'...'`와 `pipefail`의 adoption timing이 서로 다르다는 점을 확인하는 evidence다. 한 implementation이 “Issue 8
지원”이라는 하나의 boolean으로 움직이지 않는다는 점이 중요하다.

#### Alpine / BusyBox ash

<https://wiki.alpinelinux.org/wiki/Shell_management>

Alpine Linux의 `/bin/sh`는 기본적으로 BusyBox ash에 연결된다. BusyBox ash source는 `$'...'`와 `pipefail` 등 일부
feature가 build-time Bash compatibility configuration에 따라 달라질 수 있음을 보여준다.

따라서 BusyBox라는 이름만 보고 feature support를 단정하지 않는다.

### Tier C · Implementation comparison

#### GNU Bash 5.3 Reference Manual

<https://www.gnu.org/software/bash/manual/bash.html>

Bash default behavior, `--posix`, `set -o posix`, `sh` invocation 차이를 확인한다. Bash는 comparison target이지 POSIX
`sh` definition의 owner가 아니다.

### Tier D · Static feedback

#### ShellCheck

<https://www.shellcheck.net/>

<https://github.com/koalaman/shellcheck/blob/master/CHANGELOG.md>

quoting, suspicious expansion, common semantic error, non-POSIX syntax을 찾는 feedback surface다. 표준 revision과
ShellCheck version에 따라 rule이 변할 수 있으므로 normative authority로 사용하지 않는다.

SC2086, SC2048/SC2068 같은 rule은 unquoted expansion과 `"$@"`의 실제 failure mode를 설명하는 좋은 secondary teaching
evidence지만, rule 자체를 표준 조문처럼 취급하지 않는다.

### Tier E · Pedagogy references

#### MIT Missing Semester 2026

<https://missing.csail.mit.edu/2026/course-shell/>

<https://missing.csail.mit.edu/2026/command-line-environment/>

arguments, streams, environment, return codes, signals를 연결된 execution model로 가르치는 점은 좋은 참고다. 반면
examples는 Bash를 명시적으로 사용하고 `[[ ... ]]`, process substitution, Bash strict-mode recipe 등 Bash-specific
assumptions를 포함한다.

따라서 **teaching move는 참고하고 dialect는 복제하지 않는다**.

#### Software Carpentry, The Unix Shell

<https://swcarpentry.github.io/shell-novice/>

초급자가 command를 예측하고 loop/script를 작은 단계로 실행해 보는 challenge 구조는 유용하다. 다만 material은 Bash를
기준으로 하며 일부 example은 quoting/portable scripting을 이 deck이 요구하는 수준보다 느슨하게 다룬다.

따라서 challenge design과 progressive practice는 참고하되 example code를 portable `sh` correctness의 authority로
사용하지 않는다.

#### Google Shell Style Guide

<https://google.github.io/styleguide/shellguide.html>

이 guide는 명시적으로 Bash-only policy이므로 syntax authority로 쓰지 않는다. 다만 shell을 small utility/simple wrapper
범위에 두고 복잡도가 커지면 structured language로 옮기라는 boundary는 이 deck의 scope discipline을 점검하는 useful
counterweight다.

## Finding 1 · `sh`, implementation, platform policy를 세 층으로 분리해야 한다

초급자는 `/bin/sh`, dash, Bash, BusyBox ash를 모두 “shell”이라는 한 범주로 보기 쉽다. portable scripting에서는 최소 다음
층을 분리해야 한다.

```text
language contract: POSIX shell language revision
        ↓
implementation/build: dash / Bash POSIX mode / BusyBox ash config / ...
        ↓
platform policy: Debian /bin/sh contract, Alpine defaults, target environment
```

예를 들어 Debian Policy는 `local`을 `/bin/sh`에 요구하지만 POSIX.1-2024의 portable function model은 `local` variable을
요구하지 않는다. Debian에서 동작한다는 사실을 POSIX language guarantee로 끌어올리면 안 된다.

### Textbook implication

교본에서 portability claim을 할 때 “POSIX”라는 한 단어 대신 필요하면 다음을 분리한다.

- language revision
- feature가 old/core인지 newly standardized인지
- 실제 runtime implementation
- platform-specific contract

## Finding 2 · shell operation을 먼저 보여주되 beginner model임을 명시해야 한다

POSIX.1-2024의 shell operation은 대략 다음 흐름을 가진다.

```text
read source
→ recognize tokens
→ parse commands
→ perform quote/word processing and expansions
→ perform redirections
→ execute command/function
→ collect exit status
```

이 순서는 shell syntax가 단순 문자열 substitution이 아니라는 것을 이해시키는 데 매우 강하다.

하지만 초급 mental model을 모든 grammar context에 똑같이 적용하면 또 다른 오류를 만든다. simple command에서는 assignment
word와 redirection이 일반 argument word와 다른 processing 규칙을 가진다.

따라서 교본은 두 단계로 가르치는 것이 좋다.

1. **ordinary argument context**에서 expansion이 final argument vector를 만드는 과정을 먼저 완전히 익힌다.
2. 이후 assignment/redirection/declaration context가 같은 source word를 다르게 처리할 수 있음을 추가한다.

이렇게 하면 첫 장부터 specification의 모든 예외를 쏟아붓지 않으면서도 잘못된 보편 규칙을 심지 않는다.

## Finding 3 · 첫 calibration slice는 여전히 final argv가 가장 좋다

초급자가 가장 자주 만드는 category error는 source에 보이는 text가 그대로 한 argument가 된다고 생각하는 것이다.

```sh
program $value
program "$value"
```

두 line은 단순 style 차이가 아니다. unquoted expansion은 field splitting과 pathname expansion에 참여할 수 있고, quoted
expansion은 argument boundary를 보존한다.

따라서 첫 slice에서 반드시 관찰할 값은 pretty output보다 다음이다.

```text
argc
argv[0]
argv[1]
...
```

### Calibration cases

- ordinary literal
- space를 포함한 variable
- empty string
- `*` 같은 glob character를 포함한 variable
- quoted/unquoted parameter expansion
- later transfer: `"$@"`

### Important refinement

교본 설명에서 “quote하면 항상 safe” 같은 추상적 slogan보다
**어떤 expansion stage가 억제되고 어떤 field boundary가 남는가**를 설명한다.

ShellCheck SC2086와 SC2048/SC2068은 이 failure mode를 learner-friendly example로 보여주므로 연습 설계에 참고할 수 있다.
단, 실제 설명의 authority는 POSIX semantics다.

## Finding 4 · assignment context는 ordinary argument context와 다르다

`name=value`가 assignment word로 인식될 때의 expansion은 ordinary command argument와 같지 않다. 또한 `export` 같은
declaration utility 뒤의 assignment는 assignment context를 가진다.

이 차이는 다음과 같은 code를 이해할 때 중요하다.

```sh
value='a b'
x=$value
printf '<%s>\n' "$x"
```

초급자가 “unquoted `$value`는 언제나 split된다”고 암기하면 assignment context에서 틀린 model을 갖게 된다.

### Textbook implication

Unit 1에서는 ordinary argument context를 기준으로 quote/field splitting을 가르친다. Unit 2에서 variable assignment와
environment를 다룰 때 “expansion behavior는 grammar context에 따라 달라진다”는 첫 예외를 명시적으로 연결한다.

## Finding 5 · command substitution은 string capture가 아니라 lossy boundary가 있다

`$(...)`는 subshell environment에서 command를 실행하고 output의 trailing newline sequence를 제거한다. 그래서 command
output을 shell variable에 넣는 것은 arbitrary byte stream을 손실 없이 저장하는 일반 mechanism이 아니다.

이 사실은 다음 beginner misconception을 막는다.

> “stdout을 variable에 넣으면 원래 output이 그대로 보존된다.”

### Textbook implication

초급 core에서는 `$(...)`를 backtick form보다 우선한다. Rationale도 nested/complex substitution에서 backticks를 권장하지
않는다.

worked example은 command substitution으로 얻은 값의 trailing newline이 사라지는 작은 counterexample을 하나 포함하는 것이
좋다. binary/NUL boundary는 심화 note로 두고 core progression을 방해하지 않는다.

## Finding 6 · `"$@"`는 forwarding invariant로 가르쳐야 한다

`"$@"`는 double-quoted context에서 positional parameter 각각의 field boundary를 보존하는 특수한 semantics를 가진다.

따라서 `$1`, `$2` 암기보다 다음 invariant가 더 중요하다.

```text
caller argv
→ wrapper/function
→ "$@"
→ callee argv

argument boundaries preserved
```

검증 case에는 반드시 다음을 포함한다.

- empty argument
- spaces를 포함한 argument
- wildcard character를 literal로 포함한 argument
- leading `-` argument

마지막 case는 script가 다른 utility로 argument를 전달할 때 `--` 같은 utility-level option boundary가 별개의 문제라는
것도 보여줄 수 있다.

## Finding 7 · exit status가 shell control flow의 공통 상태다

다음 주제는 별개의 문법 family가 아니라 같은 state의 확장으로 가르치는 것이 좋다.

```text
command status
→ $?
→ && / || / !
→ test / [ ]
→ if
→ while / until
→ function status
→ explicit failure handling
```

`if`를 boolean expression evaluator로 설명하기 전에 “command를 실행하고 status를 본다”를 확립해야 한다.

### Additional misconception · `&&`와 `||` precedence

POSIX shell에서 `&&`와 `||`는 **동일 precedence이며 left-associative**다. C, JavaScript 등에서 `&&`가 `||`보다 높은
precedence인 것과 다르다.

따라서 다음처럼 mixed chain을 expression처럼 읽는 습관을 일찍 교정할 가치가 있다.

```sh
command1 && command2 || command3
```

초급 material에서는 clever chain보다 `if`나 명시적인 grouping을 선호하고, mixed chain은 tracing problem으로 사용한다.

## Finding 8 · pipeline은 byte flow와 shell-state boundary를 동시에 가진다

pipeline을 `stdout → stdin` diagram만으로 설명하면 절반만 설명한 것이다.

POSIX.1-2024에서는 multi-command pipeline의 각 command가 subshell environment에 놓이며, extension으로 implementation이
일부 또는 전체 command를 current environment에서 실행할 수도 있다.

따라서 다음 형태가 parent variable을 업데이트한다고 portable하게 가정하면 안 된다.

```sh
producer | while IFS= read -r line; do
    count=$((count + 1))
done
```

implementation에 따라 loop body가 current shell에서 실행될 수 있어 보이는 경우가 있어도 portable script는 그
persistence에 의존하지 않아야 한다.

### Textbook implication

Unit 2에서 pipeline data flow를 소개할 때 “process/data flow”와 “shell state flow”를 구분한다. Unit 4 loop에서
pipeline-fed loop를 다룬다면 이 portability trap을 반드시 되짚는다.

## Finding 9 · `pipefail`은 status model 뒤에 와야 한다

POSIX.1-2024는 `pipefail`을 표준화했지만, 교육 순서는 바뀌지 않는다.

먼저 기본 pipeline status를 이해해야 `pipefail`이 무엇을 바꾸는지 이해할 수 있다.

```text
pipeline processes
→ each command status
→ default pipeline status
→ pipefail-selected status
```

또한 deployment/build support를 확인해야 한다.

### Textbook implication

- `pipefail`을 Bash-only라고 부르지 않는다.
- Unit 2/3의 conservative runnable core는 `pipefail` 없이 이해 가능하게 만든다.
- Unit 6 portability section에서 POSIX.1-2024 adoption case study로 다룬다.
- target runtime에서 support를 확인한 뒤 optional experiment로 사용한다.

## Finding 10 · redirection은 file-descriptor connection을 순서대로 바꾸는 동작이다

redirection은 punctuation catalog가 아니다. 최소한 다음 state model을 사용한다.

```text
command
├── fd 0 → stdin source
├── fd 1 → stdout destination
└── fd 2 → stderr destination
```

simple command processing과 pipeline 연결에는 order가 있다. pipeline의 standard-stream connection이 먼저 정해지고
command의 explicit redirection이 이를 바꿀 수 있다.

따라서 다음 같은 비교를 output 암기 대신 descriptor state tracing으로 다룬다.

```sh
command >out 2>&1
command 2>&1 >out
```

실제 example에서는 각 redirection 뒤의 fd 1/fd 2 target을 단계별로 그리게 한다.

## Finding 11 · function은 새 local scope보다 current shell state를 먼저 가르쳐야 한다

POSIX function은 다음 form을 core로 둔다.

```sh
name() {
    commands
}
```

function invocation 동안 positional parameters는 function arguments로 바뀌고, function이 끝나면 호출자의 positional
parameter state가 복원된다. 반면 일반 variable은 Python/JavaScript function local scope처럼 자동 격리되지 않는다.

`local`은 널리 구현되고 Debian Policy에서는 `/bin/sh` addition으로 요구되지만 POSIX portable guarantee가 아니다.

### Textbook implication

Unit 5는 `local`을 core code에 사용하지 않는다. 대신 다음을 가르친다.

- inputs: positional parameters
- outputs: stdout 또는 explicit shared variable mutation, 의도에 따라 구분
- status: last command / explicit `return`
- state risk: function body의 assignment가 caller shell state를 바꿀 수 있음

그 뒤 `local`을 implementation/platform extension example로 비교할 수 있다.

## Finding 12 · `set -e`는 status reasoning을 대체하지 못한다

초급 error handling을 `set -e` recipe로 시작하면 shell의 실제 control semantics를 가린다.

POSIX `set` application guidance도 function invocation이 conditional context에 놓이는 경우 `-e`가 function body에서
기대와 다르게 동작할 수 있음을 경고한다.

따라서 교본은 먼저 다음을 가르친다.

- 어떤 command failure가 expected인가?
- 어떤 failure를 caller가 fatal로 볼 것인가?
- `if`, `&&`, `||`, `case`, explicit `exit`/`return` 중 어떤 control이 의도를 가장 잘 표현하는가?
- cleanup이 필요한 resource가 있는가?

그 뒤 `set -e`를 **convenience option + context-sensitive behavior**로 분석한다.

`set -euo pipefail`을 의미를 이해하기 전의 주문처럼 제시하지 않는다. 특히 `pipefail`은 현재 POSIX이지만 support
baseline은 별도로 확인한다.

## Finding 13 · `trap`은 cleanup responsibility와 연결해야 한다

POSIX.1-2024 `trap`은 `EXIT`와 symbolic signal names를 지원하고, trap action이 끝난 뒤 `$?`를 trap 실행 전 값으로
복원하도록 정의한다.

초급 교본에서는 signal catalog보다 resource lifetime에 연결하는 편이 좋다.

```text
resource acquired
→ work
→ normal/failure/signal path
→ cleanup responsibility
```

symbolic names (`INT`, `TERM`, `EXIT`)을 우선하고 numeric signal 값은 portable core에서 피한다.

## Finding 14 · predictable output에는 `printf`를 기본으로 둔다

`echo`는 historical option/backslash behavior 차이 때문에 portable formatted output을 가르치는 기본 도구로 부적합하다.

교본의 predictable output은 `printf`를 기본으로 사용한다. `echo` 자체를 금지할 필요는 없지만 escape 처리나 option
ambiguity가 의미 있는 예제에서는 `printf`를 선택한다.

## Finding 15 · `test`에서는 복합 expression을 command composition으로 푸는 편이 낫다

`[ ... ]`는 syntax punctuation처럼 보여도 실제로는 `test` utility form이다.

복합 condition을 한 개의 `[ ... ]` 안에서 `-a`/`-o`로 쌓기보다 다음처럼 shell control operators로 composition하는 편이
읽기 쉽고 ambiguity도 줄인다.

```sh
if [ -f "$path" ] && [ -r "$path" ]; then
    ...
fi
```

Debian `/bin/sh`는 `test -a/-o`를 별도 policy addition으로 보장하지만, 그것을 portable curriculum의 이유로 삼지 않는다.

## Finding 16 · shebang은 shell grammar와 executable dispatch를 분리해 설명한다

POSIX Shell Command Language는 source의 첫 줄이 `#!`로 시작하는 경우 shell-language 관점 결과를 unspecified로 둔다.
Rationale은 `#!`를 interpreter selection을 위한 historical extension 영역으로 설명한다.

현실적으로 executable script에서 `#!/bin/sh`는 매우 중요하므로 제외하지 않는다. 다만 다음 두 층을 구분한다.

```text
#!/bin/sh   → OS/runtime-facing interpreter dispatch convention
script body → shell command language
```

그리고 다음 둘이 언제 같은 interpreter path를 거치지 않을 수 있는지 비교한다.

```sh
./script.sh
sh script.sh
```

## Finding 17 · portability는 test result가 아니라 bounded claim이다

다음 중 어느 것도 단독으로 “portable POSIX script”를 증명하지 않는다.

- `sh -n` success
- ShellCheck clean
- dash에서 success
- Bash `--posix`에서 success
- 한 Linux distribution에서 success

각 evidence가 답하는 질문이 다르다.

| Evidence | 잘 답하는 질문 | 증명하지 못하는 것 |
| --- | --- | --- |
| `sh -n` | parser가 현재 shell에서 source를 받아들이는가 | runtime semantics, portability |
| ShellCheck `-s sh` | known pattern/Bashism warning이 있는가 | POSIX conformance, runtime behavior |
| one-shell execution | 그 implementation/build에서 observed behavior가 맞는가 | 다른 shell/platform behavior |
| multi-shell matrix | selected implementations 사이 차이가 있는가 | 모든 conforming implementation |
| POSIX text | standardized semantics가 무엇인가 | deployed implementation adoption |

**Key rule:** implementation matrix는 portability를 “증명”하기보다 잘못된 assumption을 **반증하기 위한 도구**로
사용한다.

## Finding 18 · 좋은 beginner material의 pedagogy와 dialect는 분리해서 평가해야 한다

심층 검토에서 MIT Missing Semester, Software Carpentry, Google Shell Style Guide를 같은 기준으로 비교하면 한 가지 패턴이
분명하다.

- Missing Semester는 arguments/streams/environment/status를 연결하는 conceptual sequence가 강하지만 Bash-specific code가
  많다.
- Software Carpentry는 prediction/challenge와 incremental practice가 강하지만 Bash context와 일부 느슨한 quoting
  example이 있다.
- Google Style Guide는 maintainability boundary가 분명하지만 아예 Bash-only를 전제로 한다.

즉 유명한 material의 **교육적 성공**은 그 code가 portable POSIX reference라는 뜻이 아니다.

### Textbook implication

외부 tutorial을 참고할 때 다음 두 질문을 별도로 평가한다.

```text
pedagogy: 이 설명/연습 구조가 학습을 돕는가?
dialect: 이 code와 semantics가 우리의 POSIX target에 맞는가?
```

이 분리가 없으면 잘 설계된 Bash exercise를 portable `sh` exercise로 그대로 복사하는 오류가 생긴다.

## Feature Classification for the Textbook

### A · Conservative portable core

초급 runnable path에서 우선 사용한다.

- simple commands
- single/double quotes and backslash
- parameter expansion의 기본 form
- `$(...)` command substitution
- arithmetic expansion `$((...))`
- `"$@"`
- redirection and pipelines
- `test` / `[ ]`
- `if`, `case`, `for`, `while`, `until`
- POSIX function form `name() { ...; }`
- `shift`, `getopts`
- symbolic `trap` names and `EXIT`
- `printf`

각 example은 실제 target runtime에서 검증해야 하지만 curriculum은 이 영역을 기본 언어로 삼는다.

### B · POSIX.1-2024 but adoption-sensitive

표준이지만 current deployment support를 별도 확인한다.

- `$'...'`
- `pipefail`
- 기타 Issue 8 추가 surface가 실습에 필요해지는 경우

이 category는 “Bash-only”가 아니다. 반대로 “POSIX니까 어디서나 지금 동작한다”도 아니다.

### C · Common extension / platform-specific allowance

portable core에서 사용하지 않는다.

- `local`
- `source` instead of `.`
- `[[ ... ]]`
- arrays
- process substitution
- Bash parameter replacement extensions
- `function name { ...; }`
- BusyBox build-option-dependent behavior를 universal assumption으로 사용하기

## Pedagogy Review

### What to reuse

세부 syntax보다 다음 teaching move가 여러 좋은 material에서 반복된다.

```text
predict
→ expose hidden state
→ execute
→ compare prediction with evidence
→ explain mechanism
→ vary one condition
→ repair
→ transfer
```

shell에서 “hidden state”는 다음일 수 있다.

- final argv field boundaries
- current environment vs child/subshell environment
- fd 0/1/2 targets
- exit status
- positional parameters
- cleanup ownership

### What not to copy blindly

- Bash-specific syntax를 portable `sh` example로 재사용하기
- filenames에 space가 없을 것이라고 가정해 quoting 문제를 피하기
- `set -euo pipefail`을 semantics 설명보다 먼저 제시하기
- `[[ ... ]]`를 `[ ... ]`의 portable safer replacement처럼 가르치기
- tool warning을 language-lawyer answer처럼 사용하기

## Recommended Curriculum Architecture

### Unit 0 · A Script Is an Executed Command Language

- executable/interpreter boundary
- `#!/bin/sh` vs `sh script.sh`
- comments, simple commands
- `printf`
- first exit-status observation

Unit 0의 목적은 command catalog가 아니라 **source를 shell이 실행한다**는 model을 고정하는 것이다.

### Unit 1 · From Source Words to Final Arguments

- tokens, words, final argv의 차이
- single/double/unquoted forms
- parameter expansion
- `$(...)` command substitution
- field splitting
- pathname expansion
- command substitution trailing-newline boundary
- argument-boundary observation

먼저 ordinary argument context만 완전히 이해시키고 assignment context 예외는 Unit 2로 넘긴다.

### Unit 2 · Variables, Environments, Redirection, and Pipelines

- assignment context
- shell variable vs exported environment
- temporary command environment
- positional/special parameters
- fd 0/1/2
- redirection order
- pipeline byte flow
- subshell/current-environment boundary
- default pipeline status

### Unit 3 · Decisions Are Exit Status

- `$?`
- `&&`, `||`, `!`
- equal precedence / left associativity of `&&` and `||`
- `test` / `[ ]`
- `if`, `case`
- avoid dense `test -a/-o` expressions

### Unit 4 · Repetition and Argument Processing

- `for`, `while`, `until`
- `break`, `continue`
- `"$@"`, `$#`, `shift`
- empty/space/glob/leading-dash arguments
- pipeline-fed loop state portability trap
- `IFS= read -r` only if line input becomes part of an exercise

### Unit 5 · Functions and Small Script Structure

- POSIX function form
- positional parameter replacement/restoration during calls
- shared shell state
- `export`
- function exit status / `return`
- `getopts`
- `local` as non-portable extension comparison, not core requirement

### Unit 6 · Failure, Cleanup, and Portability

- expected vs fatal failure
- explicit status handling
- `trap` and resource lifetime
- `sh -n`
- `set -x`
- ShellCheck versioned feedback
- Bashism repair
- POSIX.1-2024 adoption case studies: `$'...'`, `pipefail`
- `set -e` behavior after status model is established

### Unit 7 · Capstone: A Portable Automation Script

- requirements → inputs/outputs/failure conditions
- argument contract
- stream/fd contract
- state mutation boundary
- cleanup contract
- incremental implementation
- syntax/lint/runtime evidence
- bounded portability claim

## First Calibration Slice

첫 implementation slice는 여전히 **source text → final argv**가 가장 높은 information gain을 가진다.

단, deep review 결과 다음처럼 더 정밀하게 정의한다.

```text
Scope: ordinary argument context only

source line
→ identify words
→ perform relevant expansion
→ predict final argc/argv
→ observe exact argument boundaries
→ vary whitespace / empty / glob input
→ compare quoted vs unquoted
→ explain field-boundary change
→ repair one broken case
→ transfer to a new argument value
```

assignment context, pipeline state, functions까지 한 slice에 넣지 않는다. 첫 mental model을 검증한 뒤 후속 unit에서
context-sensitive rules를 추가한다.

## Practice Types to Prefer

- **Prediction:** 이 source line은 command에 몇 fields를 전달하는가?
- **Tracing:** expansion 전후 field boundary를 표시한다.
- **Comparison:** `$@`, `"$@"`, `$*`, `"$*"`의 결과를 구분한다.
- **State tracing:** command가 current shell, child environment, subshell 중 어디의 state를 바꾸는가?
- **FD tracing:** 각 redirection 뒤 fd 1과 fd 2가 어디를 가리키는가?
- **Control tracing:** mixed `&&`/`||` chain에서 실제 실행되는 command와 final status를 추적한다.
- **Debugging:** whitespace/glob/pipeline-subshell 때문에 깨지는 script의 원인을 분류한다.
- **Repair:** Bashism 또는 platform-specific assumption을 최소 변경으로 제거한다.
- **Transfer:** wrapper/function에서 argument vector를 보존한다.
- **Synthesis:** small automation의 inputs, outputs, state, failure, cleanup contract를 먼저 정의한 뒤 구현한다.

완성된 script를 그대로 타이핑하는 것은 competence evidence로 사용하지 않는다.

## Validation Strategy for Future Slices

각 runnable slice는 필요한 수준에서 다음 층을 구분한다.

### 1. Specification review

- example의 intended semantics가 POSIX source와 일치하는가?
- Issue 8/newly standardized surface인가?
- implementation extension을 standard처럼 말하고 있지 않은가?

### 2. Syntax

```sh
sh -n script.sh
```

현재 interpreter가 source를 parse할 수 있는지만 확인한다.

### 3. Static feedback

```sh
shellcheck -s sh script.sh
```

ShellCheck version을 함께 기록한다. warning absence를 conformance proof로 해석하지 않는다.

### 4. Runtime evidence

concept에 맞는 state를 직접 관찰한다.

- argument boundary
- stdout/stderr separation
- exit status
- environment mutation
- cleanup effect

### 5. Selected implementation comparison

가능한 runtime에서 system `/bin/sh`, dash, Bash POSIX mode, BusyBox ash 등 중 실제 available target을 비교한다.

목적은 “모든 POSIX shell에서 검증했다”가 아니라 **assumption divergence를 빨리 발견하는 것**이다.

### 6. Claim gate

실제로 검증하지 않은 platform/build까지 portability claim을 확장하지 않는다.

## Risks and Open Questions

### Risk 1 · POSIX.1-2024 adoption is feature-granular

`pipefail`과 `$'...'`만 봐도 같은 dash family에서 adoption timing이 다르다.

**Disposition:** 새 Issue 8 feature마다 별도 support evidence를 확인한다. “Issue 8 supported”라는 coarse label로
대신하지 않는다.

### Risk 2 · BusyBox behavior can be build-config dependent

BusyBox ash source에서 일부 compatibility feature는 build-time option에 묶여 있다.

**Disposition:** BusyBox version 문자열만으로 capability를 추정하지 않는다. future runtime test에서는 실제 binary
behavior를 확인한다.

### Risk 3 · Platform policy can exceed POSIX

Debian `/bin/sh`는 `local` 등 POSIX.1-2017 이상의 addition을 요구한다.

**Disposition:** platform allowance를 portable language feature로 승격하지 않는다.

### Risk 4 · lint rules lag or lead standard adoption

ShellCheck master와 tagged release의 POSIX.1-2024 handling이 다를 수 있다.

**Disposition:** expected lint result를 학습 evidence로 고정할 때 tool version을 기록한다.

### Risk 5 · exact implementation matrix is not yet chosen

현재 curriculum은 implementation-neutral하다. repository CI에서 실제로 어떤 shells를 cheap하게 실행할 수 있는지는 first
runnable slice 단계에서 확인해야 한다.

**Disposition:** playground/validation을 만들기 전 target matrix를 최소 비용으로 정한다. curriculum 자체를 특정 distro에
종속시키지 않는다.

### Open question · how far to teach POSIX utilities

portable shell script의 correctness는 shell grammar뿐 아니라 `test`, `printf`, `read`, `getopts`, `mktemp` 같은 utility
contract에도 영향을 받는다. 모든 utility portability를 한 deck에서 다루면 범위가 급격히 넓어진다.

**Disposition:** shell-language competence에 직접 필요한 standard utility만 해당 unit에서 최소 범위로 가르치고, general
Unix utility portability는 별도 주제로 확장하지 않는다.

## Review Against the Textbook Contract

이번 research 방향은 다음 이유로 textbook foundation에 적합하다.

- **progression:** final argv → environment/state → fd/data flow → exit control → iteration → functions →
  failure/cleanup 순으로 dependency가 있다.
- **mechanism:** syntax 이름보다 hidden state와 transformation을 중심에 둔다.
- **misconceptions:** `sh=Bash`, source text=argv, `if=boolean expression`, pipeline=state-preserving, `local=portable`,
  `set -e=always abort`, lint=proof 같은 plausible wrong models을 명시적으로 다룬다.
- **practice:** prediction/tracing/debugging/transfer가 가능한 observable surface를 정의했다.
- **evidence fidelity:** POSIX normative text, implementation evidence, platform policy, lint feedback를 같은
  authority로 섞지 않는다.
- **scope:** shell 전체 ecosystem이나 production shell architecture로 확장하지 않는다.

## Review History

### Deep loop 1 · broaden and falsify

- POSIX.1-2024 normative text와 Rationale를 다시 대조했다.
- `pipefail`의 기존 분류 오류를 발견했다.
- `$'...'` dash support를 upstream/deployed package로 분리했다.
- Debian `/bin/sh` policy가 POSIX language contract와 다른 층임을 확인했다.

**Result:** baseline portability model 수정.

### Deep loop 2 · mechanism and curriculum pressure test

- assignment context가 ordinary argument context와 다름을 반영했다.
- command substitution trailing-newline loss를 추가했다.
- pipeline subshell/current-environment extension을 curriculum risk로 올렸다.
- `&&`/`||` equal precedence를 explicit misconception으로 추가했다.
- function scope와 `local` extension 경계를 강화했다.

**Result:** Unit 1–6 responsibility를 정밀화하고 첫 calibration slice를 더 작게 제한.

### Deep loop 3 · evidence and validation pressure test

- ShellCheck stable/master revision 차이를 확인했다.
- BusyBox build configuration dependency를 확인했다.
- one-shell execution과 multi-shell matrix의 evidence boundary를 재정의했다.
- implementation matrix를 proof가 아니라 disconfirmation 도구로 규정했다.

**Result:** future playground validation claim을 더 보수적이고 검증 가능하게 변경.

### Deep loop 4 · pedagogy and scope pressure test

- MIT Missing Semester, Software Carpentry, Google Shell Style Guide를 pedagogy와 dialect라는 두 축으로 다시 비교했다.
- ShellCheck rule examples를 normative source가 아니라 misconception/feedback source로 한정했다.
- 유명 tutorial의 code를 그대로 가져오는 대신 exercise structure만 선택적으로 재사용한다는 원칙을 명시했다.
- shell이 small glue/automation이라는 scope boundary가 curriculum goal과 충돌하지 않는지 다시 확인했다.

**Result:** source popularity와 syntax authority를 분리하고, textbook scope가 tool enthusiasm 때문에 확장되지 않도록
보강했다.

## Research Conclusion

기초 POSIX `sh` 교본은 다음 네 개의 model을 반복해서 강화하는 것이 가장 좋다.

```text
1. source word → expansion/context → final argv
2. command → exit status → control-flow decision
3. fd connection → stream/data flow
4. current shell / command / subshell → state mutation boundary
```

이 네 model이 있으면 quoting, variables, arguments, redirection, pipelines, conditions, loops, functions, error
handling을 독립적인 문법 목록이 아니라 하나의 작은 execution language로 연결할 수 있다.

현재 가장 중요한 build decision은 유지한다. 전체 textbook을 먼저 채우지 않는다. 첫 implementation은
**ordinary argument context의 `source text → final argv` calibration slice** 하나를 설명, worked reasoning, prediction,
runtime observation, repair, transfer까지 완성한 뒤 review한다.

## Public References

### Normative

- The Open Group, POSIX.1-2024, Shell Command Language:
  <https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>
- The Open Group, POSIX.1-2024, Rationale for Shell and Utilities:
  <https://pubs.opengroup.org/onlinepubs/9799919799/xrat/V4_xcu_chap01.html>

### Implementation / platform

- GNU, Bash Reference Manual 5.3:
  <https://www.gnu.org/software/bash/manual/bash.html>
- Debian, dash(1) manual:
  <https://manpages.debian.org/unstable/dash/dash.1.en.html>
- Debian Bug #989239, dash Dollar-Single-Quotes support:
  <https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=989239>
- Debian Bug #1071238, dash `pipefail` support:
  <https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1071238>
- Debian Policy 4.7.4.1, Scripts:
  <https://www.debian.org/doc/debian-policy/ch-files.html>
- Alpine Linux, Shell management:
  <https://wiki.alpinelinux.org/wiki/Shell_management>
- BusyBox ash source:
  <https://github.com/mirror/busybox/blob/master/shell/ash.c>

### Static analysis

- ShellCheck:
  <https://www.shellcheck.net/>
- ShellCheck changelog:
  <https://github.com/koalaman/shellcheck/blob/master/CHANGELOG.md>
- ShellCheck SC2086:
  <https://www.shellcheck.net/wiki/SC2086>
- ShellCheck SC2048 / SC2068:
  <https://www.shellcheck.net/wiki/SC2048>
  <https://www.shellcheck.net/wiki/SC2068>

### Pedagogy / scope comparison

- MIT Missing Semester 2026, Introduction to the Shell:
  <https://missing.csail.mit.edu/2026/course-shell/>
- MIT Missing Semester 2026, Command-line Environment:
  <https://missing.csail.mit.edu/2026/command-line-environment/>
- Software Carpentry, The Unix Shell:
  <https://swcarpentry.github.io/shell-novice/>
- Google Shell Style Guide:
  <https://google.github.io/styleguide/shellguide.html>
