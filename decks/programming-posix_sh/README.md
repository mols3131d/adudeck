# POSIX sh Scripting

`programming-posix_sh`는 `/bin/sh` 계열에서 통하는 **기초 portable shell scripting 문법과 실행 의미**를 배우는 deck이다.

목표는 문법 조각을 외우는 것이 아니라, shell이 source text를 command와 arguments로 바꾸고, file descriptor 연결과
execution environment를 구성하고, command의 exit status를 다음 control flow에 전달하는 과정을 추적할 수 있게 되는
것이다.

## Learner Goal

작은 automation script를 직접 읽고, 작성하고, 수정하고, 디버깅할 수 있다. 특히 다음을 설명할 수 있어야 한다.

- quoting과 expansion 때문에 program이 실제로 받는 arguments가 어떻게 달라지는가?
- assignment, ordinary argument, redirection처럼 context가 달라지면 expansion semantics가 어떻게 달라지는가?
- command의 성공과 실패가 다음 실행 흐름을 어떻게 바꾸는가?
- current shell, command environment, subshell 중 어디의 state가 바뀌는가?
- stdin/stdout/stderr가 redirection과 pipeline을 거쳐 어디로 연결되는가?

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
- word, quoting, tilde/parameter/command/arithmetic expansion
- field splitting과 pathname expansion이 final argument vector에 미치는 영향
- ordinary argument context와 assignment context의 차이
- shell variable, exported environment, command environment
- positional parameters와 special parameters: `$0`, `$#`, `$?`, `"$@"` 등
- redirection, file descriptor 0/1/2, pipeline, command list
- current shell environment와 subshell environment의 상태 변화
- `test` / `[ ]`, `if`, `case`, `&&`, `||`, `!`
- `for`, `while`, `until`, `break`, `continue`
- POSIX function과 function의 argument/state/exit-status 동작
- `shift`, 기본적인 `getopts`, 작은 CLI script 구성
- `trap`의 기초와 정상 종료/실패 시 cleanup responsibility
- `sh -n`, `set -x`, ShellCheck를 이용한 서로 다른 validation evidence
- POSIX.1-2024에서 새로 표준화되었지만 adoption 확인이 필요한 surface의 구분
- 작은 portable script를 읽고 설명하고 고치는 통합 연습

기본 범위에서는 다루지 않는다.

- Bash array, `[[ ... ]]`, process substitution, `function` keyword처럼 portable POSIX core가 아닌 문법
- `local`이나 `source` 같은 common extension을 portable guarantee처럼 사용하는 방식
- interactive shell customization, job control, prompt configuration
- `sed`, `awk`, regular expression 자체의 심화 학습
- 대규모 shell application architecture
- general Unix utility portability 전체
- security hardening 전체, privileged shell programming
- `set -e` 같은 option을 이해 없이 붙이는 이른바 "strict mode" recipe

이 deck은 shell 자체를 목적화하지 않는다. small glue/automation을 읽고 쓰는 competence를 만든다. script가 큰
application처럼 자라거나 복잡한 data structure/control flow를 요구하는 경우 더 structured한 language가 적합할 수 있다는
boundary도 유지한다.

## Authority and Portability Boundary

언어 의미의 규범 기준은 **POSIX.1-2024 Shell Command Language**다.

- POSIX.1-2024: <https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html>
- POSIX Rationale은 historical choice와 Issue 8 변경 이유를 해석하는 보조 authority다.
- GNU Bash 5.3 manual은 Bash 구현과 POSIX mode의 차이를 확인하는 comparison source다.
- dash, BusyBox ash 같은 실제 implementation은 deployment evidence다.
- Debian `/bin/sh` 같은 distribution policy는 platform contract이며 POSIX language definition과 동일하지 않다.
- ShellCheck는 정적 피드백 도구이며 표준 그 자체로 취급하지 않는다.

POSIX.1-2024에 새로 포함된 기능이라도 실제 배포된 `sh` 구현의 지원은 늦거나 build configuration에 따라 달라질 수 있다.
따라서 이 deck은 다음 두 기준을 동시에 유지한다.

