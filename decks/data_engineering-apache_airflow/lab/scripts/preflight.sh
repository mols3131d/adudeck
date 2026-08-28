#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
AIRFLOW_PYTHON_VERSION="${ADUDECK_AIRFLOW_PYTHON:-3.12}"

EXPECTED_DAGS=(
  "adudeck_observable_runtime"
  "adudeck_observable_schedule"
  "adudeck_u2_authoring_starter"
  "adudeck_u5_boundaries_starter"
)

FAILURES=0

pass() {
  printf 'PASS  %s\n' "$1"
}

warn() {
  printf 'WARN  %s\n' "$1"
}

fail() {
  printf 'FAIL  %s\n' "$1" >&2
  FAILURES=$((FAILURES + 1))
}

echo "== Host prerequisites =="

if command -v uv >/dev/null 2>&1; then
  pass "uv available: $(uv --version)"
  pass "lab Python baseline requested through uv: ${AIRFLOW_PYTHON_VERSION}"
else
  fail "uv is required. Install uv before starting this lab."
fi

case "$(uname -s)" in
  Linux|Darwin)
    pass "POSIX host detected: $(uname -s)"
    ;;
  *)
    warn "Airflow is documented for POSIX hosts; on Windows use WSL2 or a Linux environment."
    ;;
esac

if [[ -r "${LAB_DIR}/dags" && -r "${LAB_DIR}/fixtures" && -w "${LAB_DIR}" ]]; then
  pass "lab source is readable and lab directory is writable"
else
  fail "lab source must be readable and the lab directory must be writable"
fi

if command -v lsof >/dev/null 2>&1; then
  if lsof -nP -iTCP:8080 -sTCP:LISTEN >/dev/null 2>&1; then
    warn "TCP port 8080 is already in use; standalone may need the existing process stopped first"
  else
    pass "TCP port 8080 appears available"
  fi
else
  warn "lsof not found; skipping the optional TCP port 8080 check"
fi

if (( FAILURES > 0 )); then
  echo
  echo "Preflight stopped before resolving Airflow because host prerequisites failed." >&2
  exit 1
fi

echo
echo "== Airflow toolchain =="
echo "The wrapper resolves Apache Airflow 3.3.1 with the matching release constraints."
echo "A fresh machine may download Python ${AIRFLOW_PYTHON_VERSION}, the constraints file, and packages on this step."
AIRFLOW_VERSION_OUTPUT="$(bash "${LAB_DIR}/airflow.sh" version)"
printf '%s\n' "${AIRFLOW_VERSION_OUTPUT}"
if grep -Fq "3.3.1" <<<"${AIRFLOW_VERSION_OUTPUT}"; then
  pass "Apache Airflow 3.3.1 resolved through the constrained lab wrapper"
else
  fail "expected Apache Airflow 3.3.1 from lab/airflow.sh"
fi

echo
echo "== Local Dag discovery =="
if DAG_LIST="$(bash "${LAB_DIR}/airflow.sh" dags list --local)"; then
  printf '%s\n' "${DAG_LIST}"
  pass "local Dag discovery command completed"
  for dag_id in "${EXPECTED_DAGS[@]}"; do
    if grep -Fq "${dag_id}" <<<"${DAG_LIST}"; then
      pass "Dag discovered: ${dag_id}"
    else
      fail "expected Dag not discovered: ${dag_id}"
    fi
  done
else
  fail "local Dag discovery failed; inspect the command output above"
fi

echo
echo "== Local import-error surface =="
if bash "${LAB_DIR}/airflow.sh" dags list-import-errors --local -o table; then
  pass "local import-error inspection command completed"
else
  fail "could not inspect local import errors"
fi

echo
if (( FAILURES > 0 )); then
  echo "Preflight found ${FAILURES} blocking problem(s). Fix them before starting the learning loop." >&2
  exit 1
fi

echo "Preflight complete. The environment is ready for the next verification layer."
echo "Next: use the verification ladder in lab/README.md before starting standalone."
