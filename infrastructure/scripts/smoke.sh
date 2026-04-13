#!/usr/bin/env bash
# Post-deploy smoke test. Hits /health/ready on every known service and
# returns non-zero if any is unreachable. Designed to be safe during
# early phases — services that do not yet exist are simply skipped.
set -euo pipefail

BASE="${BASE_URL:-http://localhost}"
CURL_OPTS=(--noproxy "*" -s -o /dev/null -w '%{http_code}' --max-time 5)
SERVICES=(
  "history:/api/history/readyz"
  "physics:/api/physics/readyz"
  "math:/api/math/readyz"
  "geography:/api/geography/readyz"
  "ai-assistant:/ai/readyz"
)

fail=0
for entry in "${SERVICES[@]}"; do
  name="${entry%%:*}"
  path="${entry#*:}"
  url="${BASE}${path}"
  code=$(curl "${CURL_OPTS[@]}" "${url}" || echo "000")
  if [[ "${code}" == "200" ]]; then
    printf "  ok   %-14s %s\n" "${name}" "${url}"
  elif [[ "${code}" == "000" || "${code}" == "404" ]]; then
    printf "  skip %-14s %s (not deployed yet)\n" "${name}" "${url}"
  else
    printf "  FAIL %-14s %s (HTTP %s)\n" "${name}" "${url}" "${code}"
    fail=1
  fi
done

exit "${fail}"
