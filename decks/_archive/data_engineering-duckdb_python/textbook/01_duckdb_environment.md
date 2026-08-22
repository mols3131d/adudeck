# 01. DuckDB와 실행 환경

## Overview

이 장에서는 DuckDB가 어떤 역할을 하는지 확인하고, Python 프로세스 내부에서 SQL query를 실행한다.

## 핵심 개념

DuckDB는 별도 서버 없이 application process 안에서 실행되는 분석용 SQL database다. 다음 작업에 적합하다.

- 로컬 Parquet 분석
- ETL 결과 검증
- marimo 또는 Python script의 SQL engine
- 테스트용 embedded database
- dbt-duckdb 기반 로컬 transformation

DuckDB는 OLTP database보다 columnar analytical workload에 초점을 둔다. 대량 `SELECT`, aggregation, join에는 적합하지만
높은 동시성의 row 단위 transaction system을 대체하는 용도는 아니다.

## 첫 SQL 실행

### Action

`src/duckdb_python_basic/first_query.py`를 만든다.

```python
import duckdb


def main() -> None:
    result = duckdb.sql("SELECT 42 AS answer")
    result.show()


if __name__ == "__main__":
    main()
```

실행한다.

```bash
uv run python src/duckdb_python_basic/first_query.py
```

### Change

DuckDB는 process 내부에 기본 in-memory connection을 만들고 query를 실행한다. 영구 database 파일은 생성되지 않는다.

### Verify

출력에 `answer` column과 값 `42`가 표시되는지 확인한다.

## 타입 확인

### Action

```python
import duckdb

relation = duckdb.sql(
    """
    SELECT
        1 AS integer_value,
        1.5 AS decimal_value,
        'duckdb' AS text_value,
        DATE '2026-07-14' AS date_value
    """
)

print(type(relation))
relation.show()
```

### Change

`duckdb.sql()`은 결과 row를 즉시 Python list로 반환하지 않고 `DuckDBPyRelation`을 반환한다.

### Verify

- [ ] 객체 타입에 `DuckDBPyRelation`이 포함된다.
- [ ] 네 개 column의 값과 type이 출력된다.

## Checklist

- [ ] DuckDB가 embedded analytical database인 이유를 설명할 수 있다.
- [ ] `duckdb.sql()`로 query를 실행할 수 있다.
- [ ] in-memory 실행과 파일 database의 차이를 알고 있다.
- [ ] DuckDB를 OLTP database 대체재로 보지 않는다.
