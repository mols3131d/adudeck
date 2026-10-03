# POSIX sh Scripting

`programming-posix_sh`는 `/bin/sh` 계열에서 통하는 **기초 shell scripting 문법과 실행 의미**를 배우는 deck이다.

목표는 문법 조각을 외우는 것이 아니라, shell이 source text를 읽어 command와 arguments를 만들고 redirection을 적용한 뒤
program을 실행하고 exit status를 다음 control flow에 전달하는 과정을 추적할 수 있게 되는 것이다.

## Learner Goal

작은 automation script를 직접 읽고, 작성하고, 수정하고, 디버깅할 수 있다. 특히 quoting이나 expansion 때문에 실제
arguments가 어떻게 달라지는지, command의 성공과 실패가 다음 실행 흐름을 어떻게 바꾸는지 설명할 수 있어야 한다.

## Learner Prerequisites

이 deck은 다음 기초를 이미 안다고 가정한다.

- terminal과 shell이 같은 것이 아니라는 점
- current working directory와 absolute/relative path
- command를 실행하고 기본적인 option과 argument를 전달하는 방법
- stdin, stdout, stderr의 역할
- command가 exit status를 반환한다는 사실

이 내용은 필요한 지점에서 짧게 연결하지만 다시 하나의 입문 command-line 교본처럼 전개하지 않는다.

## Learning Scope

이 deck의 중심은 **portable POSIX shell command language**다.

다룬다.

- shell script의 실행 경계, comment, simple command
- word, quoting, parameter expansion, command substitution, arithmetic expansion
- field splitting과 pathname expansion이 argument 목록에 미치는 영향
- shell variable, environment variable, assignment, `export`
- positional parameters와 special parameters: `$0`, `$#`, `$?`, `"$@"` 등
- redirection, pipeline, command list와 exit status의 결합
- `test` / `[ ]`, `if`, `case`
- `for`, `while`, `until`, `break`, `continue`
- POSIX function과 function의 argument/exit-status 동작
- `shift`, 기본적인 `getopts`, 작은 CLI script 구성
- `trap`의 기초와 정상 종료/실패 시 정리 책임
- `sh -n`, `set -x`, ShellCheck를 이용한 syntax/portability 피드백
- 작은 portable script를 읽고 설명하고 고치는 통합 연습

기본 범위에서는 다루지 않는다.

- Bash array, `[[ ... ]]`, process substitution, `function` keyword처럼 Bash에 종속적인 문법
- interactive shell customization, job control, prompt configuration
- `sed`, `awk`, regular expression 자체의 심화 학습
- 대규모 shell application architecture
- security hardening 전체, privileged shell programming
- `set -e` 같은 option을 이해 없이 붙이는 이른바 "strict mode" recipe

## Authority and Portability Boundary

언어 의미의 규범 기준은 **POSIX.1-2024 Shell Command Language**다.

- POSIX.1-2024: <https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>
- GNU Bash 5.3 manual은 Bash 구현과 POSIX mode의 차이를 확인하는 보조 자료로 사용한다.
- ShellCheck는 정적 피드백 도구이며 표준 그 자체로 취급하지 않는다.

POSIX.1-2024에 새로 포함된 문법이라도 실제 배포된 `sh` 구현의 지원이 늦을 수 있다. 따라서 이 deck은 **설명 기준은
POSIX.1-2024로 유지하되, 초급 runnable core는 널리 구현된 보수적인 공통 부분을 우선**한다. 새로운 Issue 8 기능이 실제
호환성에 영향을 주는 경우에는 별도로 표시하고 실행 환경에서 확인한다.

예시는 기본적으로 `#!/bin/sh`를 사용하되, shebang은 shell grammar 자체가 아니라 executable script를 시작하는 운영체제
관례라는 경계를 함께 설명한다.

## Core Mental Model

이 deck 전체에서 다음 실행 모델을 반복해서 사용한다.

```text
source text
→ token recognition
→ parsing
→ word expansion
→ redirection
→ command/function execution
→ exit status
→ next control-flow decision
```

특히 `word expansion`은 단순 문자열 치환으로 설명하지 않는다.

```text
source word
→ parameter / command / arithmetic expansion
→ field splitting
→ pathname expansion
→ quote removal
→ final argv fields
```

학습자는 최종 출력만 보는 대신 **어떤 words가 몇 개의 arguments가 되었는지**를 추적한다. 이 모델이 quoting,
`"$@"`, globbing, command substitution, 조건식의 많은 실수를 하나의 원인으로 연결한다.

## Learning Outcomes

완료 후 학습자는 다음을 할 수 있어야 한다.

