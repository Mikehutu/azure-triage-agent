# CHANGELOG

> **Rule: never erase old entries.** Always append at the top with the date.

## v0.1.0 (2026-09-13)
- [scaffold]: SDD+DOX bootstrap via sdd-kit (doc tree, AGENTS.md chain, scripts/sdd-validate, sdd-dox-check, kb/)
- [spec]: PRD.md authored — enterprise ticket triage & enrichment agent (Azure OpenAI classification + Azure AI Search RAG, managed-identity-only, <3s e2e)
- [spec]: TASKS.md sliced R-PIV (3 slices) — validator = agy (isolated); builder = project session
- [tooling]: aimock (CopilotKit mock) chosen for offline LLM/search/agentic mocks — no Azure creds required for dev/eval
- [slice-01]: Core contract — `src/schemas.py` (TicketPayload/RunbookReference/TriageResult, Literal enums, extra=forbid), `src/config.py` (pydantic-settings, env NAMES only), `src/main.py` (POST /api/v1/triage validation shell, 501 until wiring), `infra/main.bicep` (Container App + user-assigned MI + RBAC, zero secrets)
- [slice-01]: gates G1–G4 + secrets scan PASS (16 tests, 100% cov); `scripts/run-gates.sh` added (fail-loud)
- [slice-01][decision]: Azure OpenAI client via `openai` package (AzureOpenAI class) — `azure-openai` is legacy/nonexistent on PyPI
- [slice-01][decision]: container CPU 0.5 → 1 (bicep 2023-05-01 schema types cpu as int); flagged in slice-01.md
- [slice-01][decision]: validation report + AC matrix at docs/validation/slice-01.md; agy validation = PASS-WITH-CONCERNS (no MAJOR findings)
- [slice-01][fix]: agy F-01 — `cpu: json('0.5')` (zero-warning fractional CPU, correct 0.5 vCPU/1.0Gi pairing); gates re-PASS
- [slice-01][queue]: agy F-02 whitespace-only body → slice 02; F-03 unbounded field lengths → slice 03
- [slice-02]: classification engine — `src/services/triage_service.py` (Azure OpenAI structured outputs, temp 0.0, DI client), `src/services/__init__.py` (managed-identity prod client + mock client), flat strict JSON schema
- [slice-02][fix]: agy F-02 — whitespace-only body/subject rejected (field_validator)
- [slice-02][test]: 30 tests / 100% cov; unit (mocked client incl. 429/malformed/mismatch) + aimock e2e (real HTTP: billing fixture + throttle 429 → TriageServiceError, fail loud)
- [slice-02][harness]: `aimock/` — Azure OpenAI mocks (billing, mfa, fallback, 429 error), AGENTS.md registered in DOX index; secrets gate allows ONLY `api_key="mock"` (documented)
- [slice-02][validate]: agy verdict **PASS** (5/5 AC VERIFIED, 0 MAJOR/MINOR; probes: DI isolation, schema strictness, fences, secret scan); INFO F-01 choices guard FIXED (31 tests); F-03 → slice 03
- [slice-03]: search + full pipeline — `src/services/search_service.py` (Azure AI Search hybrid, fail-loud `SearchServiceError`, `FakeSearchService` offline adapter), `src/main.py` wired (200 `TriageResult`; provider errors → 502, no fake results)
- [slice-03][fix]: agy F-03 — `max_length` 64/200/20_000 (ticket_id/subject/body) with 422 tests
- [slice-03][test]: 46 tests / 100% cov — pipeline e2e (aimock LLM + fake search, <3s asserted), search unit, MCP handshake e2e, fail-loud 502 paths
- [slice-03][harness]: aimock MCP stanza (`get_runbook_notes`) + verified handshake sequence (session-id header required for notifications/initialized); search mocked via FakeSearchService (no Azure Search REST in aimock)
- [slice-03][validate]: agy verdict **PASS** — project "ready to be declared DONE per PRD Success Criteria" (6/6 ACs; probes incl. runbook collision, MCP fault injection, 5.7ms latency); INFO F-01 dedup FIXED (47 tests); F-02 defers rate limiting to gateway
- [final]: 3/3 slices delivered, 3 isolated agy validations (1×PASS-WITH-CONCERNS→fixes, 2×PASS), GitHub publish not done (local only, per publish policy)
