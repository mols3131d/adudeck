# Script Workflows Plan

Status: working note in `inbox/`; non-canonical.

## Goal

정리 대상은 repository의 반복적인 local automation이다.

- formatting
- testing
- environment setup
- environment update

새 automation framework를 추가하지 않는다. 이미 존재하는 `mise`, `uv`, `rumdl`, `Biome`, `Tombi`, `Lefthook`,
`Rulesync`를 그대로 사용하고, shell script와 `mise` task 사이의 책임만 명확하게 만든다.

## Current State

`main`에는 이미 다음 script가 있다.

- `scripts/format.sh`
- `scripts/test.sh`
- `scripts/setup.sh`
- `scripts/update.sh`

또한 `mise.toml`이 동일한 작업의 일부를 직접 구현하고 있다. 특히 formatting과 test subtask는 script와 `mise` 양쪽에
command sequence가 중복되어 있다.

이 작업의 핵심은 script를 다시 만드는 것이 아니라 실행 경로를 정리하는 것이다.

## Ownership Model

### `mise`

사람과 editor/CI가 사용하는 repository task entrypoint를 소유한다.

예:

```bash
mise run format
mise run test
mise run setup
mise run update
mise run ci:fast
```

`mise.toml`은 task 이름, tool resolution, orchestration만 담당한다. multi-step shell implementation을 가능한 한 복제하지
않는다.

### `scripts/`

여러 shell command를 순서대로 실행해야 하는 작업의 구현을 소유한다.

- repo root resolution
- fail-fast behavior
- target dispatch
- temporary directory cleanup
- 단계별 log
- multi-project sequencing

단순한 한 줄짜리 tool invocation을 모두 script로 감싸지는 않는다.

### Tool configuration

실제 formatting/linting semantics는 각 tool의 config가 소유한다.

- Markdown: `rumdl`
- JSON/JSONC: `Biome`
- TOML: `Tombi`
- staged-file hook behavior: `lefthook.yml`

Lefthook은 staged file만 대상으로 해야 하므로 full-repository script를 호출하도록 억지로 통합하지 않는다.

## Script Contracts

### `scripts/format.sh`

목적: repository-owned text format을 일관되게 format하거나 검증한다.

초기 contract:

```text
scripts/format.sh [--check]
```

- default: auto-format
- `--check`: 파일을 수정하지 않고 drift를 검증
- Markdown / JSON / JSONC / TOML 처리
- generated agent projection과 repository policy file에 대한 기존 exclude semantics 유지

첫 단계에서는 formatter 종류별 custom argument parser나 공통 shell library를 만들지 않는다.

`mise run format`은 이 script에 위임한다.

기존 세부 task가 계속 필요하면 `format:markdown`, `format:json`, `format:toml`은 leaf task로 유지할 수 있다. 단, 같은
multi-step sequence를 두 군데서 유지하지 않는다.

### `scripts/test.sh`

목적: repository test suite의 single dispatcher가 된다.

초기 target:

```text
scripts/test.sh all
scripts/test.sh smoke
scripts/test.sh dataset-generator
scripts/test.sh scripts
```

- `all`: 아래 test target을 순서대로 실행
- `smoke`: root Python/toolchain 최소 smoke test
- `dataset-generator`: unit test + CLI smoke test
- `scripts`: `bash -n scripts/*.sh` 수준의 zero-dependency shell syntax validation

`mise run test`, `mise run test:smoke`, `mise run test:dataset-generator`는 script target에 위임한다.

ShellCheck 같은 새 dependency는 실제 failure mode가 생기기 전에는 추가하지 않는다.

### `scripts/setup.sh`

목적: clean clone을 현재 repository state에 맞는 reproducible local workspace로 만든다.

해야 하는 일:

1. `mise` toolchain 설치/확인
2. root `uv sync --locked`
3. 별도 uv project가 있으면 locked sync
4. repository-local Git 설정
5. Lefthook 설치
6. frozen Rulesync dependency 설치

