# 08. Transaction과 Idempotent Ingestion

## Summary

Partition overwrite는 `DELETE → INSERT → 검증`을 하나의 transaction으로 묶어 재실행 시 중복과 중간 상태를 방지한다.

## Transaction 기본

```python
with duckdb.connect("warehouse.duckdb") as con:
    try:
        con.execute("BEGIN")
        con.execute("DELETE FROM target_table WHERE partition_date = ?", ["2026-07-14"])
        con.execute("INSERT INTO target_table SELECT * FROM source_table")
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
```

## Ingestion 함수

### Action

`src/duckdb_python_basic/ingestion.py`를 만든다.

```python
from pathlib import Path

import duckdb


def ingest_trip_partition(
    con: duckdb.DuckDBPyConnection,
    parquet_path: Path,
    pickup_date: str,
) -> int:
    if not parquet_path.exists():
        raise FileNotFoundError(parquet_path)

    con.execute("BEGIN")

    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS raw_trips (
                trip_id BIGINT,
                trip_distance DOUBLE,
                fare_amount DOUBLE,
                pickup_date DATE
            )
            """
        )

        con.execute(
            """
            DELETE FROM raw_trips
            WHERE pickup_date = CAST(? AS DATE)
            """,
            [pickup_date],
        )

        con.execute(
            """
            INSERT INTO raw_trips
            SELECT
                trip_id,
                trip_distance,
                fare_amount,
                CAST(? AS DATE) AS pickup_date
            FROM read_parquet(?)
            """,
            [pickup_date, str(parquet_path)],
        )

        inserted_count = con.execute(
            """
            SELECT COUNT(*)
            FROM raw_trips
            WHERE pickup_date = CAST(? AS DATE)
            """,
            [pickup_date],
        ).fetchone()[0]

        if inserted_count == 0:
            raise ValueError(f"Empty partition: {pickup_date}")

        con.execute("COMMIT")
        return inserted_count

    except Exception:
        con.execute("ROLLBACK")
        raise
```

### Change

같은 날짜를 다시 실행하면 기존 partition을 삭제하고 동일 source로 교체한다.

### Verify

```python
from pathlib import Path

import duckdb

from duckdb_python_basic.ingestion import ingest_trip_partition


with duckdb.connect("warehouse.duckdb") as con:
    first_count = ingest_trip_partition(
        con,
        Path("data/trips.parquet"),
        "2026-07-14",
    )
    second_count = ingest_trip_partition(
        con,
        Path("data/trips.parquet"),
        "2026-07-14",
    )

    stored_count = con.execute(
        """
        SELECT COUNT(*)
        FROM raw_trips
        WHERE pickup_date = DATE '2026-07-14'
        """
    ).fetchone()[0]

assert first_count == second_count == stored_count
```

## Trade-offs

`DELETE + INSERT`는 구현이 단순하고 local MVP에 적합하다. 대규모 dataset에서는 partition file 교체, table format
snapshot, staging table swap 같은 방법이 더 효율적일 수 있다.

## Checklist

- [ ] `BEGIN`, `COMMIT`, `ROLLBACK`을 사용할 수 있다.
- [ ] partition overwrite가 idempotent한 이유를 설명할 수 있다.
- [ ] ingestion 중간 상태가 남지 않도록 transaction을 사용한다.
- [ ] 입력 파일 존재와 적재 row count를 검증한다.
