# Validation — Slice 01: Core Skeleton, Schemas & Bicep Baseline

Date: 2026-09-13 · Builder: project session (Hermes) · Validator: agy (separate, see `slice-01-agy.md`)

## Acceptance Criteria (predate code — TASKS.md / PRD FR-1)

| AC | Criterion | Verdict | Evidence |
|---|---|---|---|
| AC-1 | `src/schemas.py` defines `TicketPayload`, `RunbookReference`, `TriageResult` (Pydantic v2, Literal enums, extra=forbid) | VERIFIED | `tests/unit/test_schemas.py` (9 tests), mypy strict clean |
| AC-2 | `src/config.py` via pydantic-settings; env var NAMES only; no hardcoded secrets | VERIFIED | `tests/unit/test_config.py`, `scripts/run-gates.sh` SECRETS_CLEAN |
| AC-3 | `POST /api/v1/triage` validates payload; 422 with field-level detail on invalid input | VERIFIED | `tests/unit/test_api.py` (tier/missing/extra → 422 with `loc` assertions) |
| AC-4 | `infra/main.bicep` compiles clean ARM-JSON, zero warnings; user-assigned managed identity + RBAC Azure OpenAI User / Search Index Data Reader; zero secrets | VERIFIED | `bicep build infra/main.bicep` exit 0, zero diagnostics |
| AC-5 | Gates: G1 ruff check+format, G2 mypy `src/ --strict`, G4 pytest unit with >= 85% coverage | VERIFIED | `scripts/run-gates.sh` → ALL_GATES_PASS; 16 passed, 100% coverage |

## Mechanical gates (recorded)

- G1: `ruff check . && ruff format --check .` → 0 (26 files, clean)
- G2: `mypy src/ --strict` → 0 errors (4 source files)
- G3: `bicep build --file infra/main.bicep` → 0 diagnostics (clean ARM-JSON)
- G4: `pytest tests/unit/ -v` → 16 passed, coverage 100% (config 15/15, main 9/9, schemas 22/22)
- DOX: `./scripts/sdd-dox-check .` → DOX_PASS
- Secrets scan: no `api_key|secret|password|token` assignment patterns in `src/`

## Known deviations / notes (validator should confirm)

1. **Container CPU (RESOLVED):** PRD says 0.5 cores. Initial `cpu: 1` (2023-05-01 schema types cpu as int) flagged by agy as F-01 (pairing risk with 1.0Gi). Fixed via `cpu: json('0.5')` — zero Bicep warnings, ARM float, correct 0.5 vCPU / 1.0Gi pairing. Verified by agy probe + re-run gates.
2. **Standalone `bicep` CLI replaces `az bicep`** locally (no `az` on this machine, no sudo). `bicep build infra/main.bicep` == `az bicep build --file infra/main.bicep` semantics; CI can use the az form.
3. **`sdd-validate` must run with venv on PATH** (`PATH="$PWD/.venv/bin:$PATH" ./scripts/sdd-validate .`) — the kit script prefers global pytest, which lacks pytest-cov. Documented in HANDOFF.
4. **Slice 01 interim behavior:** valid payloads return 501 until service wiring (slice 02/03) — intentional fail-loud, no fake triage results. AC-3 covers 422 only; AC-FR-2 (200 + TriageResult) lands in slices 02–03.

## Validator findings (agy, PASS-WITH-CONCERNS) — resolution log
- F-01 MINOR (bicep cpu/memory pairing) → **FIXED** (json('0.5')), re-validated.
- F-02 MINOR (whitespace-only body passes min_length=1) → queued in Slice 02 (schema pattern `\S`).
- F-03 INFO (unbounded field lengths) → queued in Slice 03 (max_length / payload ceilings).
- F-04 INFO (interim 501) → accepted by design, per PRD FR-1 staging.

## Residual risk (human ship approval scope)
- Real Azure OpenAI/Search behavior is untested (no creds by design) — slices 02/03 replace mocks with aimock-recorded fixtures; real-cloud validation is a separate later gate.
