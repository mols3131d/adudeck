# Deck Policy

Deck은 하나의 학습 주제를 독립적으로 다루는 이동 가능한 workspace unit이다.

## State

Deck의 현재 상태는 directory 위치로 표현한다.

- `decks/<name>/` — active. 현재 학습하거나 수정·확장 중이다.
- `decks/_backlog/<name>/` — backlog. 현재 active는 아니지만 후속 학습, 보충, 변경 등의 작업 의도가 있다.
- `decks/_archive/<name>/` — archive. 현재 예정된 작업이 없는 inactive deck이다.
- Deck은 작업 의도가 바뀌면 세 상태 사이를 이동할 수 있다.
- 같은 deck을 여러 상태에 동시에 두지 않는다.
- `decks/` 직하위의 `_` prefix directory는 deck이 아닌 관리 namespace로 예약한다.

## Content

- `README.md`를 해당 deck의 entrypoint로 둔다.
- deck 내부 link는 relative path를 우선한다.
- movable deck 내부에는 repository 위치에 의존하는 공통 정책 link를 두지 않는다.
- directory와 file은 현재 content가 요구할 때 만든다. 예상되는 미래 구조를 미리 만들지 않는다.
- 공통 repository policy를 deck마다 복사하지 않는다.

## Boundary

Deck README는 해당 deck의 목표와 content만 설명한다. repository 전체의 운영 정책은 `docs/`가 담당하고, agent 실행 규칙의
canonical source는 `.agentsmesh/`가 담당한다.
