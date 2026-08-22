# 06. Table과 View 관리

## Summary

Table은 데이터를 저장하고, view는 SQL definition을 저장하며, temporary object는 connection 범위에서만 유지된다.

## Table 생성

### Action

```python
from pathlib import Path

from duckdb_python_basic.connection import connect_database


with connect_database(Path("warehouse.duckdb")) as con:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS trips (
            trip_id BIGINT,
            pickup_at TIMESTAMP,
            dropoff_at TIMESTAMP,
            passenger_count INTEGER,
            trip_distance DOUBLE,
            fare_amount DECIMAL(12, 2)
        )
        """
    )
```

### Change

`warehouse.duckdb` catalog에 `trips` table이 생성된다.

### Verify

```python
con.sql("DESCRIBE trips").show()
```

## CTAS

```python
con.execute(
    """
    CREATE OR REPLACE TABLE daily_trip_summary AS
    SELECT
        CAST(pickup_at AS DATE) AS pickup_date,
        COUNT(*) AS trip_count,
        AVG(trip_distance) AS avg_trip_distance,
        SUM(fare_amount) AS total_fare
    FROM trips
    GROUP BY pickup_date
    """
)
```

`CREATE TABLE AS SELECT`는 query 결과를 materialize한다.

## View

```python
con.execute(
    """
    CREATE OR REPLACE VIEW long_trips AS
    SELECT *
    FROM trips
    WHERE trip_distance >= 10
    """
)
```

view는 원본 table을 조회하는 SQL definition이다. 원본 데이터 변경이 다음 query에 반영된다.

## Temporary View

```python
con.execute(
    """
    CREATE OR REPLACE TEMP VIEW current_run_trips AS
    SELECT *
    FROM trips
    WHERE CAST(pickup_at AS DATE) = CURRENT_DATE
    """
)
```

connection 종료 시 사라진다.

## Metadata 조회

```python
con.sql("SHOW TABLES").show()

con.sql(
    """
    SELECT
        table_name,
        column_name,
        data_type,
        is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'main'
    ORDER BY table_name, ordinal_position
    """
).show()
```

## Checklist

- [ ] 명시적 schema로 table을 생성할 수 있다.
- [ ] CTAS로 query 결과를 materialize할 수 있다.
- [ ] table, view, temp view의 lifecycle 차이를 설명할 수 있다.
- [ ] `information_schema`로 schema metadata를 조회할 수 있다.
