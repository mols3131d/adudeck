# Notion Policy

## Config

```yaml
database: https://app.notion.com/p/mols3131d/3c113d7e58b980edab91d2d243a7d30c
data_source: collection://3c113d7e-58b9-80af-b3ec-000b05102566
title_property: 이름
state_property: State
states:
  active: Active
  backlog: Backlog
  archive: Archive
```

Notion은 사용자가 현재 deck 또는 작업의 storage로 명시적으로 지정한 경우에만 사용한다. 별도 지정이 없으면 filesystem이
기본이다. Notion이 지정되면 별도 지시가 없는 한 위 database를 사용한다.

## Deck

Notion에서도 deck은 하나의 학습 주제를 다루는 하나의 workspace unit이다.

- 하나의 deck은 하나의 top-level database item/page로 관리한다.
- 필요한 세부 내용은 해당 deck page의 blocks 또는 child pages로 구성할 수 있다.
- 같은 deck을 state별 database나 여러 top-level page로 복제하지 않는다.
- filesystem과 Notion 사이의 mirror, sync, migration은 사용자가 명시적으로 요청한 경우에만 수행한다.

## State

Notion에서는 directory 이동 대신 deck의 state property로 상태를 표현한다.

새 schema를 구성할 때는 config의 `state_property`와 `states`를 기본으로 사용한다.

State가 바뀌면 page를 복사하거나 별도 database로 이동하지 않고 해당 state property를 변경한다.

Notion view의 filter, group, sort는 presentation이다. view나 database 위치를 deck state의 source of truth로 사용하지
않는다.

## Properties

새 schema에서는 최소한 config의 `title_property`와 `state_property`만 요구한다. 다른 properties는 실제 학습 또는 운영
필요가 있을 때만 추가한다.

기존 Notion database가 동일한 의미를 다른 property 이름이나 값으로 이미 표현하고 있다면, 불필요한 schema 변경보다 기존
구조를 우선한다. 단, state 의미는 config의 `states`와 대응되어야 한다.

## Boundary

Notion은 deck storage다. adudeck의 공통 deck 의미와 state semantics는 [`decks.md`](decks.md)를 따르고, Notion 특유의
표현 방식과 기본 storage target만 이 문서가 정의한다.
