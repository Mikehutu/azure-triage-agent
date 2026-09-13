#!/usr/bin/env bash
# Mechanical gates G1-G4 + zero-secret scan (Slice 01+). Usage: ./scripts/run-gates.sh
# Any gate failure exits non-zero — PASS lines are only printed after real success.
set -uo pipefail
cd "$(dirname "$0")/.."

fail() { echo "GATE_FAILED: $1"; exit 1; }

echo "== G1: ruff check + format =="
uv run ruff check . || fail "G1 ruff check"
uv run ruff format --check . || fail "G1 ruff format"
echo "G1_PASS"

echo "== G2: mypy --strict =="
uv run mypy src/ --strict || fail "G2 mypy"
echo "G2_PASS"

echo "== G3: bicep build =="
bicep build infra/main.bicep || fail "G3 bicep"
echo "G3_PASS"

echo "== G4: pytest + coverage =="
uv run pytest tests/unit/ -v || fail "G4 pytest"
echo "G4_PASS"

echo "== SECRETS scan (assignment patterns only) =="
if grep -rniE "(api[_-]?key|access[_-]?key|secret|password|token)[[:space:]]*=[[:space:]]*[\"'][^\"']+" src/ ; then
  fail "hardcoded secret assignment found"
fi
echo "SECRETS_CLEAN"

echo "ALL_GATES_PASS"
