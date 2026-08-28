from __future__ import annotations

import json
import os
import re
import time
from datetime import timedelta
from pathlib import Path
from typing import Any

import pendulum
from airflow.sdk import Param, dag, get_current_context, task

OUTPUT_DIR = Path(os.environ.get("ADUDECK_AIRFLOW_OUTPUT_DIR", "/tmp/adudeck-airflow-output"))


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _runtime_snapshot() -> dict[str, Any]:
    context = get_current_context()
    ti = context["ti"]
    dag_run = context["dag_run"]

    def render(value: Any) -> str | None:
        return None if value is None else str(value)

    return {
        "dag_id": getattr(ti, "dag_id", None),
        "run_id": getattr(ti, "run_id", None),
        "task_id": getattr(ti, "task_id", None),
        "try_number": getattr(ti, "try_number", None),
        "task_state": render(getattr(ti, "state", None)),
        "logical_date": render(getattr(dag_run, "logical_date", None)),
        "data_interval_start": render(context.get("data_interval_start")),
        "data_interval_end": render(context.get("data_interval_end")),
    }


def _observe(label: str) -> dict[str, Any]:
    snapshot = _runtime_snapshot()
    print(f"[ADUDECK_OBSERVE] {label}: {json.dumps(snapshot, ensure_ascii=False, sort_keys=True)}")
    return snapshot


@dag(
    dag_id="adudeck_observable_runtime",
    schedule=None,
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    params={
        "failure_mode": Param(
            "once",
            type="string",
            enum=["none", "once", "always"],
            description="none=성공, once=첫 시도만 실패, always=모든 시도 실패",
        )
    },
    tags=["adudeck", "observable"],
)
def observable_runtime():
    @task
    def prepare() -> str:
        snapshot = _observe("prepare:start")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        run_key = _safe(str(snapshot["run_id"]))
        path = OUTPUT_DIR / f"{run_key}-manifest.json"
        path.write_text(
            json.dumps(
                {
                    "stage": "prepared",
                    "runtime": snapshot,
                    "orders": [101, 102, 103],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print(f"[ADUDECK_OBSERVE] prepare wrote external side effect: {path}")
        time.sleep(8)
        _observe("prepare:end")
        return str(path)

    @task(retries=1, retry_delay=timedelta(seconds=15))
    def transform(manifest_path: str) -> str:
        context = get_current_context()
        snapshot = _observe("transform:start")
        failure_mode = context["params"]["failure_mode"]
        try_number = int(snapshot["try_number"] or 0)

        print(
            "[ADUDECK_OBSERVE] transform decision: "
            f"failure_mode={failure_mode}, try_number={try_number}"
        )
        time.sleep(8)

        if failure_mode == "always" or (failure_mode == "once" and try_number == 1):
            raise RuntimeError(
                "intentional lab failure: observe failed/up_for_retry state before changing anything"
            )

        manifest = json.loads(Path(manifest_path).read_text())
        output_path = OUTPUT_DIR / f"{_safe(str(snapshot['run_id']))}-transformed.json"
        output_path.write_text(
            json.dumps(
                {
                    "stage": "transformed",
                    "source": manifest_path,
                    "runtime": snapshot,
                    "order_count": len(manifest["orders"]),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print(f"[ADUDECK_OBSERVE] transform wrote external side effect: {output_path}")
        _observe("transform:end")
        return str(output_path)

    @task
    def publish(transformed_path: str) -> str:
        snapshot = _observe("publish:start")
        transformed = json.loads(Path(transformed_path).read_text())
        output_path = OUTPUT_DIR / f"{_safe(str(snapshot['run_id']))}-published.json"
        output_path.write_text(
            json.dumps(
                {
                    "stage": "published",
                    "source": transformed_path,
                    "runtime": snapshot,
                    "order_count": transformed["order_count"],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print(f"[ADUDECK_OBSERVE] publish wrote external side effect: {output_path}")
        time.sleep(8)
        _observe("publish:end")
        return str(output_path)

    publish(transform(prepare()))


observable_runtime()
