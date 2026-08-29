from __future__ import annotations

import json

from airflow.sdk import dag, get_current_context, task

DAG_ID = "adudeck_u2_authoring_starter"


def _observe(label: str) -> None:
    context = get_current_context()
    ti = context["ti"]
    dag_run = context["dag_run"]
    logical_date = getattr(dag_run, "logical_date", None)
    snapshot = {
        "dag_id": getattr(ti, "dag_id", None),
        "run_id": getattr(ti, "run_id", None),
        "task_id": getattr(ti, "task_id", None),
        "try_number": getattr(ti, "try_number", None),
        "logical_date": None if logical_date is None else str(logical_date),
    }
    print(f"[ADUDECK_OBSERVE] {label}: {json.dumps(snapshot, ensure_ascii=False, sort_keys=True)}")


@dag(
    dag_id=DAG_ID,
    schedule=None,
    catchup=False,
    tags=["adudeck", "exercise", "u2-authoring"],
)
def u2_authoring_starter():
    """Parser-safe starting point for the U2 authoring/loading investigation."""

    @task
    def inspect_source() -> None:
        _observe("u2:inspect_source")

    @task
    def build_summary() -> None:
        _observe("u2:build_summary")

    first = inspect_source()
    second = build_summary()
    first >> second

    # Learner work:
    # - predict which TaskInstances will exist before triggering the Dag;
    # - add one meaningful task boundary and justify why it deserves independent state/log/retry;
    # - intentionally introduce and repair one parse/load error;
    # - compare "file exists", "Dag is loaded", "DagRun exists", and "TaskInstance ran" as separate states.


u2_authoring_starter()
