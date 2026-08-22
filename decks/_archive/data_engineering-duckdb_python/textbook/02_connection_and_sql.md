# 02. Connection과 SQL 실행

## Summary

반복 query, transaction, table 상태 공유가 필요하면 명시적인 `duckdb.connect()` connection을 사용한다.

## In-memory Connection

### Action

```python
import duckdb

with duckdb.connect(":memory:") as con:
    con.execute(
        """
        CREATE TABLE users (
            user_id INTEGER,
            name VARCHAR
        )
        """
    )

    con.execute(
        """
        INSERT INTO users VALUES
            (1, 'Kim'),
            (2, 'Lee')
        """
    )

    con.sql("SELECT * FROM users ORDER BY user_id").show()
```

### Change

`users` table은 현재 connection의 in-memory database에 생성된다.

### Verify

process를 다시 실행했을 때 이전 table이 남지 않는지 확인한다.

## 파일 기반 Database

### Action

`src/duckdb_python_basic/connection.py`를 만든다.

```python
from pathlib import Path

import duckdb


def connect_database(
    database_path: Path,
    *,
    read_only: bool = False,
) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(
        database=str(database_path),
        read_only=read_only,
    )
```

사용한다.

```python
from pathlib import Path

from duckdb_python_basic.connection import connect_database


database_path = Path("warehouse.duckdb")

with connect_database(database_path) as con:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            event_id BIGINT,
            event_type VARCHAR,
            created_at TIMESTAMP
        )
        """
    )
```

### Change

project root에 `warehouse.duckdb` 파일이 생성된다.

### Verify

```bash
ls -lh warehouse.duckdb
```

다시 연결해 table이 유지되는지 확인한다.

```python
with connect_database(database_path, read_only=True) as con:
    con.sql("SHOW TABLES").show()
```

## `execute()`와 `sql()`

| API | 적합한 용도 | 반환 형태 |
| :--- | :--- | :--- |
| `con.execute()` | DB-API 스타일 실행, parameter binding | connection/result cursor |
| `con.sql()` | relation 기반 query 구성 | `DuckDBPyRelation` |
| `duckdb.sql()` | 간단한 단발성 query | global connection relation |

## Checklist

- [ ] in-memory connection을 생성할 수 있다.
- [ ] 파일 기반 database를 생성하고 다시 열 수 있다.
- [ ] `with` statement로 connection lifecycle을 관리한다.
- [ ] 분석 전용 연결에 `read_only=True`를 사용할 수 있다.
- [ ] `execute()`와 `sql()`의 사용 목적을 구분할 수 있다.
