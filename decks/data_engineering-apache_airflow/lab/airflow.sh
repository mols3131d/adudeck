#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export AIRFLOW_HOME="${AIRFLOW_HOME:-${LAB_DIR}/.airflow}"
export AIRFLOW__CORE__DAGS_FOLDER="${AIRFLOW__CORE__DAGS_FOLDER:-${LAB_DIR}/dags}"
export AIRFLOW__CORE__LOAD_EXAMPLES="False"
export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS="True"
export ADUDECK_AIRFLOW_OUTPUT_DIR="${ADUDECK_AIRFLOW_OUTPUT_DIR:-${LAB_DIR}/output}"

# Teaching-only defaults for the U5 boundary exercise. They are not real credentials and are
# intentionally scoped to this disposable local wrapper environment.
export AIRFLOW_VAR_ADUDECK_ENVIRONMENT="${AIRFLOW_VAR_ADUDECK_ENVIRONMENT:-local-lab}"
if [[ -z "${AIRFLOW_CONN_ADUDECK_DEMO_API:-}" ]]; then
  export AIRFLOW_CONN_ADUDECK_DEMO_API='{"conn_type":"http","host":"localhost","port":8080,"login":"learner","password":"not-a-secret","extra":{"purpose":"adudeck-u5-boundary-lab"}}'
fi

mkdir -p "${ADUDECK_AIRFLOW_OUTPUT_DIR}"

exec uvx "apache-airflow==3.3.1" "$@"
