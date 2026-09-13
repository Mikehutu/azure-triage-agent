# HANDOFF — azure-triage-agent

Last updated: 2026-09-13 (Slice 02 build complete) · Next awaited: agy verdict for Slice 02, then Slice 03

## Current State
- SDD+DOX project at ~/projects/azure-triage-agent (not a GitHub repo — local only, per Mike's workflow; publish policy applies if ever shared).
- **Slice 01 DONE** (commits `0eed6cd`, `c6b505f`): schemas/config/main shell/bicep; agy PASS-WITH-CONCERNS; F-01 fixed (`cpu: json('0.5')`), F-02/F-03 queued.
- **Slice 02 built + committed** (`6c525e2`): `src/services/triage_service.py` (Azure OpenAI structured outputs, temp 0.0, DI client, flat strict schema), `src/services/__init__.py` (managed-identity prod client, mock client), F-02 whitespace validator fix, aimock harness (`aimock/` + e2e tests).
  - Gates: ALL_GATES_PASS (30 tests, 100% cov), MECH_PASS, DOX_PASS.
  - **agy validation RUNNING** → will write `docs/validation/slice-02-agy.md`; process its findings before Slice 03.
- **Slice 03 (next)**: `src/services/search_service.py` (Azure AI Search hybrid, fake adapter offline), wire service+search into main.py (200 TriageResult), e2e API test, F-03 field ceilings, aimock search/MCP/A2A mocks.

## Environment Notes
- WSL2, no sudo → bicep standalone `~/.local/bin/bicep` (G3 = `bicep build infra/main.bicep`); `az` CLI NOT installed.
- `uv sync` deps; `PATH="$PWD/.venv/bin:$PATH" ./scripts/sdd-validate .` required (kit script prefers global pytest, which lacks pytest-cov).
- aimock 1.39.0 global. Fixture paths in `aimock/aimock.json` resolve against **repo root** (process CWD): `./aimock/fixtures/llm`.
- Secrets gate: only `api_key="mock"` allowed (documented exception, mock client only).
- Background agy runs via terminal backend can look stalled ("Fixing project permissions...") — check `/tmp/agy-slice0X-out.txt` / process poll.
- Always run agy validators from `/tmp` with `--add-dir` pointing at the project (WSL sudo-hang pitfall), `--model "Gemini 3.8 Flash (High)"`.

## Risks
- Real Azure OpenAI/Search untested by design (no creds) — mock-backed until a real-cloud validation gate.
- DOX: `aimock/AGENTS.md` registered in root index (child AGENTS chain complete).
- Validator isolation: never reuse builder context for agy; fresh session each slice.
