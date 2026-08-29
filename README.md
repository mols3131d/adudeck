# adudeck

**Agentic Education Deck** — AI 에이전트와 함께 공부하기 위한 개인 학습 workspace.

학습 주제를 deck 단위로 정리하고, AI가 생성·보조한 설명·예제·연습 자료를 활용해 학습·탐구·복습한다. 필요하면 공개된 외부
자료도 참고한다.

이 저장소는 개인적인 학습과 실험을 위한 공간이며, 서비스·사업·교육 상품·공식 교육과정을 제공하기 위한 프로젝트가 아니다.

## Layout

```text
.rulesync/           # canonical agent assets
decks/               # default filesystem deck storage
docs/                # repository-wide human-facing docs
tools/               # reusable learning utilities
rulesync.jsonc        # shared agent projection configuration
mise.toml             # toolchain and repository tasks
pyproject.toml        # uv-managed Python project
uv.lock               # reproducible Python lock
```

## Start

```bash
mise install
mise run setup
```

`mise`가 repository toolchain을 관리하고, `uv`가 Python dependency와 `.venv`를 관리한다. Agent asset을 변경했을 때는
`mise run rulesync:generate`로 projection을 갱신한다.

## Working Model

- 별도 지시가 없으면 deck은 `decks/`에서 filesystem으로 관리한다.
- 다른 storage는 사용자가 현재 deck 또는 작업에 대해 명시적으로 지정한 경우에만 사용한다.
- deck의 storage와 state 원칙은 [`docs/decks.md`](docs/decks.md)를 따른다.
- directory 사용법은 가까운 `README.md`에, repository-wide 정책은 `docs/`에 둔다.
- portable agent Rules와 Skills의 canonical source는 `.rulesync/`이며 generated target files는 직접 수정하지 않는다.

## Automation

```bash
mise run format
mise run ci:fast
```

format 가능한 문제는 자동 수정하고, CI는 빠르고 결정적인 검증만 수행한다. 자세한 경계는
[`docs/automation.md`](docs/automation.md)를 따른다.

## Docs

- [`docs/VISON.md`](docs/VISON.md) — workspace vision과 learning principles
- [`docs/README.md`](docs/README.md) — 문서 배치와 정책 index
- [`docs/decks.md`](docs/decks.md) — deck storage, state, content 원칙
- [`docs/automation.md`](docs/automation.md) — local/CI/cloud automation 경계
