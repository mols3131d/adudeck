# Deck Policy

Deck은 하나의 학습 주제를 독립적으로 다루는 하나의 workspace unit이다.

## Storage

Filesystem은 기본 storage다. 별도 지시가 없으면 이 repository의 `decks/`에서 deck을 관리한다.

다른 storage는 사용자가 현재 deck 또는 작업에 대해 명시적으로 지정한 경우에만 사용한다. Agent가 임의로 external
storage를 선택하거나 deck을 이동, 복제, mirror, sync하지 않는다.

Storage가 달라도 하나의 deck은 하나의 응집된 학습 자료 묶음으로 유지한다.

## State

Deck은 다음 세 상태 중 하나를 가진다.

- active — 현재 학습하거나 수정·확장 중이다.
- backlog — 현재 active는 아니지만 후속 학습, 보충, 변경 등의 작업 의도가 있다.
- archive — 현재 예정된 작업이 없는 inactive 상태다.

Deck은 작업 의도가 바뀌면 세 상태 사이를 이동할 수 있다. 같은 deck을 여러 상태에 동시에 두지 않는다.

### Filesystem

Filesystem에서는 directory 위치로 state를 표현한다.

- `decks/<name>/` — active
- `decks/_backlog/<name>/` — backlog
- `decks/_archive/<name>/` — archive
- `decks/` 직하위의 `_` prefix directory는 deck이 아닌 관리 namespace로 예약한다.

Filesystem이 아닌 storage를 사용하면 해당 storage의 policy에 따라 같은 state semantics를 표현한다.

## Naming

Filesystem deck directory name은 다음 형식을 기본으로 한다.

```text
<domain>[-<subdomain>]-<topic>[-<extension>...]
```

- `-`는 의미 필드의 경계를 구분한다.
- `_`는 하나의 필드 안에서 띄어쓰기를 표현한다.
- `subdomain`과 `extension`은 필요한 경우에만 사용한다.
- 현재 구분할 필요가 없는 난이도나 범위 suffix를 선제적으로 붙이지 않는다.

예: `language-c`, `data_engineering-duckdb_python`.

## Content

- Filesystem deck에서는 `README.md`를 entrypoint로 둔다.
- deck 내부 link는 relative path를 우선한다.
- movable deck 내부에는 repository 위치에 의존하는 공통 정책 link를 두지 않는다.
- directory와 file은 현재 content가 요구할 때 만든다. 예상되는 미래 구조를 미리 만들지 않는다.
- 공통 repository policy를 deck마다 복사하지 않는다.

## Boundary

Deck content는 해당 deck의 목표와 학습 내용만 설명한다. repository 전체의 운영 정책은 `docs/`가 담당하고, agent 실행
규칙의 canonical source는 `.agentsmesh/`가 담당한다.
