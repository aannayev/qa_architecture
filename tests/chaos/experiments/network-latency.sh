#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TARGET="${TARGET_ENDPOINT:-/api/history/readyz}"
REQUESTS="${REQUESTS:-20}"
MAX_FAILURE_RATE="${MAX_FAILURE_RATE:-0.20}"

fail=0
for _ in $(seq 1 "${REQUESTS}"); do
  code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 3 "${BASE_URL}${TARGET}" || echo "000")
  if [[ "${code}" != "200" ]]; then
    fail=$((fail + 1))
  fi
done

failure_rate=$(awk "BEGIN { printf \"%.2f\", ${fail}/${REQUESTS} }")
echo "Chaos baseline result: failures=${fail}/${REQUESTS} failure_rate=${failure_rate}"

if awk "BEGIN { exit !(${failure_rate} <= ${MAX_FAILURE_RATE}) }"; then
  echo "Chaos check passed."
else
  echo "Chaos check failed."
  exit 1
fi
