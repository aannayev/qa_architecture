#!/usr/bin/env bash
# Network-latency chaos experiment.
#
# Two modes:
#   1. baseline (default) — hits the gateway N times under normal conditions
#      and asserts the failure rate stays below MAX_FAILURE_RATE. Validates
#      the steady state before injecting chaos.
#   2. toxiproxy — when Toxiproxy is reachable on TOXIPROXY_HOST, injects a
#      latency toxic on the Postgres proxy, runs the same N requests, then
#      removes the toxic. Validates the system tolerates injected latency.
#
# Toxiproxy is provided by docker-compose.chaos.yml (`make up-chaos`).
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
TARGET="${TARGET_ENDPOINT:-/api/history/readyz}"
REQUESTS="${REQUESTS:-20}"
MAX_FAILURE_RATE="${MAX_FAILURE_RATE:-0.20}"
TOXIPROXY_HOST="${TOXIPROXY_HOST:-http://localhost:8474}"
LATENCY_MS="${LATENCY_MS:-200}"
JITTER_MS="${JITTER_MS:-50}"

run_burst() {
  local label="$1"
  local fail=0
  for _ in $(seq 1 "${REQUESTS}"); do
    code=$(curl --noproxy "*" -s -o /dev/null -w '%{http_code}' --max-time 5 "${BASE_URL}${TARGET}" || echo "000")
    if [[ "${code}" != "200" ]]; then
      fail=$((fail + 1))
    fi
  done
  local rate
  rate=$(awk "BEGIN { printf \"%.2f\", ${fail}/${REQUESTS} }")
  echo "[${label}] failures=${fail}/${REQUESTS} failure_rate=${rate}"
  if ! awk "BEGIN { exit !(${rate} <= ${MAX_FAILURE_RATE}) }"; then
    echo "[${label}] FAIL: failure_rate ${rate} > ${MAX_FAILURE_RATE}"
    return 1
  fi
  return 0
}

toxiproxy_available() {
  curl --noproxy "*" -s -o /dev/null -w '%{http_code}' --max-time 2 "${TOXIPROXY_HOST}/proxies" | grep -q '^200$'
}

# Phase 1: baseline
run_burst "baseline"

# Phase 2: with injected latency (only if Toxiproxy is present)
if toxiproxy_available; then
  echo "Toxiproxy detected at ${TOXIPROXY_HOST} — injecting ${LATENCY_MS}ms latency on postgres proxy"
  curl --noproxy "*" -s -X POST -H 'Content-Type: application/json' \
    "${TOXIPROXY_HOST}/proxies/postgres/toxics" \
    -d "{\"name\":\"latency_down\",\"type\":\"latency\",\"stream\":\"downstream\",\"attributes\":{\"latency\":${LATENCY_MS},\"jitter\":${JITTER_MS}}}" \
    > /dev/null || echo "(toxic may already exist)"

  status=0
  run_burst "with-latency" || status=$?

  echo "Removing latency toxic"
  curl --noproxy "*" -s -X DELETE "${TOXIPROXY_HOST}/proxies/postgres/toxics/latency_down" > /dev/null || true

  if [[ ${status} -ne 0 ]]; then
    echo "Chaos check FAILED under injected latency."
    exit 1
  fi
else
  echo "Toxiproxy not reachable at ${TOXIPROXY_HOST} — skipping latency injection."
  echo "Run 'make up-chaos' to enable the full experiment."
fi

echo "Chaos check passed."