1. shell source 한 줄이 token, word expansion, redirection을 거쳐 어떤 command와 argument 목록으로 실행되는지 설명한다.
2. single/double quote와 unquoted expansion의 차이를 이용해 filename과 arbitrary string을 안전하게 argument로 전달한다.
3. variable과 parameter expansion을 사용하고 unset/null 값이 control flow에 어떤 영향을 줄 수 있는지 판단한다.
4. `$#`, `$?`, `"$@"`, `shift`를 이용해 script argument를 보존하면서 처리한다.
5. redirection과 pipeline을 stdout/stderr 및 exit status의 data flow로 설명한다.
6. `if`, `case`, `for`, `while`, `until`을 exit-status 기반 control flow로 작성하고 추적한다.
7. function의 positional parameters, variable/environment 경계, 반환되는 exit status를 설명한다.
8. `sh -n`, execution trace, ShellCheck 결과를 구분해 syntax error와 semantic/portability 문제를 진단한다.
9. Bash 전용 문법이 섞인 작은 script를 portable `sh` 범위로 고치고 왜 고쳤는지 설명한다.
10. 파일과 command를 조합하는 작은 automation script를 독립적으로 설계하고 동작을 검증한다.

## Concept Dependencies

```text
script execution boundary
        ↓
words + quoting
        ↓
expansion → fields → argv
        ↓
variables + positional parameters
        ↓
redirection + pipeline + exit status
        ↓
conditional control flow
        ↓
iteration + argument processing
        ↓
functions + script organization
        ↓
cleanup + portability + debugging
        ↓
integrated script
```

exit status는 조건문 장에서 처음 등장하는 boolean 대체물이 아니다. 첫 command부터 관찰하고, 이후 pipeline, `&&`/`||`,
`if`, loop, function으로 같은 상태 모델을 확장한다.

## Planned Learning Units

아래는 curriculum architecture다. 아직 chapter file을 미리 만들지 않는다.

### Unit 0 · A Script Is an Executed Command Language

script 실행 경계, `#!/bin/sh`, comment, simple command, `printf`, exit status를 다룬다. source file을 실행하는 것과
`sh script.sh`로 interpreter에 전달하는 것을 구분한다.

### Unit 1 · From Source Words to Arguments

quoting과 expansion을 deck의 핵심 mental model로 확립한다. unquoted/double-quoted parameter expansion, command
substitution, field splitting, pathname expansion을 비교하고 최종 `argv`를 예측한다.

### Unit 2 · Variables, Parameters, and Command Data Flow

assignment, environment, `export`, positional/special parameters, redirection, pipeline, lists를 하나의 실행 상태와 data-flow
관점으로 연결한다.

### Unit 3 · Decisions Are Exit Status

`test` / `[ ]`, `if`, `case`, `&&`, `||`, `!`를 다룬다. 문자열처럼 보이는 조건식을 다른 언어의 boolean expression으로
오해하지 않도록 command 실행과 exit status에서 출발한다.

### Unit 4 · Repetition and Script Arguments

`for`, `while`, `until`, `break`, `continue`, `shift`, `"$@"`를 사용한다. filenames와 빈 argument를 보존하면서 반복하는
법을 중심 문제로 삼는다.

### Unit 5 · Functions and Small Script Structure

POSIX function definition, function-local positional parameters, shared shell state, environment/export 경계, function exit
status를 다룬다. 필요한 경우 `getopts`를 이용해 작은 command interface를 만든다.

### Unit 6 · Failure, Cleanup, and Portability Feedback

`trap`, explicit error handling, `sh -n`, `set -x`, ShellCheck를 다룬다. `set -e`는 성공/실패 모델을 먼저 이해한 뒤
제한과 surprise를 분석하는 대상으로만 소개한다. Bashism과 구현 차이를 찾아 고치는 연습을 포함한다.

### Unit 7 · Capstone: A Portable Automation Script

처음부터 완성 script를 복사하지 않는다. 요구사항에서 inputs, outputs, failure conditions를 정의하고 작은 단위로 작성한 뒤
argument preservation, redirection, exit status, cleanup, portability를 검증한다.

## Practice Model

연습은 transcription보다 다음 순서를 선호한다.

```text
predict
→ trace
→ run / observe
→ explain
→ repair or modify
→ transfer
```

예를 들어 `echo "$files"`를 한 번 따라 치는 대신, 같은 variable을 quoted/unquoted로 전달했을 때 **program이 실제로 몇 개의
arguments를 받는지 먼저 예측**하고 검증한다.

후반으로 갈수록 scaffold를 줄인다. 마지막에는 Bashism이 섞인 script나 whitespace/glob 때문에 깨지는 script를 보고
학습자가 스스로 문제를 분류하고 수정하게 한다.

## First Calibration Slice

첫 실제 textbook increment는 **“source text → final argv”**로 잡는다.

작은 실행 준비만 한 뒤 다음 recurring teaching pattern을 검증한다.

```text
one source line
→ quote / expand
→ predict argv
→ inspect argv
→ vary one condition
→ explain the difference
→ repair a broken case
```

이 slice가 잘 작동해야 뒤의 variable, argument handling, tests, loop에서도 같은 reasoning model을 반복할 수 있다.

## Current Build State

현재 단계는 **curriculum foundation only**다.

- curriculum scope와 prerequisite를 정의했다.
- observable outcomes와 concept dependency를 정의했다.
- planned unit responsibility를 정의했다.
- POSIX.1-2024를 normative authority로 정했다.
- 첫 calibration slice를 선택했다.
- textbook chapter와 playground는 아직 구현하지 않았다.

다음 build increment는 Unit 0 전체를 한꺼번에 채우는 것이 아니라, 위 calibration slice를 실제 설명·worked example·practice와
함께 한 번 완성하고 검토하는 것이다.