```text
normative explanation = POSIX.1-2024
runnable beginner core = conservative, verified implementation subset
```

예를 들어 `$'...'`와 `pipefail`은 현재 POSIX.1-2024에 포함되지만 실제 target shell에서 support를 확인하기 전에는 core
exercise의 전제로 만들지 않는다.

반대로 Debian에서 `local`을 `/bin/sh`에 사용할 수 있다는 사실은 Debian-specific allowance이지 cross-platform POSIX
guarantee가 아니다.

예시는 기본적으로 `#!/bin/sh`를 사용하되, shebang은 shell grammar 자체와 executable interpreter dispatch가 같은 층이
아니라는 경계를 함께 설명한다.

## Core Mental Models

이 deck은 한 개의 syntax list 대신 네 개의 state/data model을 반복해서 강화한다.

### 1. Source to Arguments

```text
source text
→ token recognition / parsing
→ context-sensitive expansion
→ final argv fields
```

ordinary command argument를 배울 때는 다음 흐름을 관찰한다.

```text
source word
→ tilde / parameter / command / arithmetic expansion (as applicable)
→ field splitting (when applicable)
→ pathname expansion (when applicable)
→ quote removal
→ final argv fields
```

이것은 모든 grammar context에 똑같이 적용되는 보편 공식이 아니다. quoting과 word context에 따라 적용 단계가
달라지고, tilde expansion의 결과는 field splitting과 pathname expansion을 위해 quoted된 것처럼 취급한다. assignment와
redirection 같은 context는 필요한 unit에서 차이를 추가한다.

### 2. Status to Control Flow

```text
command execution
→ exit status
→ && / || / !
→ if / while / until / function result
```

exit status는 조건문에서 갑자기 등장하는 boolean 대체물이 아니다. 첫 command부터 같은 상태로 관찰한다.
다만 `case`는 shell pattern matching, `for`는 expanded item list로 실행 경로를 정한다. 두 construct도 결과
exit status를 갖지만 **선택 입력**은 exit status가 아니다.

### 3. File Descriptors to Data Flow

```text
process
├── fd 0 → stdin
├── fd 1 → stdout
└── fd 2 → stderr

redirection / pipeline
→ change connections
→ execute command
```

### 4. Execution Environment to State Mutation

```text
current shell
├── shell variables / cwd / functions / positional parameters
├── command environment
└── subshell environment

mutation
→ ask where it happened
→ ask whether caller can observe it afterwards
```

특히 pipeline 안에서 variable을 바꾼 뒤 parent shell에 남을 것이라고 portable하게 가정하지 않는다.

## Learning Outcomes

완료 후 학습자는 다음을 할 수 있어야 한다.

1. ordinary command source 한 줄이 expansion을 거쳐 어떤 command와 exact argument vector로 실행되는지 추적한다.
2. single/double quote와 unquoted expansion의 차이를 이용해 empty, whitespace, glob character가 포함된 argument
   boundary를 보존한다.
3. assignment context와 ordinary argument context를 구분하고 shell variable, exported environment, temporary command
   environment의 관계를 설명한다.
4. `$#`, `"$@"`, `shift`를 이용해 script/function argument를 보존하면서 처리한다.
5. redirection과 pipeline을 fd 0/1/2 및 exit-status data flow로 설명하고 redirection order를 추적한다.
6. current shell과 subshell의 state mutation을 구분하고 pipeline-dependent variable persistence에 의존하는 script를
   고친다.
7. `if`, `while`, `until`, `&&`, `||`에서 exit status가 실행 경로를 결정하는 방식과 `case`의 pattern matching,
   `for`의 item-list iteration을 구분하고 각 construct의 실행 순서와 결과 exit status를 추적한다.
8. POSIX function의 positional parameters, shared shell state, 반환 status를 설명하고 common extension인 `local`에
   의존하지 않는 작은 function을 작성한다.
9. `sh -n`, execution trace, ShellCheck, selected multi-shell execution이 각각 어떤 evidence를 주고 무엇을 증명하지
   못하는지 설명한다.
