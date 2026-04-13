#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"

if [[ ! -d "${FRONTEND_DIR}" ]]; then
  echo "frontend directory is missing; skipping type generation."
  exit 0
fi

echo "Frontend type generation is not configured yet."
echo "Expected next step: wire openapi-typescript into frontend package scripts."
