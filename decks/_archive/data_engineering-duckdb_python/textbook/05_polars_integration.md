# 05. Polars DataFrame 연동

## Overview

Polars DataFrame을 DuckDB에 복사하지 않고 SQL source로 등록하고, 결과를 다시 Polars DataFrame으로 반환한다.

## DataFrame 등록

### Action

```python
import duckdb
import polars as pl

users_df = pl.DataFrame(
    {
        "user_id": [1, 2, 3],
        "name": ["Kim", "Lee", "Park"],
        "age": [31, 28, 35],
    }
)

with duckdb.connect() as con:
    con.register("users_source", users_df)

    result_df = con.execute(
        """
        SELECT
            user_id,
            name,
            age
        FROM users_source
        WHERE age >= ?
        ORDER BY age DESC
        """,
        [30],
    ).pl()

    con.unregister("users_source")

print(result_df)
```

### Change

`users_source`는 connection 내부의 temporary relation으로 등록된다. 영구 table은 생성되지 않는다.

### Verify

- [ ] 결과에 `Park`, `Kim`이 포함된다.
- [ ] connection 종료 후 `users_source`를 조회할 수 없다.

## DataFrame을 Table로 저장

```python
with duckdb.connect("warehouse.duckdb") as con:
    con.register("users_source", users_df)

    con.execute(
        """
        CREATE OR REPLACE TABLE users AS
        SELECT *
        FROM users_source
        """
    )
```

이 경우 DataFrame 내용이 DuckDB storage에 복사되어 connection 종료 후에도 유지된다.

## SQL 우선 처리

Polars로 전체 데이터를 가져온 뒤 처리하기보다 DuckDB에서 필요한 row와 column만 계산한다.

```python
summary_df = con.sql(
    """
    SELECT
        age,
        COUNT(*) AS user_count
    FROM users_source
    GROUP BY age
    ORDER BY age
    """
).pl()
```

## Pitfalls

- DataFrame column에 혼합 type이 있으면 예상하지 못한 변환이 발생할 수 있다.
- timezone-aware datetime은 저장 전 timezone 정책을 명확히 해야 한다.
- connection 종료 전에 DataFrame relation을 모두 사용해야 한다.
- 큰 결과를 `.pl()`로 반환하면 Python memory 사용량이 증가한다.

## Checklist

- [ ] `register()`와 `unregister()`를 사용할 수 있다.
- [ ] DataFrame relation과 영구 table의 차이를 안다.
- [ ] SQL에서 먼저 filter와 aggregation을 수행한다.
- [ ] DataFrame type과 timezone 변환을 점검한다.