중요한 invariant:

- lockfile을 upgrade하지 않는다.
- dependency version을 임의로 변경하지 않는다.
- clean checkout에서 실행한 뒤 불필요한 tracked-file diff를 만들지 않는다.

`mise run setup`은 이 script에 위임한다.

### `scripts/update.sh`

목적: repository가 의도적으로 관리하는 dependency/tool/generated state를 최신 상태로 갱신한다.

해야 하는 일:

1. mise-managed tool update
2. root Python dependency lock upgrade + sync
3. nested uv project dependency lock upgrade + sync
4. Rulesync external dependency update
5. agent projection regenerate
6. hook refresh

`setup`과 달리 tracked file 변경이 발생할 수 있는 mutation command다.

완료 후 별도 검증 경로인 `mise run ci:fast`로 결과를 확인한다. `update.sh` 내부에 전체 CI orchestration을 다시 복제하지
않는다.

## `mise.toml` Changes

첫 구현에서는 다음 방향으로 정리한다.

```text
format                    -> bash scripts/format.sh
test                      -> bash scripts/test.sh all
test:smoke                -> bash scripts/test.sh smoke
test:dataset-generator    -> bash scripts/test.sh dataset-generator
test:scripts              -> bash scripts/test.sh scripts
setup                     -> bash scripts/setup.sh
update                    -> bash scripts/update.sh
```

`ci:fast`는 repository orchestration owner로 남긴다.

예상 흐름:

```text
mise run ci:fast
  -> dependency sync/check
  -> mise run format
  -> hook/rulesync validation
  -> mise run test
```

## What Not to Add Yet

현재 단계에서는 다음을 만들지 않는다.

- `scripts/lib.sh` 같은 shared shell framework
- 별도 task runner
- Makefile
- formatter/linter abstraction layer
- environment profile matrix
- OS별 script 분기
- ShellCheck dependency
- 별도 `check.sh` wrapper

반복되는 실제 문제나 플랫폼 요구가 생기면 그때 추가한다.

## Implementation Order

1. `mise.toml`의 duplicate implementation을 script delegation으로 축소한다.
2. `test.sh`에 `scripts` target과 `bash -n` 검증을 추가한다.
3. `format.sh`의 `--check` contract와 exit behavior를 확인한다.
4. `setup.sh`가 lockfile을 변경하지 않는지 확인한다.
5. `update.sh`의 mutation boundary를 확인한다.
6. README / `docs/automation.md`는 실제 behavior와 달라지는 부분만 최소 수정한다.
7. `mise run ci:fast`로 전체 fast path를 검증한다.

## Acceptance Criteria

- `mise run format`과 direct `scripts/format.sh`의 결과가 일치한다.
- `scripts/format.sh --check`는 파일을 수정하지 않는다.
- `mise run test`가 모든 현재 repository test를 실행한다.
- `mise run test:scripts`가 shell syntax error를 잡는다.
- `mise run setup`은 clean repository에서 dependency/lockfile upgrade를 만들지 않는다.
- `mise run update`가 의도된 lock/generated state만 갱신한다.
- VS Code task와 CI는 계속 `mise` entrypoint를 사용한다.
- Lefthook의 staged-file formatting 범위는 유지된다.
- 최종적으로 `mise run ci:fast`가 통과한다.

## Likely First Patch

첫 patch는 작게 유지한다.

- `mise.toml`: test task 중복 제거, `format`을 `scripts/format.sh`로 연결
- `scripts/test.sh`: `scripts` target 추가
- 필요 시 `scripts/format.sh`: argument validation 보강
- behavior가 바뀐 경우에만 관련 문서 수정

`setup.sh`와 `update.sh`는 현재 구현이 위 contract를 이미 대체로 만족하므로, 실제 검증에서 문제가 확인되지 않으면
불필요하게 다시 쓰지 않는다.
