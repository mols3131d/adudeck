#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAB_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
AIRFLOW_PYTHON_VERSION="${ADUDECK_AIRFLOW_PYTHON:-3.12}"

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
echo "== Local source import-error surface =="
echo "This check parses local source without treating serialized DB content as the source of truth."
if IMPORT_ERRORS_JSON="$(bash "${LAB_DIR}/airflow.sh" dags list-import-errors --local -o json)"; then
  printf '%s\n' "${IMPORT_ERRORS_JSON}"
  NORMALIZED_IMPORT_ERRORS="$(tr -d '[:space:]' <<<"${IMPORT_ERRORS_JSON}")"
  if [[ "${NORMALIZED_IMPORT_ERRORS}" == "[]" ]]; then
    pass "local source has no reported import errors"
  else
    fail "local source has import errors; inspect the JSON above before creating runtime state"
  fi
else
  fail "could not evaluate local source import errors"
fi

echo
if (( FAILURES > 0 )); then
  echo "Preflight found ${FAILURES} blocking problem(s). Fix them before starting the learning loop." >&2
  exit 1
fi

echo "Preflight complete. No metadata schema or scheduler-backed runtime has been claimed yet."
echo "Next: run `bash lab/airflow.sh db migrate`, then verify expected Dags as described in lab/README.md."
