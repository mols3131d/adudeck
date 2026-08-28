from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any

import pendulum
from airflow.sdk import dag, get_current_context, task

OUTPUT_DIR = Path(os.environ.get("ADUDECK_AIRFLOW_OUTPUT_DIR", "/tmp/adudeck-airflow-output"))


def _safe(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)


def _render(value: Any) -> str | None:
    return None if value is None else str(value)


@dag(
    dag_id="adudeck_observable_schedule",
    schedule="*/2 * * * *",
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,
    tags=["adudeck", "observable"],
)
def observable_schedule():
    @task
    def expose_interval() -> str:
        context = get_current_context()
        ti = context["ti"]
        dag_run = context["dag_run"]
        snapshot = {
            "dag_id": getattr(ti, "dag_id", None),
            "run_id": getattr(ti, "run_id", None),
            "task_id": getattr(ti, "task_id", None),
            "try_number": getattr(ti, "try_number", None),
            "logical_date": _render(getattr(dag_run, "logical_date", None)),
            "data_interval_start": _render(context.get("data_interval_start")),
            "data_interval_end": _render(context.get("data_interval_end")),
        }

        print(
            "[ADUDECK_OBSERVE] scheduled interval: "
            f"{json.dumps(snapshot, ensure_ascii=False, sort_keys=True)}"
        )
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"schedule-{_safe(str(snapshot['run_id']))}.json"
        output_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))

        # Keep the task running long enough to inspect Grid/CLI/metadata while it is RUNNING.
        time.sleep(20)
        print(f"[ADUDECK_OBSERVE] interval snapshot persisted: {output_path}")
        return str(output_path)

    expose_interval()


observable_schedule()
