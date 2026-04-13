#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY_SERVICES=(history physics ai-assistant)
COVERAGE="${COVERAGE:-0}"

for service in "${PY_SERVICES[@]}"; do
  service_dir="${ROOT_DIR}/services/${service}"
  echo "==> Test python/${service}"

  if [[ ! -d "${service_dir}" ]]; then
    echo "Skip ${service}: directory is missing."
    continue
  fi

  (
    cd "${service_dir}"
    if [[ "${COVERAGE}" == "1" ]]; then
      python -m pytest --cov=app --cov-report=term-missing
    else
      python -m pytest
    fi
  )
done

if [[ -d "${ROOT_DIR}/services/math" ]]; then
  echo "==> Test go/math"
  (
    cd "${ROOT_DIR}/services/math"
    go test ./...
  )
fi

if [[ -d "${ROOT_DIR}/services/geography" ]]; then
  echo "==> Test java/geography"
  (
    cd "${ROOT_DIR}/services/geography"
    mvn -B test
  )
fi

if [[ -d "${ROOT_DIR}/frontend" ]]; then
  echo "==> Test frontend build"
  (
    cd "${ROOT_DIR}/frontend"
    npm install
    npm run build
  )
fi

echo "Tests completed."