10. Bash/platform-specific assumption이 섞인 작은 script를 portable target으로 고치고 bounded portability claim과
    validation evidence를 제시한다.
11. inputs, outputs, failure conditions, cleanup responsibility를 먼저 정의하고 작은 automation script를 독립적으로
    설계한다.

## Concept Dependencies

```text
script execution boundary
        ↓
ordinary words + quoting
        ↓
expansion → fields → argv
        ↓
assignment + variables + environments
        ↓
redirection + pipeline + execution environment
        ↓
exit status + conditional control flow
        ↓
iteration + argument processing
        ↓
functions + script organization
        ↓
failure + cleanup + portability validation
        ↓
integrated script
```

각 단계는 새로운 punctuation을 추가하는 것이 아니라 앞서 만든 state model을 확장한다.

## Planned Learning Units

아래는 curriculum architecture다. 아직 chapter file을 미리 만들지 않는다.

### Unit 0 · A Script Is an Executed Command Language

script 실행 경계, `#!/bin/sh`, comment, simple command, `printf`, 첫 exit status observation을 다룬다. executable file로
실행하는 것과 `sh script.sh`로 interpreter에 직접 전달하는 것을 구분한다.

### Unit 1 · From Source Words to Final Arguments

먼저 **ordinary argument context** 하나에 집중한다.

- literal word
- single/double/unquoted form
- basic tilde expansion (`~`, `~/path`)과 quoting에 따른 차이
- parameter expansion
- `$(...)` command substitution
- arithmetic expansion (`$((...))`)의 값과 argument field
- field splitting
- pathname expansion 및 shell pattern 기초 (`*`, `?`, `[...]`)
- final `argc/argv` prediction
- command substitution이 trailing newline을 보존하지 않는 boundary

assignment context까지 섞지 않고 argument model을 먼저 안정시킨다. `HOME`이 unset이면 tilde expansion 결과를
보장하지 않으며, 여기서는 ordinary argument에서의 기본 tilde와 단순 정수 연산에 집중한다. Assignment-specific
tilde semantics는 Unit 2, arithmetic expansion을 이용한 counter 응용은 Unit 4에서 다룬다.

### Unit 2 · Variables, Environments, Redirection, and Pipelines

Unit 1의 model에 grammar/execution context를 추가한다.

- assignment context
- shell variable와 `export`
- command environment
- positional/special parameters
- fd 0/1/2와 redirection order
- pipeline byte flow
- current shell / subshell boundary
- default pipeline exit status

pipeline 안의 state mutation이 caller에 남는다고 가정하지 않는 portable rule을 명시한다.

### Unit 3 · Decisions, Patterns, and Resulting Status

`$?`, `test` / `[ ]`, `if`, `&&`, `||`, `!`에서는 command의 exit status가 조건과 단락 평가에
어떻게 쓰이는지 추적한다. 반면 `case`는 expanded word를 shell pattern과 비교하여 clause를 고른다.
Unit 1에서 익힌 pattern 기초를 재사용하되, `case` selection을 pathname expansion과 동일한 동작으로 설명하지 않는다.
각 construct가 최종적으로 반환하는 status와 다음 실행 경로를 고르는 입력을 분리해 관찰한다.

`&&`와 `||`가 POSIX shell에서는 동일 precedence와 left associativity를 가진다는 점을 tracing으로 확인한다. 복잡한
`[ ... -a ... -o ... ]`보다 command-level composition을 선호한다.

### Unit 4 · Repetition and Script Arguments

`for`, `while`, `until`, `break`, `continue`, `shift`, `"$@"`를 사용한다. `for`는 item list를
순회한다는 점을 `while`/`until`의 exit-status 조건과 구분하고, Unit 1의 arithmetic expansion (`$((...))`)을
counter update와 반복 상태 추적에 적용한다.

핵심 invariant는 **caller의 argument vector를 필요 이상으로 다시 split/glob하지 않고 보존한다**는 것이다. empty,
whitespace, glob, leading-dash argument를 포함한다. 단, shell의 quoting은 argument boundary를 보존할 뿐
utility의 option parsing을 변경하지 않는다. `--` 지원 여부 또는 적절한 `./` pathname prefix는 개별 utility
contract에 따라 판단한다.

