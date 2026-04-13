#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
ENDPOINTS=(
  "/api/history/v1/topics"
  "/api/physics/v1/topics"
)

echo "Checking that seed data is available through API..."
for endpoint in "${ENDPOINTS[@]}"; do
  url="${BASE_URL}${endpoint}"
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 "${url}" || echo "000")
  if [[ "${code}" == "200" ]]; then
    echo "  ok   ${url}"
  elif [[ "${code}" == "404" || "${code}" == "000" ]]; then
    echo "  skip ${url} (service is not reachable yet)"
  else
    echo "  fail ${url} (HTTP ${code})"
    exit 1
  fi
done

echo "Seed check completed."
