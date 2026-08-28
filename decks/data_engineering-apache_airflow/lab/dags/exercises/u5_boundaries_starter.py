from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from airflow.sdk import Connection, Param, Variable, dag, get_current_context, task

DAG_ID = "adudeck_u5_boundaries_starter"
LAB_DIR = Path(__file__).resolve().parents[2]
FIXTURE_PATH = LAB_DIR / "fixtures" / "orders.jsonl"
OUTPUT_DIR = Path(os.environ.get("ADUDECK_AIRFLOW_OUTPUT_DIR", LAB_DIR / "output"))


def _write_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


@dag(
    dag_id=DAG_ID,
    schedule=None,
    catchup=False,
    params={
        "region": Param(
            "all",
            type="string",
            enum=["all", "apac", "emea"],
            description="Per-run input used to choose which fixture rows are processed.",
        )
    },
    tags=["adudeck", "exercise", "u5-boundaries"],
)
def u5_boundaries_starter():
    """Safe baseline for comparing Params, XCom, external data, Variable, and Connection."""

    @task
    def stage_orders() -> str:
        context = get_current_context()
        region = context["params"]["region"]

        rows = [
            json.loads(line)
            for line in FIXTURE_PATH.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        selected = rows if region == "all" else [row for row in rows if row["region"] == region]

        # Business rows stay in external storage; TaskFlow/XCom carries only the path identifier.
        run_id = str(context["dag_run"].run_id).replace("/", "_").replace(":", "_")
        output_path = OUTPUT_DIR / "u5" / f"{run_id}-orders.json"
        _write_json(output_path, {"region": region, "orders": selected})
        print(f"[ADUDECK_OBSERVE] u5 staged business data: {output_path}")
        return str(output_path)

    @task
    def inspect_boundaries(dataset_path: str) -> dict[str, Any]:
        context = get_current_context()
        environment = Variable.get("adudeck_environment", default="local-lab")
        connection = Connection.get("adudeck_demo_api")

        evidence = {
            "run_input_param": context["params"]["region"],
            "xcom_value_kind": "dataset path",
            "dataset_path": dataset_path,
            "global_runtime_variable": environment,
            "connection": {
                "conn_id": connection.conn_id,
                "conn_type": connection.conn_type,
                "host": connection.host,
                "port": connection.port,
            },
        }
        print(
            "[ADUDECK_OBSERVE] u5 boundary evidence: "
            f"{json.dumps(evidence, ensure_ascii=False, sort_keys=True)}"
        )

        # Never add connection passwords or other credentials to logs, XCom, or output.
        return evidence

    @task
    def persist_evidence(evidence: dict[str, Any]) -> str:
        context = get_current_context()
        run_id = str(context["dag_run"].run_id).replace("/", "_").replace(":", "_")
        output_path = OUTPUT_DIR / "u5" / f"{run_id}-boundaries.json"
        print(f"[ADUDECK_OBSERVE] u5 persisted safe evidence: {output_path}")
        return _write_json(output_path, evidence)

    persist_evidence(inspect_boundaries(stage_orders()))

    # Learner work:
    # - explain why `region` is a per-run Param instead of a global Variable in this scenario;
    # - explain why fixture/output data stays in files while XCom carries an identifier;
    # - inspect the demo Connection without printing its password;
    # - change one requirement and decide whether the value belongs in Params, XCom,
    #   external storage, Connection, Variable, or ordinary version-controlled Dag code.


u5_boundaries_starter()
