from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pyiceberg.catalog import Catalog, load_catalog

TABLE_ID = "tutorial.orders"


def warehouse_root() -> Path:
    configured = os.environ.get("ICEBERG_WAREHOUSE")
    project_root = Path(__file__).resolve().parents[1]
    return Path(configured).resolve() if configured else project_root / "warehouse"


def load_lab_catalog() -> Catalog:
    root = warehouse_root()
    return load_catalog(
        "local",
        type="sql",
        uri=f"sqlite:///{root / 'pyiceberg_catalog.db'}",
        warehouse=f"file://{root}",
    )


def files_under_warehouse() -> list[str]:
    root = warehouse_root()
    if not root.exists():
        return []
    return sorted(str(path.relative_to(root)) for path in root.rglob("*") if path.is_file())


def read_state() -> dict[str, Any]:
    root = warehouse_root()
    if not (root / "pyiceberg_catalog.db").exists():
        return {"table": False, "files": files_under_warehouse()}

    catalog = load_lab_catalog()
    if not catalog.table_exists(TABLE_ID):
        return {"table": False, "files": files_under_warehouse()}

    table = catalog.load_table(TABLE_ID)
    return {
        "table": True,
        "schema": [(field.field_id, field.name, str(field.field_type)) for field in table.schema().fields],
        "snapshots": [snapshot.snapshot_id for snapshot in table.snapshots()],
        "rows": table.scan().to_arrow().to_pylist(),
        "files": files_under_warehouse(),
    }


def print_state() -> None:
    current = read_state()
    if not current["table"]:
        print("table     : 없음")
    else:
        print(f"schema    : {current['schema']}")
        print(f"snapshots : {current['snapshots']}")
        print(f"rows      : {current['rows']}")
    print("files:")
    for path in current["files"]:
        print(f"  - {path}")
