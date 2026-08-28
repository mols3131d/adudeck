# Rulesync

`.rulesync/`는 repository-owned portable agent Rules와 Skills의 canonical authoring source다. Generated target files는
derived projection이며 직접 편집하지 않는다.

## Layout

```text
.rulesync/
├── rules/     # portable repository rules
├── scripts/   # root AGENTS projection helper
└── skills/    # portable agent skills
```

`rulesync.jsonc`가 shared Skill target set과 external Skill dependency selection의 source of truth다.

External reusable Skills는 `rulesync.jsonc`의 declarative `sources`로 관리한다. Upstream repository가 authority이며,
`rulesync install`이 dependency를 `.rulesync/skills/.curated/`에 설치하고 resolved revision을 `rulesync.lock`에
고정한다. Curated dependency와 generated Skill projections는 Git에 추적하지 않는다. Chatbot route의 external source
revision도 같은 `resolvedRef`를 따라야 한다.

Repository Rules는 `agentsmd,copilot` 대상으로 별도 생성한다. Nested `AGENTS.md`는 canonical scoped Rule projection이고,
`.rulesync/scripts/project-root-agents.sh`가 canonical root Rule body를 root `AGENTS.md`로 투영한다. Chatbot용
cross-`AGENTS.md` loading harness는 `CHATBOT.md`만 소유한다.

`rulesync.local.jsonc`에서 `targets`를 정의하면 shared target set 전체를 교체한다. Local target을 추가할 때 repository의
shared target도 함께 적는다.

## Commands

```bash
mise run rulesync:doctor
mise run rulesync:install
mise run rulesync:generate
mise run rulesync:check
```

- `doctor` — configuration을 strict mode로 진단한다.
- `install` — external dependency를 resolve하고 lockfile을 갱신한다.
- `generate` — frozen lock을 소비해 Skills와 Rule projections를 생성한다.
- `check` — frozen Skills, Copilot Rules, root `AGENTS.md` projection을 확인한다.

Rulesync는 active development 동안 mise의 GitHub backend에서 current latest release를 사용한다.
