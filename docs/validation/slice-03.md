# Validation — Slice 03: Runbook Retrieval & Full Pipeline

Date: 2026-09-13 · Builder: project session (Hermes) · Validator: agy (separate, `slice-03-agy.md` pending)

## Acceptance Criteria (TASKS.md slice 03)

| AC | Criterion | Verdict | Evidence |
|---|---|---|---|
| AC-1 | `ISearchService.search_runbooks(query, top=2)` returns up to 2 `RunbookReference`; empty list on no match | VERIFIED | `src/services/search_service.py`; `tests/unit/test_search.py` (mapping, no-match empty, missing score → 0.0) |
| AC-2 | hybrid search vs `kb-runbooks-index` (Azure AI Search SDK); failures surface as `SearchServiceError` — no silent fallback | VERIFIED | `AzureAISearchService` (`search_mode="all"`, `select=[document_id,title]`, fail loud); `test_provider_error_raises_search_error`; `test_empty_query_raises` |
| AC-3 | `POST /api/v1/triage` end-to-end enriches in < 3s (G5) | VERIFIED | `tests/unit/test_triage_api.py::test_pipeline_returns_enriched_result_under_3s` (asserts `resp.elapsed < 3.0`; aimock 30ms fixture + fake search → ~50ms) |
| AC F-03 | unbounded fields fixed: `max_length` 64/200/20_000 + API 422 on oversized | VERIFIED | `src/schemas.py`; `test_oversized_body_rejected`, `test_oversized_ticket_id_rejected`, API `test_oversized_body_returns_422` |
| AC-4 | e2e: FastAPI TestClient + aimock LLM + fake search (both standard & critical fixtures) | VERIFIED | `tests/unit/test_triage_api.py` (billing 200/Billing/P2_HIGH; mfa 200/Authentication/P1_CRITICAL; search 502; wiring-absent 502) |
| AC-5 | agentic surfaces mocked: MCP handshake over real HTTP (initialize → session id → initialized → tools/list → tools/call) | VERIFIED | `tests/unit/test_aimock_mcp.py`; `aimock/aimock.json` mcp stanza (serverInfo/tools/get_runbook_notes) |
| AC-6 | Gates: G1 ruff, G2 mypy --strict, G3 bicep, G4 >=85% cov (now enforced via `--cov-fail-under=85`) + secrets scan | VERIFIED | `run-gates.sh` → ALL_GATES_PASS (46 tests, 100% coverage); `sdd-validate` MECH_PASS; DOX_PASS |

## Validator verdict (agy, clean-room, artifacts-only)
**PASS — "project ready to be declared DONE per PRD Success Criteria"** (report: `slice-03-agy.md`, eval commit `50c3772`). All 6 ACs VERIFIED; zero MAJOR/MINOR findings.
- Probes: hallucinated-runbook collision (LLM runbooks excluded/replaced by search — verified live), duplicate doc IDs, missing `@search.score` → 0.0, missing fields → KeyError → SearchServiceError → 502, secrets scan (1 documented mock exception), content-type/malformed payloads → 422, MCP fault injection (no session header → 400; unknown tool → JSON-RPC -32602), **latency 5.7ms avg** (vs <3s PRD), DOX all 8 children PASS.
- INFO findings: F-01 duplicate document_ids → **FIXED** (dedup, `test_duplicate_document_ids_deduped`; 47 tests, 100% cov). F-02 no app-level rate limiting → deferred to gateway (Azure Front Door/APIM). F-03 single-file `--cov-fail-under` → README tip (`--no-cov`). F-04 no `infra/AGENTS.md` → accepted (root AGENTS owns Bicep/G3).
- Confidence note: live-managed-identity token exchange, content filter, semantic search config, and real latency require a real Azure tenant — mocked contract proven; real-cloud validation is a future step.

## Key decisions / notes
- **Mocking split (explicit):** azure-search-documents is NOT aimed at aimock (no Azure Search REST support) → deterministic **`FakeSearchService`** adapter for offline API tests; `AzureAISearchService` (real SDK, DI) for prod, unit-tested via a recording fake client. aimock covers **LLM + MCP**; A2A stanza mountable the same way (pattern documented in `aimock/README.md`).
- **Fail-loud at the edge:** provider errors → HTTP **502** (never a fabricated TriageResult); unoverridden (no config) endpoint also returns 502, tested.
- `search_runbooks(query)` treats blank query as error; `top` must be > 0.
- Latency claim: assert in test; real Azure latency unverifiable without creds (residual risk).
