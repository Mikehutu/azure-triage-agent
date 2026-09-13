# HANDOFF — azure-triage-agent

Last updated: 2026-09-13 · Session: default profile (Hermes) · Next slice: **Slice 01**

## Current State
- SDD+DOX scaffolded and committed (`7b5ac8a`).
- PRD.md final (authored by Mike, follows sdd-kit PRD template).
- TASKS.md: 3 slices defined (01 core contract, 02 classification, 03 retrieval+pipeline). Slice 01 unchecked.
- No code yet (src/ has AGENTS.md only). No real Azure credentials — everything mock-backed (aimock + SDK-client mocks).

## Next Slice — 01: Core Skeleton, Schemas & Bicep Baseline
1. `src/schemas.py` (TicketPayload, RunbookReference, TriageResult per PRD)
2. `src/config.py` (pydantic-settings; env var NAMES only)
3. `src/main.py` FastAPI shell: `POST /api/v1/triage` (validation only; wiring stubbed), `GET /healthz`
4. `infra/main.bicep`: Container App + user-assigned managed identity + RBAC
5. Gates G1 (ruff), G2 (mypy --strict), G3 (bicep build) + schema unit tests
6. Validate: `./scripts/sdd-validate .` then **agy** (fresh context, artifacts only) → `docs/validation/slice-01.md`

## Environment Notes
- WSL2, no sudo: bicep CLI standalone in `~/.local/bin/bicep`; `az` NOT installed (G3 runs `bicep build`, CI can run `az bicep build`)
- Python 3.11 + `uv`; global ruff/pytest; mypy via `uvx mypy` or project dev group
- aimock 1.39.0 global (`aimock`/`llmock`); aimock/ config under version control
- Machine constraint: no real Azure tenant/keys — never hardcode or invent credentials

## Risks
- Validator must be isolated from builder context (agy fresh session) — no mid-session reuse
- `az bicep build` vs `bicep build` naming — keep both documented (see INFRASTRUCTURE.md)
