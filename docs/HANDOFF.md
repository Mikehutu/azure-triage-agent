# HANDOFF — azure-triage-agent

Last updated: 2026-09-14 (v0.3.0 — Public Release & Enterprise Client Integration Architecture) · Next: Phase 5 CRM connectors or real-Azure validation

## Current State
- Public GitHub repository: `https://github.com/Mikehutu/azure-triage-agent`
- **ALL 4 DELIVERY SLICES DELIVERED:**
  - Slice 01 (`0eed6cd`, `c6b505f`): schemas/config/main shell/bicep — agy PASS-WITH-CONCERNS; F-01 fixed.
  - Slice 02 (`6c525e2`, `5d84381`): classification engine — agy PASS; F-01 (choices guard) fixed.
  - Slice 03 (`50c3772`): search + full pipeline + MCP mocks — agy PASS; F-01 dedup fixed.
  - Slice 04 (`85cc3d0`): practical live-server e2e tests (`tests/e2e/`), `FakeSearchService` mock support, standalone `scripts/run-e2e.sh`, G5 gate in `scripts/run-gates.sh`, comprehensive `docs/TESTING.md`, and professional README overhaul.
- **Continuity & Enterprise Integration Architecture:**
  - Added enterprise ITSM/CRM integration patterns (ServiceNow, Zendesk, Jira Service Management) via Azure Logic Apps and native webhooks.
  - Documented Tier-1 engineer dashboard Copilot Card visualization and field mapping.
  - Backlog Phase 5 (Slice 05) tracked in PRD.md, PLANNING.md, and TASKS.md.
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

## Risks & Next Steps
- Real Azure deployment (managed identity token exchange, content filter, search semantic config, latency) untested against live tenant — mock contract proven; ready for cloud provisioning.
- Phase 5: Implement ready-to-deploy Azure Logic App templates for ServiceNow / Zendesk intake.
