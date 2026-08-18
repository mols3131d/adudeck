# Docs

`docs/`에는 **repository-wide human-facing policy와 운영 설명**만 둔다.

## Index

- [`decks.md`](decks.md) — deck lifecycle, content, 이동 원칙
- [`automation.md`](automation.md) — local automation, CI, cloud/API 비용 경계

## Placement

- 특정 directory 사용법 → 그 directory의 `README.md`
- repository 전체에 적용되는 이유·정책 → `docs/`
- agent가 실행 중 반드시 따라야 하는 portable rule → `.agentsmesh/`
- generated target file → 문서 source로 사용하지 않고 직접 수정하지 않음

같은 내용을 여러 곳에 복사하지 않는다. 가까운 문서는 짧게 설명하고, 세부 정책은 canonical 문서로 link한다.
