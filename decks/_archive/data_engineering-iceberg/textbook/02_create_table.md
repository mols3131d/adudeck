# 02. Catalog와 테이블 직접 만들기

## Summary

학습자가 Catalog 연결과 schema를 직접 정의해 빈 Iceberg 테이블을 만듭니다. 이 단계에서는 초기 metadata가 생기지만 snapshot과 Parquet data file은 생기지 않습니다.

## 참조 구조

```text
SQLite Catalog
  └─ tutorial.orders → current metadata JSON
                          ├─ schema
                          └─ snapshots: []
```

Catalog는 실제 주문 행을 저장하는 데이터베이스가 아닙니다. 테이블 이름을 현재 metadata 위치에 연결합니다.

## 1. 공통 Catalog 코드 작성

`src/iceberg_basic/catalog.py`를 만들고 다음 코드를 직접 작성합니다.

```python
from pathlib import Path

from pyiceberg.catalog import Catalog, load_catalog

TABLE_ID = "tutorial.orders"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE_ROOT = PROJECT_ROOT / "warehouse"


def load_lab_catalog() -> Catalog:
    WAREHOUSE_ROOT.mkdir(exist_ok=True)
    return load_catalog(
        "local",
        type="sql",
        uri=f"sqlite:///{WAREHOUSE_ROOT / 'pyiceberg_catalog.db'}",
        warehouse=f"file://{WAREHOUSE_ROOT}",
    )
```

이 함수는 SQLite Catalog와 Iceberg 테이블 파일의 루트를 프로젝트의 `warehouse/`로 고정합니다. `pyiceberg_catalog.db`는 로컬 실습용 Catalog이고 나머지 하위 디렉터리에는 테이블 metadata와 data file이 생성됩니다.

## 2. 테이블 생성 코드 작성

`src/iceberg_basic/create_table.py`를 만듭니다.

```python
from pyiceberg.schema import Schema
from pyiceberg.types import LongType, NestedField, StringType

from iceberg_basic.catalog import TABLE_ID, load_lab_catalog

catalog = load_lab_catalog()

if ("tutorial",) not in catalog.list_namespaces():
    catalog.create_namespace("tutorial")

table = catalog.create_table(
    TABLE_ID,
    schema=Schema(
        NestedField(1, "order_id", LongType(), required=False),
        NestedField(2, "item", StringType(), required=False),
    ),
)

print(table.schema())
```

`NestedField`의 첫 번째 값은 field ID입니다. 이름이나 컬럼 위치와 별개로 컬럼의 정체성을 추적합니다.

## 3. 실행하고 검증

```bash
uv run python -m iceberg_basic.create_table
uv run python scripts/inspect_lab.py
```

- **Action:** `tutorial.orders` namespace와 빈 테이블을 생성합니다.
- **Change:** `warehouse/pyiceberg_catalog.db`와 초기 `metadata/00000-*.metadata.json`이 생성됩니다.
- **Verify:** schema에 field ID 1과 2가 있고, `snapshots : []`, `rows : []`이며 `.parquet` 파일은 없어야 합니다.

## 흔한 실수

- `TableAlreadyExistsError`: 이전 결과가 남았습니다. `uv run python scripts/reset_lab.py` 실행 후 이 장을 다시 진행합니다.
- `ModuleNotFoundError: iceberg_basic`: `uv sync`를 실행했고 파일이 `src/iceberg_basic/` 아래에 있는지 확인합니다.
- namespace를 만들지 않고 테이블부터 만들면 Catalog에 따라 namespace 관련 오류가 발생합니다.

## Checklist

- [ ] Catalog URI와 warehouse 경로의 역할을 구분할 수 있다.
- [ ] schema와 field ID를 직접 정의했다.
- [ ] 빈 테이블에는 metadata가 있지만 snapshot과 Parquet가 없는 것을 확인했다.