pipeline-fed loop가 parent variable을 업데이트한다고 가정하는 portability trap도 이전 execution-environment model과
연결한다.

### Unit 5 · Functions and Small Script Structure

POSIX function definition, function call 동안의 positional parameters, shared shell state, environment/export 경계,
function exit status와 `return`을 다룬다. 필요한 경우 `getopts`로 작은 command interface를 만든다.

`local`은 core code에서 사용하지 않고 common implementation/platform extension의 비교 대상으로만 둔다.

### Unit 6 · Failure, Cleanup, and Portability Feedback

- expected failure와 fatal failure 구분
- explicit status handling
- `trap`과 resource lifetime
- `sh -n`
- `set -x`
- ShellCheck의 versioned feedback
- Bashism/extension repair
- POSIX.1-2024 adoption 사례: `$'...'`, `pipefail`
- `set -e`의 context-sensitive behavior

`set -e`나 `pipefail`이 앞서 배운 status reasoning을 대신하지 않도록 한다.

### Unit 7 · Capstone: A Portable Automation Script

처음부터 완성 script를 복사하지 않는다.

```text
requirements
→ input / argv contract
→ output / fd contract
→ state mutation boundary
→ failure conditions
→ cleanup responsibility
→ implementation
→ evidence
→ bounded portability claim
```

## Outcome Development and Assessment Coverage

각 outcome은 학습할 unit과 그 성취를 관찰할 평가 증거를 함께 갖는다. 아래는 **curriculum-level coverage**이며
실제 평가 문항, 채점 기준, playground implementation은 후속 교본 작업에서 구체화한다.

| Outcome | Develop | Assess · 관찰 가능한 증거 |
| --- | --- | --- |
| O1 · exact argv | Unit 1 | quoting/expansion의 최종 `argc/argv` 예측 및 관찰값 설명 |
| O2 · quoting/field boundary | Unit 1 | empty/whitespace/glob argument가 깨진 예제를 수정하고 이유 설명 |
| O3 · assignment/environment | Unit 2 | assignment와 ordinary word context, export/temporary environment 상태 추적 |
| O4 · positional arguments | Unit 2, Unit 4, Unit 5 | `"$@"`, `$#`, `shift`를 활용한 wrapper/function의 argument-vector 보존 |
| O5 · fd/pipeline | Unit 2 | redirection 순서별 fd 0/1/2 연결과 pipeline/status 추적 |
| O6 · shell/subshell state | Unit 2, Unit 4 | pipeline 안의 state mutation에 의존하는 버그 설명 및 수정 |
| O7 · control-flow mechanism | Unit 3, Unit 4 | status/pattern/item list의 결정 입력과 resulting status를 구분해 실행 추적 |
| O8 · function/state | Unit 5 | function positional parameters, shared state, `return` 동작 추적 및 수정 |
| O9 · evidence limits | Unit 6 | POSIX text, `sh -n`, ShellCheck, runtime 비교의 증거 범위 판별 |
| O10 · portability repair | Unit 6, Unit 7 | Bash/platform assumption 수정과 검증 범위를 제한한 portability claim |
| O11 · independent synthesis | Unit 7 | 요구사항·argv/fd/state/failure/cleanup 계약부터 구현·검증 증거까지 제시 |

## Practice Model

연습은 transcription보다 다음 순서를 선호한다.

```text
predict
→ trace hidden state
→ run / observe
→ compare prediction and evidence
→ explain
→ vary one condition
→ repair or modify
→ transfer
```

관찰할 hidden state는 해당 unit에 따라 달라진다.

- argv boundaries
- shell/environment state
- fd targets
- exit status
- positional parameters
- cleanup effect

후반으로 갈수록 scaffold를 줄인다. 마지막에는 implementation-specific assumption이 섞였거나
whitespace/glob/pipeline-state 때문에 깨지는 script를 보고 학습자가 스스로 문제를 분류하고 수정하게 한다.

