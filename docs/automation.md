# Automation Policy

자동화는 **자동 수정 가능한 것은 조용히 고치고, 실패는 사람이 판단해야 하는 문제에만 사용**한다.

## Ownership

| 영역 | 도구 | 책임 |
| --- | --- | --- |
| task entrypoint | mise | 사람, editor, CI가 호출하는 repository task와 orchestration |
| multi-step workflow | `scripts/` | formatting, testing, setup, update의 실행 순서와 failure boundary |
| Python project | uv | dependency, lock, `.venv` |
| Markdown | rumdl | auto-format |
| JSON/JSONC | Biome | auto-format/check |
| TOML | Tombi | auto-format/lint |
| Git hooks | Lefthook | staged auto-fix와 local guard |
| agent assets | Rulesync | canonical Rule/Skill에서 target-native file 생성 |

## Local

`mise` binary는 repository setup의 prerequisite다. 설치된 `mise`를 기준으로 다음 entrypoint를 사용한다.

```bash
mise run setup
mise run ci:fast
```

`setup`은 `mise.toml`에 선언된 tool을 설치하고 locked dependency와 local hook을 구성한다. version pin이나 lock을
upgrade하지 않는다. 의도적으로 repository-managed tool pin, dependency lock, Rulesync dependency/generated state를
갱신할 때만 `mise run update`를 사용한다.

`ci:fast`는 format 이후 Rulesync projection을 생성·검증하고 테스트를 실행한다. 필요한 단계만 실행할 때는
`mise run format`, `mise run format:check`, `mise run test` (특정 대상만 검증할 때는 `mise run test <target...>`)
또는 `mise run rulesync:generate` 같은 개별 task를 사용한다.

multi-step 구현은 `scripts/`가 소유하므로 필요하면 직접 호출할 수 있다.

```bash
bash scripts/format.sh
bash scripts/format.sh --check
bash scripts/test.sh all
bash scripts/test.sh smoke scripts
bash scripts/setup.sh
bash scripts/update.sh
```

`format.sh --check`는 파일을 수정하지 않고 Markdown, JSON/JSONC, TOML formatting과 lint drift를 검사한다.

local hook은 staged file의 formatting 문제를 수정하고 수정된 file을 다시 stage한다. full-repository script로 대체하지
않는다.

## CI

CI는 `ci/validated` 단일 상태 보고를 유지하면서 변경 영향 범위에 비례해 검증한다.

- formatting, hook, Rulesync projection, chatbot route, root `smoke`, `scripts` 검증은 모든 실행에서 수행한다.
- branch push는 `origin/main` 대비 변경 경로(`scripts/test.sh --ci-scope`)를 계산해 영향받는 subproject test와
  OpenTelemetry external runtime acceptance만 선택 실행한다.
- 공통 설정(`mise.toml`, `pyproject.toml`, `uv.lock`, `scripts/*`, `.github/workflows/*`)이나 미분류 경로가 변경되면,
  또는 `main` push·`workflow_dispatch`·base 비교 불가 시에는 전체 테스트와 external acceptance로 fail-safe 확장한다.
- formatter와 Rulesync는 branch push에서 style/projection drift를 먼저 auto-fix하되, write permission과
  repository-defined command 실행을 분리한다.
- persisted auto-fix는 read-only job이 검증한 Git tree와 동일할 때만 허용하며, `main`과 manual validation은
  auto-fix drift 발견 시 저장소를 수정하지 않고 실패시킨다.

## Tests

언어나 runtime이 실제로 사용될 때만 최소 테스트를 추가한다.

- Python/TypeScript 같은 code에는 작은 smoke/unit test부터 시작한다.
- repository shell script는 `bash -n scripts/*.sh`로 최소 syntax validation을 수행한다.
- test framework, coverage, matrix는 실제 failure mode가 생길 때 확장한다.
- 테스트 수 자체를 목표로 하지 않는다.

## Cloud and API

LLM, chatbot, external API처럼 호출 비용이 발생하는 검증은 fast CI와 분리한다.

- 기본 PR push에서 자동 호출하지 않는다.
- 별도 workflow나 explicit trigger를 사용한다.
- case/request/token/cost budget을 실행 코드에서 제한한다.
- cloud smoke와 full eval은 실제 eval harness가 생긴 뒤 추가한다.

즉, **cheap checks are automatic; expensive checks are explicit**이 기본 경계다.
