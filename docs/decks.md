# Deck Policy

Deck은 하나의 학습 주제를 독립적으로 다루는 이동 가능한 workspace unit이다.

## Lifecycle

- `decks/<name>/`에 있으면 active다.
- 더 이상 현재 학습 대상이 아니면 directory 전체를 `decks/archive/`로 이동한다.
- 학습을 재개하면 기존 directory를 active 위치로 되돌린다.
- archive와 active에 같은 deck을 동시에 두지 않는다.

## Content

- `README.md`를 해당 deck의 entrypoint로 둔다.
- deck 내부 link는 relative path를 우선한다.
- movable deck 내부에는 repository 위치에 의존하는 공통 정책 link를 두지 않는다.
- directory와 file은 현재 content가 요구할 때 만든다. 예상되는 미래 구조를 미리 만들지 않는다.
- 공통 repository policy를 deck마다 복사하지 않는다.

## Boundary

Deck README는 해당 deck의 목표와 content만 설명한다. repository 전체의 운영 정책은 `docs/`가 담당하고, agent 실행 규칙의
canonical source는 `.agentsmesh/`가 담당한다.
