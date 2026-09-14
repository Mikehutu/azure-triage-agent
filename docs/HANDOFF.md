# HANDOFF — azure-triage-agent

Last updated: 2026-09-14 (v0.2.0 — Slice 04 Delivered: Practical E2E Tests + Test Documentation + Clean README) · Next: optional GitHub publish or real-Azure validation slice

## Current State
- SDD+DOX project at ~/projects/azure-triage-agent (local git; no GitHub repo — publish policy applies if ever shared).
- **ALL 4 SLICES DELIVERED:**
  - Slice 01 (`0eed6cd`, `c6b505f`): schemas/config/main shell/bicep — agy PASS-WITH-CONCERNS; F-01 fixed.
  - Slice 02 (`6c525e2`, `5d84381`): classification engine — agy PASS; F-01 (choices guard) fixed.
  - Slice 03 (`50c3772`): search + full pipeline + MCP mocks — agy PASS; F-01 dedup fixed.
  - Slice 04 (`v0.2.0`): practical live-server e2e tests (`tests/e2e/`), `FakeSearchService` mock support in `create_search_service`, standalone `scripts/run-e2e.sh`, G5 integration in `scripts/run-gates.sh`, comprehensive `docs/TESTING.md`, and professional README overhaul.
- Gates today: ALL_GATES_PASS (62 tests total: 49 unit + 13 e2e, 100% cov, `--cov-fail-under=85`), MECH_PASS, DOX_PASS.
- PRD Success Criteria 1-5 satisfied against live local server and offline mocks; real Azure validation remains (no creds by design).

## Environment Notes
- WSL2 no sudo: bicep standalone; `az` absent (G3 = `bicep build`).
- `PATH="$PWD/.venv/bin:$PATH" ./scripts/sdd-validate .` (kit prefers global pytest; needs venv pytest-cov).
- aimock 1.39.0; config fixture paths relative to repo root; MCP notification REQUIRES `mcp-session-id` header.
- Secrets gate: only `api_key="mock"` allowed (documented).
- agy validators: run from `/tmp` + `--add-dir`, `--model "Gemini 3.8 Flash (High)"`, fresh session per slice (validator ≠ builder).
- Background agy runs can appear stalled ("Fixing project permissions...") — check `/tmp/agy-slice0X-out.txt`.

## Mocking map (no Azure needed)
- Azure OpenAI → aimock fixtures (success/billing/mfa/fallback + 429 chaos).
- MCP agentic surface → aimock mcp stanza + verified handshake test.
- Azure AI Search → FakeSearchService (offline); real SDK path unit-tested with recording fake client.
- A2A stanza = same pattern, not yet used.

## Risks
- Real Azure (managed identity token exchange, content filter, search semantic config, latency) untested — no creds; mock contract proven, real-cloud gate is a future slice.
