#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
CURL_OPTS=(--noproxy "*" -s -o /dev/null -w '%{http_code}' --max-time 5)
subjects=(history physics math geography)
failed=0

for subject in "${subjects[@]}"; do
  ready_code=$(curl "${CURL_OPTS[@]}" "${BASE_URL}/api/${subject}/readyz" || echo "000")
  if [[ "${ready_code}" != "200" ]]; then
    echo "FAIL ${subject}: readiness endpoint returned HTTP ${ready_code}"
    failed=1
    continue
  fi

  questions_code=$(curl "${CURL_OPTS[@]}" "${BASE_URL}/api/${subject}/v1/questions?limit=1" || echo "000")
  if [[ "${questions_code}" != "200" ]]; then
    echo "FAIL ${subject}: questions endpoint returned HTTP ${questions_code}"
    failed=1
    continue
  fi

  echo "ok   ${subject}: contract baseline checks passed"
done

if [[ "${failed}" -ne 0 ]]; then
  echo "Contract checks failed."
  exit 1
fi

echo "Contract checks passed."
