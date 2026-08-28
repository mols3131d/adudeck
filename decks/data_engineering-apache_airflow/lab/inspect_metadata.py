from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from typing import Iterable

LAB_DIR = Path(__file__).resolve().parent
DEFAULT_AIRFLOW_HOME = Path(os.environ.get("AIRFLOW_HOME", LAB_DIR / ".airflow"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read-only inspection of the local Airflow metadata database."
    )
    parser.add_argument("--dag-id", help="Limit rows to one DAG id.")
    parser.add_argument("--run-id", help="Limit rows to one DAG run id.")
    parser.add_argument("--limit", type=int, default=20, help="Maximum rows per table.")
    return parser.parse_args()


def existing_columns(connection: sqlite3.Connection, table: str) -> set[str]:
    rows = connection.execute(f'PRAGMA table_info("{table}")').fetchall()
    return {row[1] for row in rows}


def format_table(columns: list[str], rows: Iterable[sqlite3.Row]) -> str:
    materialized = [["" if row[column] is None else str(row[column]) for column in columns] for row in rows]
    widths = [len(column) for column in columns]
    for values in materialized:
        for index, value in enumerate(values):
            widths[index] = max(widths[index], min(len(value), 48))

    def line(values: list[str]) -> str:
        clipped = [value if len(value) <= 48 else value[:45] + "..." for value in values]
        return " | ".join(value.ljust(widths[index]) for index, value in enumerate(clipped))

    output = [line(columns), "-+-".join("-" * width for width in widths)]
    output.extend(line(values) for values in materialized)
    return "\n".join(output)


def inspect_table(
    connection: sqlite3.Connection,
    table: str,
    desired_columns: list[str],
    dag_id: str | None,
    run_id: str | None,
    limit: int,
) -> None:
    available = existing_columns(connection, table)
    if not available:
        print(f"\n[{table}] table not found")
        return

    columns = [column for column in desired_columns if column in available]
    predicates: list[str] = []
    params: list[object] = []

    if dag_id and "dag_id" in available:
        predicates.append("dag_id = ?")
        params.append(dag_id)
    if run_id and "run_id" in available:
        predicates.append("run_id = ?")
        params.append(run_id)

    where = f" WHERE {' AND '.join(predicates)}" if predicates else ""
    order_candidates = ["logical_date", "start_date", "queued_at", "timestamp", "run_id"]
    order_column = next((column for column in order_candidates if column in available), None)
    order = f' ORDER BY "{order_column}" DESC' if order_column else ""
    quoted_columns = ", ".join(f'"{column}"' for column in columns)
    query = f'SELECT {quoted_columns} FROM "{table}"{where}{order} LIMIT ?'

    params.append(limit)
    rows = connection.execute(query, params).fetchall()

    print(f"\n[{table}] {len(rows)} row(s)")
    if rows:
        print(format_table(columns, rows))


def main() -> None:
    args = parse_args()
    db_path = DEFAULT_AIRFLOW_HOME / "airflow.db"
    if not db_path.exists():
        raise SystemExit(
            f"metadata database not found: {db_path}\n"
            "Start the lab with `bash lab/airflow.sh standalone` first."
        )

    print(f"metadata db: {db_path}")
    print("mode: read-only observational probe; the metadata schema is an internal implementation surface")

    uri = f"file:{db_path}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row

    try:
        inspect_table(
            connection,
            "dag_run",
            [
                "dag_id",
                "run_id",
                "state",
                "logical_date",
                "data_interval_start",
                "data_interval_end",
                "run_after",
                "queued_at",
                "start_date",
                "end_date",
            ],
            args.dag_id,
            args.run_id,
            args.limit,
        )
        inspect_table(
            connection,
            "task_instance",
            [
                "dag_id",
                "run_id",
                "task_id",
                "map_index",
                "state",
                "try_number",
                "max_tries",
                "queued_dttm",
                "start_date",
                "end_date",
                "duration",
                "hostname",
                "executor",
            ],
            args.dag_id,
            args.run_id,
            args.limit,
        )
        inspect_table(
            connection,
            "xcom",
            [
                "dag_id",
                "run_id",
                "task_id",
                "map_index",
                "key",
                "timestamp",
            ],
            args.dag_id,
            args.run_id,
            args.limit,
        )
    finally:
        connection.close()


if __name__ == "__main__":
    main()
