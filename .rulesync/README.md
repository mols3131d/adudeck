# Rulesync

`.rulesync/`는 repository-owned portable agent Rules와 Skills의 canonical authoring source다. Generated target files는
derived projection이며 직접 편집하지 않는다.

## Layout

```text
.rulesync/
├── rules/     # portable repository rules
├── scripts/   # deterministic projection adapters
└── skills/    # portable agent skills
```

`rulesync.jsonc`는 Skills를 생성할 다음 shared target을 정의한다.

- `claudecode`
- `codexcli`
- `copilot`
- `copilotcli`
- `antigravity-ide`
- `antigravity-cli`

External reusable Skills는 `rulesync.jsonc`의 declarative `sources`로 관리한다. Upstream repository가 해당 Skill의
authority이며, `rulesync install`은 선택된 dependency를 `.rulesync/skills/.curated/`에 설치하고 resolved revision을
`rulesync.lock`에 고정한다. Curated dependency는 local generated input이므로 Git에 직접 추적하지 않고 lockfile을 통해
재현한다.

Generated Skills는 target-native runtime을 위한 local projection으로 취급하며 Git에 추적하지 않는다. 현재 project-scope
skill projection 경로는 `.claude/skills/`, `.github/skills/`, `.agents/skills/`이고 `.gitignore`가 이들을 제외한다.
Canonical Skill은 `.rulesync/skills/`에만 유지한다.

Repository Rules는 `agentsmd,copilot` 대상으로 별도 생성·검증한다. Rulesync가 생성한 nested `AGENTS.md`는 canonical
scoped Rule의 `agentsmd.subprojectPath` projection으로 그대로 유지한다. Root `AGENTS.md`에 Rulesync가 추가하는 nested
Rule discovery preamble은 `.rulesync/scripts/normalize_agents.py`가 projection 단계에서 제거한다. 이 adapter는 Rule
내용을 소유하거나 변경하지 않고 generated discovery wrapper만 정규화한다. Root와 nested `AGENTS.md`를 어떤 경로와
순서로 읽는지는 `CHATBOT.md`만 소유한다.

`rulesync.local.jsonc`에서 `targets`를 정의하면 shared target set 전체를 교체한다. Local target을 추가할 때 repository의
shared target도 함께 적는다.

## Commands

```bash
mise run rulesync:doctor
mise run rulesync:install
mise run rulesync:generate
mise run rulesync:check
```

- `doctor` — shared Rulesync configuration을 strict mode로 진단한다.
- `install` — external dependency를 lockfile에 따라 `.curated/`에 설치한다.
- `generate` — dependency를 설치하고 Skills/Rules를 생성한 뒤 root `AGENTS.md` projection을 정규화한다.
- `check` — frozen dependency, native Copilot Rule projection, normalized root/nested `AGENTS.md` projection을 검증한다.

Rulesync는 active development 동안 mise의 GitHub backend에서 current latest release를 사용한다.
