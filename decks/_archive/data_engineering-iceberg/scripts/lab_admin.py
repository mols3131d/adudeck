from __future__ import annotations

import argparse
import os
import shutil
import time
from pathlib import Path
from typing import Any

from pyiceberg.catalog import Catalog, load_catalog
from pyiceberg.table import Table

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


def snapshot_ids(table: Table) -> list[int]:
    return [snapshot.snapshot_id for snapshot in table.snapshots()]


def state() -> dict[str, Any]:
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
        "snapshots": snapshot_ids(table),
        "rows": table.scan().to_arrow().to_pylist(),
        "files": files_under_warehouse(),
    }


def print_state() -> None:
    current = state()
    if not current["table"]:
        print("table     : 없음")
    else:
        print(f"schema    : {current['schema']}")
        print(f"snapshots : {current['snapshots']}")
        print(f"rows      : {current['rows']}")
    print("files:")
    for path in current["files"]:
        print(f"  - {path}")


def reset() -> None:
    root = warehouse_root()
    print(f"ACTION   : 실습 상태 초기화 ({root})")
    print("CHANGE   : SQLite Catalog와 warehouse 파일 제거")
    if root.exists():
        shutil.rmtree(root)
    print(f"VERIFY   : warehouse 디렉터리 없음 = {not root.exists()}")


def status() -> None:
    print("ACTION   : 현재 실습 상태 읽기")
    print("CHANGE   : 없음")
    print_state()


def watch(interval: float) -> None:
    print("상태를 반복해서 읽습니다. 종료: Ctrl+C")
    try:
        while True:
            print("\033[2J\033[H", end="")
            status()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n관찰을 종료했습니다.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Iceberg 실습 상태 초기화·관찰 도구")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("reset", help="실습 상태를 삭제합니다")
    subparsers.add_parser("status", help="현재 상태를 읽습니다")
    watch_parser = subparsers.add_parser("watch", help="현재 상태를 반복해서 읽습니다")
    watch_parser.add_argument("--interval", type=float, default=1.0)
    args = parser.parse_args()

    if args.command == "reset":
        reset()
    elif args.command == "status":
        status()
    else:
        watch(args.interval)


if __name__ == "__main__":
    main()
