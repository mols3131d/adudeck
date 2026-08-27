#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export AIRFLOW_HOME="${AIRFLOW_HOME:-${LAB_DIR}/.airflow}"
export AIRFLOW__CORE__DAGS_FOLDER="${AIRFLOW__CORE__DAGS_FOLDER:-${LAB_DIR}/dags}"
export AIRFLOW__CORE__LOAD_EXAMPLES="False"
export AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_ALL_ADMINS="True"
export ADUDECK_AIRFLOW_OUTPUT_DIR="${ADUDECK_AIRFLOW_OUTPUT_DIR:-${LAB_DIR}/output}"

mkdir -p "${ADUDECK_AIRFLOW_OUTPUT_DIR}"

exec uvx "apache-airflow==3.3.1" "$@"
