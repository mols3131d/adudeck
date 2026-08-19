# adudeck

**Agentic Education Deck** — AI 에이전트가 생성·보조한 학습 자료로 공부하고 기록하는 개인 학습 workspace.

학습 주제를 deck 단위로 구성하고, 에이전트를 활용해 학습·탐구·복습한다.

## Scope

- 개인 학습과 실험을 위한 repository다.
- 서비스, 사업, 교육 상품 또는 공식 교육과정을 제공하기 위한 프로젝트가 아니다.
- 학습 자료는 AI-generated / AI-assisted content를 중심으로 만들며, 필요에 따라 외부 공개 자료를 참고한다.

## Layout

```text
.agentsmesh/         # canonical agent assets
decks/               # learning decks
docs/                # repository-wide human-facing docs
mise.toml            # toolchain and repository tasks
pyproject.toml       # uv-managed Python project
uv.lock              # reproducible Python lock
```

## Start

```bash
mise install
mise run setup
mise run agents:check
```

`mise`가 repository toolchain을 고정하고, `uv`가 Python dependency와 `.venv`를 관리한다.

## Working Model

- 학습 content는 `decks/`에서 관리하고, 구조와 lifecycle은 [`docs/decks.md`](docs/decks.md)를 따른다.
- directory 사용법은 가까운 `README.md`에, repository-wide 정책은 `docs/`에 둔다.
- portable agent rules의 canonical source는 `.agentsmesh/`이며 generated target files는 직접 수정하지 않는다.

## Automation

```bash
mise run format
mise run ci:fast
```

format 가능한 문제는 자동 수정하고, CI는 빠르고 결정적인 검증만 수행한다. 자세한 경계는
[`docs/automation.md`](docs/automation.md)를 따른다.

## Docs

- [`docs/README.md`](docs/README.md) — 문서 배치와 정책 index
- [`docs/decks.md`](docs/decks.md) — deck lifecycle과 content 원칙
- [`docs/automation.md`](docs/automation.md) — local/CI/cloud automation 경계
