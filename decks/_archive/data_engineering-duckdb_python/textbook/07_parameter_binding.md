# 07. Parameter Binding과 안전한 SQL

## Overview

값은 SQL 문자열에 직접 삽입하지 않고 parameter binding으로 전달한다. Table name과 column name 같은 identifier는
allowlist로 검증한다.

## 값 Binding

### Action

```python
import duckdb

with duckdb.connect() as con:
    con.execute(
        """
        CREATE TABLE users (
            user_id INTEGER,
            name VARCHAR
        )
        """
    )

    con.execute(
        "INSERT INTO users VALUES (?, ?)",
        [1, "Kim"],
    )

    row = con.execute(
        "SELECT * FROM users WHERE user_id = ?",
        [1],
    ).fetchone()

print(row)
```

### Change

DuckDB driver가 Python 값을 SQL type으로 변환하고 query와 값을 분리해 처리한다.

### Verify

`(1, 'Kim')`이 반환되는지 확인한다.

## Batch Insert

```python
rows = [
    (1, "Kim"),
    (2, "Lee"),
    (3, "Park"),
]

con.executemany(
    "INSERT INTO users VALUES (?, ?)",
    rows,
)
```

대규모 데이터는 `executemany()`보다 DataFrame, Arrow 또는 Parquet 기반 bulk load가 일반적으로 효율적이다.

## Identifier 검증

parameter binding은 column name이나 table name에 사용할 수 없다.

```python
allowed_columns = {"user_id", "name"}
selected_column = "name"

if selected_column not in allowed_columns:
    raise ValueError(f"Invalid column: {selected_column}")

query = f"SELECT {selected_column} FROM users"
rows = con.execute(query).fetchall()
```

사용자 입력을 검증하지 않고 f-string identifier로 넣지 않는다.

## 날짜와 파일 경로 Binding

```python
row = con.execute(
    """
    SELECT COUNT(*)
    FROM read_parquet(?)
    WHERE pickup_date = CAST(? AS DATE)
    """,
    ["data/trips.parquet", "2026-07-14"],
).fetchone()
```

## Checklist

- [ ] 값에 `?` parameter binding을 사용한다.
- [ ] identifier와 value parameter의 차이를 안다.
- [ ] 동적 identifier는 allowlist로 검증한다.
- [ ] 대량 입력에 row-by-row insert를 남용하지 않는다.
