# 04. CSV와 Parquet 조회

## Summary

DuckDB는 CSV와 Parquet를 table에 적재하지 않고 SQL의 source로 직접 조회할 수 있다.

## CSV 준비

### Action

`data/users.csv`를 만든다.

```csv
user_id,name,age
1,Kim,31
2,Lee,28
3,Park,35
```

조회한다.

```python
import duckdb

with duckdb.connect() as con:
    con.sql(
        """
        SELECT *
        FROM read_csv_auto('data/users.csv')
        WHERE age >= 30
        ORDER BY age DESC
        """
    ).show()
```

### Change

database table은 생성되지 않는다. DuckDB가 query 실행 시 CSV를 읽는다.

### Verify

`Park`, `Kim` 두 row만 출력되는지 확인한다.

## 명시적 CSV Schema

```python
con.sql(
    """
    SELECT *
    FROM read_csv(
        'data/users.csv',
        columns = {
            'user_id': 'INTEGER',
            'name': 'VARCHAR',
            'age': 'INTEGER'
        },
        header = true
    )
    """
).show()
```

운영 ingestion에서는 자동 추론보다 명시적 schema가 안전하다.

## Parquet 생성

### Action

```python
import polars as pl

trips = pl.DataFrame(
    {
        "trip_id": [1, 2, 3, 4],
        "pickup_date": [
            "2026-07-13",
            "2026-07-13",
            "2026-07-14",
            "2026-07-14",
        ],
        "trip_distance": [2.1, 11.3, 4.2, 18.0],
        "fare_amount": [12.0, 52.5, 18.3, 70.0],
    }
)

trips.write_parquet("data/trips.parquet")
```

### Change

`data/trips.parquet`가 생성된다.

### Verify

```python
with duckdb.connect() as con:
    count = con.execute(
        "SELECT COUNT(*) FROM read_parquet('data/trips.parquet')"
    ).fetchone()[0]

assert count == 4
```

## Parquet Query

```python
con.sql(
    """
    SELECT
        pickup_date,
        COUNT(*) AS trip_count,
        AVG(trip_distance) AS avg_distance
    FROM read_parquet('data/trips.parquet')
    WHERE trip_distance > 10
    GROUP BY pickup_date
    ORDER BY pickup_date
    """
).show()
```

## 여러 파일과 Hive Partition

```text
data/trips/
├── pickup_date=2026-07-13/
│   └── part-000.parquet
└── pickup_date=2026-07-14/
    └── part-000.parquet
```

```python
con.sql(
    """
    SELECT
        pickup_date,
        COUNT(*) AS trip_count
    FROM read_parquet(
        'data/trips/**/*.parquet',
        hive_partitioning = true
    )
    GROUP BY pickup_date
    ORDER BY pickup_date
    """
).show()
```

## Trade-offs

| 방식 | 장점 | 주의점 |
| :--- | :--- | :--- |
| 파일 직접 조회 | 적재 단계 없음, 단순함 | 반복 scan 비용 |
| DuckDB table 적재 | 반복 query와 catalog 관리 | storage 중복 |
| `union_by_name` | schema 순서 차이 흡수 | schema drift 은폐 가능 |
| Hive partition | partition pruning 가능 | directory 규칙 필요 |

## Checklist

- [ ] CSV를 직접 조회할 수 있다.
- [ ] CSV schema를 명시할 수 있다.
- [ ] Parquet를 생성하고 조회할 수 있다.
- [ ] glob과 Hive partition을 사용할 수 있다.
- [ ] `union_by_name`의 위험을 설명할 수 있다.
