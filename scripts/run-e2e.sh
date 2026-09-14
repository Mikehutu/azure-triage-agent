#!/usr/bin/env bash
# Run practical end-to-end tests against live server instances over real TCP sockets.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "== Running Practical End-to-End Tests =="
uv run pytest tests/e2e/ --no-cov -v
echo "E2E_PASS"
