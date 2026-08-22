# 05. schema를 직접 변경하기

## Summary

학습자가 `update_schema()` 트랜잭션으로 nullable 컬럼을 추가합니다. schema metadata는 바뀌지만 기존 Parquet와 append snapshot은 다시 만들어지지 않습니다.

## Field ID가 필요한 이유

Iceberg는 이름이나 위치만으로 컬럼을 식별하지 않습니다.

```text
변경 전                 변경 후
1: order_id long        1: order_id long
2: item string          2: item string
                        3: channel string
```

고유한 field ID가 있으므로 rename과 삭제 후 같은 이름의 새 컬럼 추가를 구분할 수 있습니다.

## 1. schema evolution 코드 작성

`src/iceberg_basic/evolve_schema.py`를 만듭니다.

```python
from pyiceberg.types import StringType

from iceberg_basic.catalog import TABLE_ID, load_lab_catalog

catalog = load_lab_catalog()
table = catalog.load_table(TABLE_ID)

with table.update_schema() as update:
    update.add_column("channel", StringType())

table.refresh()
print(table.schema())
```

## 2. 실행 전후 비교

```bash
uv run python scripts/inspect_lab.py
uv run python -m iceberg_basic.evolve_schema
uv run python scripts/inspect_lab.py
```

- **Action:** nullable 문자열 컬럼 `channel`을 추가합니다.
- **Change:** 새 metadata JSON과 field ID 3이 생깁니다.
- **Verify:** snapshot은 2개, Parquet는 2개로 그대로이고 schema에 `(3, 'channel', 'string')`이 추가되어야 합니다. 기존 3행의 `channel` 값은 `None`입니다.

## 왜 기존 파일을 다시 쓰지 않는가

기존 Parquet에는 `channel` 값이 없습니다. 새 컬럼이 nullable이므로 Iceberg reader는 기존 파일의 누락된 값을 `NULL`로 해석할 수 있습니다. 포맷이 schema 변경을 지원하는 것과 downstream 프로그램이 새 schema를 처리하는 것은 별개의 호환성 문제입니다.

## 흔한 실수

- 파일을 다시 실행하면 이미 존재하는 컬럼 오류가 발생합니다. 이 실습의 변경 파일은 한 번씩만 실행합니다.
- 모든 타입 변경이 안전한 것은 아닙니다. 이 장에서는 nullable 컬럼 추가만 검증합니다.
- partition evolution도 기존 data file을 자동으로 새 배치에 다시 쓰는 작업은 아닙니다.

## Checklist

- [ ] `update_schema()` 트랜잭션을 직접 작성했다.
- [ ] `channel`에 field ID 3이 할당된 것을 확인했다.
- [ ] schema 변경이 snapshot이나 Parquet를 추가하지 않은 것을 확인했다.
- [ ] 기존 행에서 `channel`이 `None`인 이유를 설명할 수 있다.
