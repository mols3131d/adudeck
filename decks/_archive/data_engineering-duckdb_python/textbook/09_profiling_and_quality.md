# 09. Profiling과 데이터 품질 검사

## Overview

Row count, null rate, schema, freshness를 query로 계산해 partition 상태를 관찰한다.

## Profile Model

### Action

`src/duckdb_python_basic/profiling.py`를 만든다.

```python
from dataclasses import dataclass
from datetime import datetime

import duckdb


@dataclass(frozen=True)
class ProfileResult:
    row_count: int
    null_fare_rate: float
    min_pickup_at: datetime | None
    max_pickup_at: datetime | None


def profile_partition(
    con: duckdb.DuckDBPyConnection,
    pickup_date: str,
) -> ProfileResult:
    row = con.execute(
        """
        SELECT
            COUNT(*) AS row_count,
            COUNT(*) FILTER (
                WHERE fare_amount IS NULL
            )::DOUBLE / NULLIF(COUNT(*), 0) AS null_fare_rate,
            MIN(pickup_at) AS min_pickup_at,
            MAX(pickup_at) AS max_pickup_at
        FROM raw_trips
        WHERE pickup_date = CAST(? AS DATE)
        """,
        [pickup_date],
    ).fetchone()

    if row is None:
        raise RuntimeError("Profile query returned no row")

    return ProfileResult(
        row_count=row[0],
        null_fare_rate=row[1] or 0.0,
        min_pickup_at=row[2],
        max_pickup_at=row[3],
    )
```

### Change

partition의 품질 지표가 Python dataclass로 구조화된다.

### Verify

```python
with duckdb.connect("warehouse.duckdb", read_only=True) as con:
    profile = profile_partition(con, "2026-07-14")

assert profile.row_count > 0
assert 0.0 <= profile.null_fare_rate <= 1.0
```

## Schema 검사

```python
schema_rows = con.execute(
    """
    SELECT
        column_name,
        data_type,
        is_nullable
    FROM information_schema.columns
    WHERE table_schema = 'main'
      AND table_name = 'raw_trips'
    ORDER BY ordinal_position
    """
).fetchall()
```

간단한 schema signature:

```python
import hashlib
import json

payload = json.dumps(schema_rows, sort_keys=True).encode("utf-8")
schema_hash = hashlib.sha256(payload).hexdigest()
```

## 기본 Detection 예시

```python
def detect_row_count_drop(
    baseline_count: int,
    current_count: int,
    threshold_ratio: float = 0.7,
) -> bool:
    if baseline_count <= 0:
        raise ValueError("baseline_count must be positive")

    return current_count < baseline_count * threshold_ratio
```

Profile은 evidence이고 detection은 기준선과 비교한 판단이다. 두 책임을 분리한다.

## Checklist

- [ ] row count와 null rate를 계산할 수 있다.
- [ ] `NULLIF`로 zero division을 방지한다.
- [ ] schema metadata를 조회하고 hash를 만들 수 있다.
- [ ] profiling과 detection의 책임을 구분한다.
- [ ] read-only connection으로 분석 코드를 실행한다.
