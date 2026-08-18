# Automation Policy

자동화는 **자동 수정 가능한 것은 조용히 고치고, 실패는 사람이 판단해야 하는 문제에만 사용**한다.

## Ownership

| 영역 | 도구 | 책임 |
| --- | --- | --- |
| toolchain | mise | runtime과 CLI version pin, task entrypoint |
| Python project | uv | dependency, lock, `.venv` |
| Markdown | rumdl | auto-format |
| JSON/JSONC | Biome | auto-format/check |
| TOML | Tombi | auto-format/lint |
| Git hooks | Lefthook | staged auto-fix와 local guard |
| agent assets | AgentsMesh | canonical rule에서 target-native file 생성 |

## Local

```bash
mise install
mise run setup
mise run format
mise run ci:fast
```

local hook은 가능한 formatting 문제를 수정하고 수정된 file을 다시 stage한다.

## CI

fast CI는 다음 원칙만 가진다.

- deterministic하고 저비용인 검증만 자동 실행한다.
- formatter는 style drift를 실패시키기보다 먼저 auto-fix한다.
- write permission과 repository-defined command 실행을 분리한다.
- persisted auto-fix는 read-only job이 검증한 Git tree와 동일할 때만 허용한다.
- `main`과 manual validation은 auto-fix 결과를 repository에 persist하지 않는다.

## Tests

언어나 runtime이 실제로 사용될 때만 최소 테스트를 추가한다.

- Python/TypeScript 같은 code에는 작은 smoke/unit test부터 시작한다.
- test framework, coverage, matrix는 실제 failure mode가 생길 때 확장한다.
- 테스트 수 자체를 목표로 하지 않는다.

## Cloud and API

LLM, chatbot, external API처럼 호출 비용이 발생하는 검증은 fast CI와 분리한다.

- 기본 PR push에서 자동 호출하지 않는다.
- 별도 workflow나 explicit trigger를 사용한다.
- case/request/token/cost budget을 실행 코드에서 제한한다.
- cloud smoke와 full eval은 실제 eval harness가 생긴 뒤 추가한다.

즉, **cheap checks are automatic; expensive checks are explicit**이 기본 경계다.
