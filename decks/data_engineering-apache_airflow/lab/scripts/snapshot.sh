#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "usage: bash lab/scripts/snapshot.sh <dag_id> [run_id]" >&2
  exit 2
fi

DAG_ID="$1"
RUN_ID="${2:-}"

echo "== Dag runs: ${DAG_ID} =="
bash "${LAB_DIR}/airflow.sh" dags list-runs "${DAG_ID}" -o table

if [[ -n "${RUN_ID}" ]]; then
  echo
  echo "== TaskInstance states: ${RUN_ID} =="
  bash "${LAB_DIR}/airflow.sh" tasks states-for-dag-run "${DAG_ID}" "${RUN_ID}" -o table

  echo
  echo "== Read-only metadata probe: ${RUN_ID} =="
  python "${LAB_DIR}/inspect_metadata.py" --dag-id "${DAG_ID}" --run-id "${RUN_ID}"
else
  echo
  echo "== Read-only metadata probe: recent rows =="
  python "${LAB_DIR}/inspect_metadata.py" --dag-id "${DAG_ID}"
fi

echo
echo "== Recent external outputs =="
if [[ -d "${LAB_DIR}/output" ]]; then
  find "${LAB_DIR}/output" -maxdepth 3 -type f -print | sort | tail -n 20
else
  echo "(no output directory yet)"
fi
