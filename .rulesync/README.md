# Rulesync

`.rulesync/`는 repository-owned portable agent Rules와 Skills의 canonical authoring source다. Generated target files는
derived projection이며 직접 편집하지 않는다.

## Layout

```text
.rulesync/
├── rules/     # portable repository rules
└── skills/    # portable agent skills
```

`rulesync.jsonc`는 shared target과 feature를 정의한다. 현재 target은 `copilot`, `codexcli`이고 `rules`, `skills`만
생성한다.

Directory-scoped Rule은 `globs`로 Copilot scope를 표현하고 `agentsmd.subprojectPath`로 Codex의 nested `AGENTS.md`
scope를 보존한다.

## Commands

```bash
mise run rulesync:doctor
mise run rulesync:generate
mise run rulesync:check
```

- `doctor` — configuration을 strict mode로 진단한다.
- `generate` — canonical source에서 tracked target projection을 갱신한다.
- `check` — generated projection drift가 없는지 확인한다.

Rulesync는 active development 동안 mise의 GitHub backend에서 current latest release를 사용한다.
