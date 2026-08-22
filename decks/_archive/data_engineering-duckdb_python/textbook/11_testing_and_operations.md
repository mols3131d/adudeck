# 11. 테스트와 운영 패턴

## Overview

DuckDB pipeline의 핵심은 query 실행 성공이 아니라 재실행 가능성, 결과 검증, connection 책임 분리다.

## Ingestion Test

### Action

`tests/test_ingestion.py`를 만든다.

```python
from pathlib import Path

import duckdb
import polars as pl

from duckdb_python_basic.ingestion import ingest_trip_partition


def test_ingestion_is_idempotent(tmp_path: Path) -> None:
    source_path = tmp_path / "trips.parquet"
    database_path = tmp_path / "test.duckdb"

    pl.DataFrame(
        {
            "trip_id": [1, 2],
            "trip_distance": [2.0, 5.0],
            "fare_amount": [10.0, 20.0],
        }
    ).write_parquet(source_path)

    with duckdb.connect(str(database_path)) as con:
        first = ingest_trip_partition(
            con,
            source_path,
            "2026-07-14",
        )
        second = ingest_trip_partition(
            con,
            source_path,
            "2026-07-14",
        )

        stored = con.execute(
            """
            SELECT COUNT(*)
            FROM raw_trips
            WHERE pickup_date = DATE '2026-07-14'
            """
        ).fetchone()[0]

    assert first == 2
    assert second == 2
    assert stored == 2
```

### Change

test마다 temporary directory와 독립 database를 사용한다.

### Verify

```bash
uv run pytest tests/test_ingestion.py -q
```

## Profiling Test

`tests/test_profiling.py`:

```python
import duckdb

from duckdb_python_basic.profiling import profile_partition


def test_profile_partition() -> None:
    with duckdb.connect() as con:
        con.execute(
            """
            CREATE TABLE raw_trips AS
            SELECT *
            FROM VALUES
                (1, TIMESTAMP '2026-07-14 01:00:00', 10.0, DATE '2026-07-14'),
                (2, TIMESTAMP '2026-07-14 02:00:00', NULL, DATE '2026-07-14')
            AS t(trip_id, pickup_at, fare_amount, pickup_date)
            """
        )

        result = profile_partition(con, "2026-07-14")

    assert result.row_count == 2
    assert result.null_fare_rate == 0.5
```

## 운영 원칙

| 원칙 | 적용 방식 |
| :--- | :--- |
| Reproducibility | input, SQL, output path를 명시한다. |
| Idempotency | partition overwrite 또는 replace semantics를 사용한다. |
| Validation | row count, null rate, schema를 확인한다. |
| Isolation | test마다 별도 database를 사용한다. |
| Read safety | 분석기는 `read_only=True`로 연결한다. |
| Observability | query duration, input count, output count를 기록한다. |

## 자주 발생하는 문제

### Database lock

같은 DuckDB 파일을 여러 writer process가 동시에 열지 않도록 한다. 동시 writer가 필요하면 architecture 자체를 재검토한다.

### Memory 증가

전체 query를 `.df()`나 `fetchall()`로 가져오지 않는다. SQL aggregation 또는 Parquet export를 우선한다.

### Schema drift

`union_by_name=true`만으로 해결하지 않는다. 예상 schema와 실제 schema를 비교하고 incident 또는 validation failure로 처리한다.

### Flaky sampling

동일한 정렬 key가 존재할 수 있는 sampling query에서는 deterministic tie-breaker를 추가한다.

```sql
ORDER BY
    hash(CAST(event_timestamp AS VARCHAR)),
    event_timestamp,
    hash(struct_pack(*))
```

동일 timestamp가 있어도 전체 row signature가 fallback order를 제공한다.

## Checklist

- [ ] temporary database를 사용하는 pytest를 작성할 수 있다.
- [ ] ingestion 재실행 시 row가 중복되지 않는지 검증한다.
- [ ] profile metric의 정확성을 test한다.
- [ ] writer concurrency와 memory materialization 위험을 안다.
- [ ] deterministic ordering으로 flaky test를 방지한다.
