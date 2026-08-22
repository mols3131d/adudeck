# 03. Query 결과 처리

## Overview

이 장에서는 DuckDB query 결과를 tuple, Polars DataFrame, Arrow table로 변환하고 Relation API를 사용한다.

## Row Fetching

### Action

```python
import duckdb

with duckdb.connect() as con:
    result = con.execute(
        """
        SELECT *
        FROM VALUES
            (1, 'A'),
            (2, 'B'),
            (3, 'C')
        AS t(id, name)
        ORDER BY id
        """
    )

    rows = result.fetchall()
    print(rows)
```

### Change

SQL 결과가 Python의 `list[tuple]`로 materialize된다.

### Verify

```text
[(1, 'A'), (2, 'B'), (3, 'C')]
```

## 단일 Row 조회

```python
row = con.execute(
    "SELECT COUNT(*) AS row_count FROM range(10)"
).fetchone()

assert row is not None
print(row[0])
```

`fetchone()`은 결과가 없으면 `None`을 반환할 수 있으므로 type과 존재 여부를 확인한다.

## Polars와 Arrow 변환

```python
relation = con.sql(
    """
    SELECT
        value,
        value * 10 AS multiplied
    FROM range(5) AS t(value)
    """
)

polars_df = relation.pl()
arrow_table = relation.arrow()

print(polars_df)
print(arrow_table.schema)
```

## Relation API

### Action

```python
relation = (
    con.sql("SELECT * FROM range(10) AS t(value)")
    .filter("value >= 5")
    .project("value, value * value AS squared")
    .order("value DESC")
)

relation.show()
```

### Change

query logic이 relation chain으로 구성된다. 실제 결과가 필요할 때 `show()`, `fetchall()`, `pl()` 등으로 materialize한다.

### Verify

- [ ] `value`는 5 이상이다.
- [ ] `squared`는 `value * value`와 같다.
- [ ] 내림차순으로 정렬된다.

## 메모리 주의사항

`fetchall()`과 `.pl()`은 전체 결과를 Python memory로 가져온다. 대량 결과는 다음 중 하나로 처리한다.

- SQL에서 먼저 filter와 aggregation 수행
- `COPY`로 Parquet export
- `fetchmany()`로 batch 처리
- Arrow 기반 downstream 처리

## Checklist

- [ ] `fetchone()`, `fetchall()`, `fetchmany()`를 구분한다.
- [ ] query 결과를 Polars와 Arrow로 변환할 수 있다.
- [ ] Relation API의 filter, project, order를 사용할 수 있다.
- [ ] 대량 결과를 무조건 DataFrame으로 변환하지 않는다.
