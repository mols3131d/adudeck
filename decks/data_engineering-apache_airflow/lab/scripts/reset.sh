#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

case "${1:-output}" in
  output)
    rm -rf "${LAB_DIR}/output"
    mkdir -p "${LAB_DIR}/output"
    echo "reset external lab output: ${LAB_DIR}/output"
    ;;
  --all)
    echo "Resetting only disposable state owned by this lab."
    printf '%s\n' 'Stop `bash lab/airflow.sh standalone` before using --all.'
    rm -rf "${LAB_DIR}/.airflow" "${LAB_DIR}/output"
    mkdir -p "${LAB_DIR}/output"
    echo "reset Airflow home: ${LAB_DIR}/.airflow"
    echo "reset external lab output: ${LAB_DIR}/output"
    ;;
  *)
    echo "usage: bash lab/scripts/reset.sh [output|--all]" >&2
    exit 2
    ;;
esac