## First Calibration Slice

첫 실제 textbook increment는 **ordinary argument context의 `source text → final argv`**로 제한한다.

```text
one source line
→ identify source words
→ predict expansion and final argc/argv
→ inspect exact argument boundaries
→ vary space / empty / glob input one at a time
→ compare quoted / unquoted form
→ explain the difference
→ repair one broken case
→ transfer to a new value
```

이 slice에서는 assignment, pipeline, function까지 한꺼번에 설명하지 않는다. recurring teaching pattern과 argument mental
model이 실제로 잘 작동하는지 먼저 검증한다.

첫 increment의 acceptance는 **최종 `argc/argv` 경계에 대한 예측·설명·수정**이다. 관찰 도구의 출력만 재현했다고
통과시키지 않는다.

| Probe class | 학습자가 예측할 상태 | 관찰할 증거 |
| --- | --- | --- |
| Whitespace | 기본 `IFS`에서 `$value`와 `"$value"`의 field 수 차이 | `value='a b'`의 정확한 argv |
| Empty | `$empty`의 field 제거와 `"$empty"`의 빈 argument 보존 | argument 개수와 빈 문자열의 존재 |
| Glob | unquoted pathname pattern과 quoted literal의 차이 | 격리된 fixture의 matches와 final fields |
| Repair / transfer | 깨지는 unquoted 전달을 수정하는 근거 | 다른 입력에서도 argument vector가 유지되는지 설명 |

학습자는 예측 전에 shell context(기본 `IFS`, glob fixture, 필요한 환경값)를 확인한 뒤 source line의
final argv를 **실행 전에** 적는다. 관찰·설명 후 잘못된 quoting을 수정하고 새로운 입력으로 transfer한다.
정확한 pathname match 순서가 중요하면 fixture 및 locale을 고정한다.

이것은 curriculum acceptance contract다. 실제 설명, worked example, 문제, 실행 fixture, 평가 rubric과
runtime matrix는 첫 build increment에서 해당 material owner와 함께 작성한다.

## Portability Validation Model

portable claim은 한 command의 성공으로 결정하지 않는다.

```text
specification review
→ syntax check
→ static feedback
→ concept-specific runtime observation
→ selected implementation comparison when useful
→ bounded claim
```

- `sh -n`: current parser가 source를 받아들이는지 확인한다.
- ShellCheck: known issue와 dialect warning을 찾는다. tool version에 따라 결과가 달라질 수 있다.
- one-shell execution: 그 implementation/build의 behavior만 관찰한다.
- multi-shell comparison: assumption divergence를 찾는 데 유용하지만 모든 POSIX implementation을 증명하지 않는다.
- POSIX text: standardized contract를 알려주지만 deployed adoption을 증명하지 않는다.

implementation matrix는 portability의 증명서보다 **잘못된 가정을 반증하는 도구**로 사용한다.

## Current Build State

현재 단계는 **research-backed curriculum foundation**이다.

- learner prerequisite와 scope를 정의했다.
- observable outcomes와 concept dependency를 재검토했다.
- POSIX.1-2024를 normative authority로 유지했다.
- implementation/platform/tool evidence를 authority와 분리했다.
- deep research에서 발견한 `pipefail` classification 오류를 수정했다.
- `$'...'` adoption을 deployed dash와 upstream dash로 구분했다.
- assignment context, pipeline subshell state, `&&`/`||` precedence, function scope를 unit responsibility에 반영했다.
- pedagogy reference와 dialect authority를 분리했다.
- first calibration slice를 ordinary argument context 하나로 더 좁혔다.
- curriculum review 결과 tilde/arithmetic expansion의 unit 책임, control-flow 선택 입력의 차이,
  outcome development/assessment coverage를 명시했다.
- textbook chapter와 playground는 아직 구현하지 않았다.

다음 build increment는 전체 Unit 0이나 Unit 1을 한 번에 채우는 것이 아니라, 위 calibration slice를 실제 설명·worked
example·prediction·runtime observation·repair·transfer까지 한 번 완성하고 textbook quality gate로 검토하는 것이다.
