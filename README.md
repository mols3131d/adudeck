# adudeck

**Agentic Education Deck** — AI 에이전트를 활용해 공부하기 위한 개인 학습 workspace.

학습 주제를 덱(deck) 단위로 구성하고, 에이전트를 활용해 학습·탐구·복습한다.

## Layout

```text
.agentsmesh/         # AgentsMesh canonical agent assets
decks/               # active learning decks
decks/archive/       # inactive decks
mise.toml            # repository toolchain and tasks
pyproject.toml       # uv-managed Python project
uv.lock              # reproducible Python dependency lock
```

`adudeck`는 여러 학습 덱을 함께 관리하는 monorepo로 운영한다.

## Bootstrap

```bash
mise install
mise run setup
mise run agents:check
```

mise가 Python과 uv 버전을 고정하고, uv가 Python dependency와 `.venv`를 관리한다. `UV_PYTHON`은 mise가 관리하는 Python
interpreter를 가리키며, mise는 기존 uv `.venv`를 자동으로 활성화한다.

`setup`은 `uv sync --locked`를 실행하고, 이 저장소에만 `.gitmessage`를 commit template으로 설정한 뒤
Lefthook을 설치한다.

## Automation

staged Markdown, JSON/JSONC, TOML은 pre-commit에서 자동 포맷하고 수정된 파일을 다시 stage한다. canonical
`.agentsmesh/**/*.md`도 자동 포맷한 뒤 AgentsMesh를 재생성하며, target-native generated Markdown만 formatter 대상에서
제외한다.

```bash
mise run format
mise run ci:fast
```

non-main branch push에서는 read-only prepare job이 auto-fix한 정확한 Git tree를 검증하고 patch와 tree SHA를 만든다.
수정이 있으면 별도의 write-capable persist job이 patch를 적용한 뒤 tree SHA가 검증된 tree와 일치할 때만 commit하고,
status-only job이 `ci/validated`를 최종 commit SHA에 기록한다. `main`과 수동 validation에서는 repository 내용을 쓰지
않는다.

`ci:fast`는 uv 환경을 동기화한 뒤 formatter를 적용하고, Lefthook config, AgentsMesh drift와 최소 Python runtime smoke
테스트만 검증한다.

AgentsMesh canonical assets를 변경한 뒤에는 `mise run agents:generate`로 target-native 파일을 다시 생성한다.
