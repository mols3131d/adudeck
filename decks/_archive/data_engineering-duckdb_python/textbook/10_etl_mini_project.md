# 10. 실전 ETL Mini Project

## Summary

Parquet source를 정제하고 일별 metric table을 생성한 뒤 결과를 Parquet로 export한다.

## 입력과 출력

입력:

```text
data/trips.parquet
```

출력:

```text
warehouse.duckdb
output/daily_trip_metrics.parquet
```

## Pipeline 구현

### Action

`src/duckdb_python_basic/pipeline.py`를 만든다.

```python
from pathlib import Path

import duckdb


DATABASE_PATH = Path("warehouse.duckdb")
INPUT_PATH = Path("data/trips.parquet")
OUTPUT_PATH = Path("output/daily_trip_metrics.parquet")


def build_daily_metrics() -> int:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(INPUT_PATH)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with duckdb.connect(str(DATABASE_PATH)) as con:
        con.execute("BEGIN")

        try:
            con.execute(
                """
                CREATE OR REPLACE TABLE stg_trips AS
                SELECT
                    CAST(trip_id AS BIGINT) AS trip_id,
                    CAST(pickup_date AS DATE) AS pickup_date,
                    CAST(trip_distance AS DOUBLE) AS trip_distance,
                    CAST(fare_amount AS DOUBLE) AS fare_amount
                FROM read_parquet(?)
                WHERE pickup_date IS NOT NULL
                """,
                [str(INPUT_PATH)],
            )

            con.execute(
                """
                CREATE OR REPLACE TABLE daily_trip_metrics AS
                SELECT
                    pickup_date,
                    COUNT(*) AS trip_count,
                    AVG(trip_distance) AS avg_trip_distance,
                    SUM(fare_amount) AS total_fare_amount,
                    COUNT(*) FILTER (
                        WHERE fare_amount IS NULL
                    )::DOUBLE / NULLIF(COUNT(*), 0) AS null_fare_rate
                FROM stg_trips
                GROUP BY pickup_date
                ORDER BY pickup_date
                """
            )

            row_count = con.execute(
                "SELECT COUNT(*) FROM daily_trip_metrics"
            ).fetchone()[0]

            if row_count == 0:
                raise ValueError("daily_trip_metrics is empty")

            con.execute(
                """
                COPY daily_trip_metrics
                TO ?
                (
                    FORMAT PARQUET,
                    COMPRESSION ZSTD
                )
                """,
                [str(OUTPUT_PATH)],
            )

            con.execute("COMMIT")
            return row_count

        except Exception:
            con.execute("ROLLBACK")
            raise


if __name__ == "__main__":
    metric_count = build_daily_metrics()
    print(f"metric_count={metric_count}")
```

### Change

- `stg_trips` table이 재생성된다.
- `daily_trip_metrics` table이 재생성된다.
- `output/daily_trip_metrics.parquet`가 생성된다.

### Verify

```bash
uv run python -m duckdb_python_basic.pipeline
```

```python
import duckdb

with duckdb.connect() as con:
    con.sql(
        """
        SELECT *
        FROM read_parquet('output/daily_trip_metrics.parquet')
        ORDER BY pickup_date
        """
    ).show()
```

## Query Plan 확인

```python
con.sql(
    """
    EXPLAIN ANALYZE
    SELECT
        pickup_date,
        SUM(fare_amount)
    FROM read_parquet('data/trips.parquet')
    GROUP BY pickup_date
    """
).show()
```

확인할 항목:

- 필요한 column만 scan하는가
- filter가 file scan에 적용되는가
- aggregation 전에 불필요한 row가 제거되는가
- 전체 query 시간이 어느 operator에 집중되는가

## Checklist

- [ ] source validation을 수행한다.
- [ ] staging과 metric table의 책임을 구분한다.
- [ ] transaction 안에서 table 생성과 export를 처리한다.
- [ ] empty output을 실패로 처리한다.
- [ ] Parquet 결과를 다시 query해 검증한다.
- [ ] `EXPLAIN ANALYZE`로 실행 plan을 확인한다.
