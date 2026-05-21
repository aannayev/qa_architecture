#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SERVICE_DIR="${ROOT_DIR}/services/ai-assistant"

if [[ ! -d "${SERVICE_DIR}" ]]; then
  echo "ai-assistant service is missing."
  exit 1
fi

(
  cd "${SERVICE_DIR}"
  python -m pip install --quiet -e ".[dev]" >/dev/null
  python -m pytest tests/test_llm_eval.py -q
  python tests/test_llm_eval.py
)
