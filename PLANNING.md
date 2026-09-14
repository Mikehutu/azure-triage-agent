# PLANNING — azure-triage-agent

## Phase 1 — Core contract (Slice 01)
Schemas, config, FastAPI shell, Bicep baseline. Gates G1–G3.
Dependencies: none.
Outcome: compilable skeleton with the full API surface shape and zero-secret config.

## Phase 2 — Classification engine (Slice 02)
`ITriageService` via Azure OpenAI structured outputs (temp 0.0), mocked client + aimock fixtures. Gate G4.
Dependencies: Phase 1 (schemas/config).

## Phase 3 — Retrieval + full pipeline (Slice 03)
`ISearchService` (Azure AI Search hybrid), wire into `POST /api/v1/triage`, e2e tests with aimock + fake search. Gate G5.
Dependencies: Phase 2.

## Phase 4 — Practical E2E Testing & Test Documentation (Slice 04)
Live-server black-box tests (`tests/e2e/`) over TCP sockets (real uvicorn + aimock subprocesses), standalone runner `scripts/run-e2e.sh`, comprehensive `docs/TESTING.md`, and professional README overhaul. Gate G5 practical.
Dependencies: Phase 3.

## Phase 5 — Continuity & Enterprise CRM Middleware (Slice 05)
Pre-built Azure Logic Apps and Power Automate connectors for ServiceNow, Zendesk, and Jira Service Management; bidirectional field mapping adapters for Tier-1 workspace copilot notes; optional Azure Service Bus async ingestion.
Dependencies: Phase 4.

## Cross-cutting
- Must-run gates (no later slice breaks them): G1 ruff, G2 mypy --strict, G3 bicep build.
- Coverage floor 85% from slice 02 onward.
- Security: managed identity only; grep-gate against hardcoded secrets in CI (G-secure).
- Mock-first: every external surface (Azure OpenAI, Azure AI Search, MCP/A2A) has a fixture in `aimock/` before it's used in a test.
