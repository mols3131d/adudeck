# Apache Iceberg

과거 `prac-datalake` monorepo의 `projects/iceberg_basic`에서 옮겨 보존한 archived deck이다.

Spark, Java, Docker, S3 없이 Apache Iceberg의 핵심 변화를 로컬에서 관찰하는 튜토리얼이다.

## Start

현재 deck directory에서 실행한다.

```bash
uv sync
uv run python scripts/reset_lab.py
uv run python scripts/inspect_lab.py
```

이후 [학습 로드맵](textbook/00_roadmap.md)을 따른다. SQLite Catalog와 Iceberg 파일은 `warehouse/`에 생성된다.
