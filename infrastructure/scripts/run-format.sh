#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICES=(history physics)

for service in "${SERVICES[@]}"; do
  service_dir="${ROOT_DIR}/services/${service}"
  echo "==> Format ${service}"

  if [[ ! -d "${service_dir}" ]]; then
    echo "Skip ${service}: directory is missing."
    continue
  fi

  (
    cd "${service_dir}"
    python -m ruff format app tests
    python -m ruff check --fix app tests
  )
done

echo "Format completed."
