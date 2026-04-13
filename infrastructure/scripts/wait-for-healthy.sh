#!/usr/bin/env bash
# Wait until every running container reports "healthy" (or "running" if no
# healthcheck is defined). Used after `docker compose up` so downstream
# commands can assume the stack is actually ready.
set -euo pipefail

TIMEOUT="${TIMEOUT:-180}"
INTERVAL=3
PROJECT="${COMPOSE_PROJECT_NAME:-qa-architect}"

echo "Waiting up to ${TIMEOUT}s for services to become healthy..."

deadline=$(( $(date +%s) + TIMEOUT ))
while true; do
  not_ready=$(docker ps \
    --filter "label=com.docker.compose.project=${PROJECT}" \
    --format '{{.Names}} {{.Status}}' \
    | awk '$0 !~ /\(healthy\)/ && $0 !~ /Up [0-9]+ (seconds|minutes|hours|days)$/ {print}' || true)

  if [[ -z "${not_ready}" ]]; then
    echo "All services healthy."
    exit 0
  fi

  if (( $(date +%s) >= deadline )); then
    echo "Timeout waiting for services. Still not ready:"
    echo "${not_ready}"
    exit 1
  fi

  sleep "${INTERVAL}"
done
