# Independent Validation Report — Slice 03: Runbook Retrieval & Full Pipeline

- **Date:** 2026-09-13
- **Role:** Independent Validator (agy)
- **Target:** Slice 03 (`search-service` + API full pipeline integration + agentic surfaces mock)
- **Evaluated Commit:** `50c3772`
- **Methodology:** Clean-room artifacts-only evaluation against `PRD.md` (FR-1, FR-2, FR-3, Success Criteria) and `TASKS.md` Phase 3. The builder's claim document (`docs/validation/slice-03.md`) was treated strictly as claim-only; every claim was independently verified with live test runs, code inspection, and custom probes.

---

## Validator verdict: PASS

All 6 Acceptance Criteria are mechanically verified, fully covered by automated tests, and adhere strictly to the PRD and TASKS contracts. Slice 02 finding F-03 (unbounded string fields) has been verified resolved with `max_length` constraints and 422 rejections. The search service cleanly implements runtime protocol conformance, hybrid search query parameters, fail-loud error wrapping, and deterministic offline mocking via `FakeSearchService`. The FastAPI pipeline correctly excludes LLM-hallucinated runbooks, enriches with search results, and fails loud with HTTP 502 on any upstream dependency failure. All mechanical gates pass with 100% test coverage (46 passed), clean formatting/linting, zero type errors, clean Bicep compilation, and zero plaintext secrets.

---

## Acceptance Criteria Matrix

| AC | Criterion | Verdict | Evidence (command / line reference) |
|---|---|---|---|
| **AC-1** | `src/services/search_service.py` defines `ISearchService` protocol + `AzureAISearchService` (hybrid via `search_mode="all"`, `select=[document_id,title]`, `@search.score` -> `relevance_score`, empty list on no match, `top<=0` and blank query -> `SearchServiceError`). | **VERIFIED** | `src/services/search_service.py:18-24` defines `@runtime_checkable class ISearchService(Protocol)` matching PRD. `AzureAISearchService.search_runbooks` calls `self._client.search(query, top=top, search_mode="all", select=["document_id", "title"])` at lines 54-59. Maps `@search.score` defaulting to `0.0` at line 66. Returns empty list on no match (`test_no_matches_returns_empty`). Rejects `top <= 0` and blank queries with `SearchServiceError` at lines 49-52. Covered by 8 unit tests in `tests/unit/test_search.py`. |
| **AC-2** | Provider failures surface as `SearchServiceError` (no silent fallback). | **VERIFIED** | `src/services/search_service.py:70-71` catches any provider exception and raises `SearchServiceError(f"runbook search failed: {exc}") from exc`. Verified by `test_provider_error_raises_search_error`. All 8 search unit tests pass (`uv run pytest tests/unit/test_search.py --no-cov -v`). |
| **AC-3** | `POST /api/v1/triage` returns 200 `TriageResult` with `matched_runbooks` from search; < 3s (asserted). Fails loud on search outage (502), missing wiring (502), and oversized body (422). | **VERIFIED** | `src/main.py:32-46` wires classification + search, returning `TriageResult` with `matched_runbooks=runbooks`. `test_pipeline_returns_enriched_result_under_3s` asserts status 200 and `resp.elapsed.total_seconds() < 3.0`. `test_pipeline_critical_fixture` validates critical priority path. `test_search_failure_returns_502` proves 502 with detail on search outage. `test_valid_payload_fails_loud_502_without_wiring` in `test_api.py` proves 502 when services unwired. |
| **AC-4** | F-03 resolution: `max_length` ceilings (`ticket_id` 64, `subject` 200, `body` 20_000) exist and 422 at API boundary. | **VERIFIED** | `src/schemas.py:25-28` enforces `min_length=1, max_length=64` on `ticket_id`, `max_length=200` on `subject`, and `max_length=20_000` on `body`. Verified by `test_oversized_body_rejected` and `test_oversized_ticket_id_rejected` in `test_schemas.py`, and `test_oversized_body_returns_422` in `test_triage_api.py`. |
| **AC-5** | Agentic surface mocked via aimock MCP — verified handshake (`initialize` -> `Mcp-Session-Id` header -> `notifications/initialized` WITH header -> `tools/list` -> `tools/call get_runbook_notes`). | **VERIFIED** | `tests/unit/test_aimock_mcp.py:32-80` runs complete JSON-RPC 2.0 handshake over real HTTP against `aimock` server process: initializes session, passes `Mcp-Session-Id` to `notifications/initialized` and `tools/list`, and successfully executes `tools/call get_runbook_notes` with document_id `rb-1`. |
| **AC-6** | Full gates pass (`bash scripts/run-gates.sh` ends with `ALL_GATES_PASS`; G4 enforces >=85% via `--cov-fail-under=85`); `PATH="$PWD/.venv/bin:$PATH" ./scripts/sdd-validate .` exits `MECH_PASS`; `./scripts/sdd-dox-check .` exits `DOX_PASS`. | **VERIFIED** | `bash scripts/run-gates.sh` exited 0 (G1 PASS, G2 PASS, G3 PASS, G4 PASS 46/46 passed with 100.00% statement coverage across all 160 statements, SECRETS_CLEAN, ALL_GATES_PASS). `sdd-validate` exited 0 (`MECH_PASS`). `sdd-dox-check` exited 0 (`DOX_PASS` across all 7 indexed children). |

---

## Verification of Builder Claims (`docs/validation/slice-03.md`)

| Builder Claim | Status | Validator Verification Notes |
|---|---|---|
| `ISearchService.search_runbooks(query, top=2)` returns up to 2 `RunbookReference`; empty list on no match | **CONFIRMED** | Verified in `src/services/search_service.py` and tested in `test_search.py`. |
| Hybrid search vs `kb-runbooks-index` via Azure AI Search SDK; failures surface as `SearchServiceError` | **CONFIRMED** | Verified parameters `search_mode="all"`, `select=["document_id", "title"]`, and fail-loud exception wrapping. |
| `POST /api/v1/triage` end-to-end enriches in < 3s (asserts `resp.elapsed < 3.0`) | **CONFIRMED** | Asserted in `test_triage_api.py`. Independent probe measured actual latency at ~5.70ms average. |
| Unbounded fields fixed (`max_length` 64/200/20_000 + 422 on oversized) | **CONFIRMED** | Schema validation and API endpoint rejection verified. |
| End-to-end API tests with TestClient + aimock LLM + fake search (standard + critical) | **CONFIRMED** | Both standard (`T-8001` -> Billing/P2_HIGH) and critical (`T-8002` -> Authentication/P1_CRITICAL) fixtures pass. |
| Agentic surfaces mocked via MCP over real HTTP | **CONFIRMED** | Live JSON-RPC sequence verified against ephemeral aimock server. |
| Gates pass with G4 >=85% cov enforced via `--cov-fail-under=85` + secrets scan | **CONFIRMED** | Verified: 46 tests passed, 100.00% coverage, all gates green. |

---

## Findings Table

| ID | Severity | Location | Description | Recommendation |
|---|---|---|---|---|
| **F-01** | **INFO** | `src/services/search_service.py:60-69` | **No deduplication of `document_id` in search results:** If Azure AI Search returns multiple chunks or records with the same `document_id` (common in chunked knowledge bases), `search_runbooks` appends duplicate `RunbookReference` entries. | For future production hardening, consider tracking seen `document_id`s in an `OrderedDict` or `set` during iteration to ensure the top-N results represent distinct runbooks. |
| **F-02** | **INFO** | `src/main.py` | **No application-level rate limiting:** FastAPI app contains no local rate-limiting middleware or headers (`429 Too Many Requests`). | Acceptable for a Container App microservice where ingress throttling is handled by Azure Front Door / API Management or Container Apps ingress policies, but worth documenting in API gateway specs. |
| **F-03** | **INFO** | `pyproject.toml:54` | **Single-file test runs trigger global coverage threshold:** `addopts` contains `--cov=src --cov-fail-under=85`. Running an isolated test file (e.g. `pytest tests/unit/test_search.py -v`) fails with code 1 because only a subset of `src/` statements are executed, despite 100% of the tests in that file passing. | Developers testing single files should use `--no-cov` or `-o addopts=""`. The full test suite passes with 100.00% coverage. |
| **F-04** | **INFO** | `infra/` | **No dedicated `infra/AGENTS.md`:** The `infra/` directory contains `main.bicep` and `main.json` but has no local `AGENTS.md` child doc. | Root `AGENTS.md` owns Bicep templates and the G3 gate. If `infra/` expands with additional modules or environments, consider creating `infra/AGENTS.md`. |

*Note: Zero MAJOR or MINOR findings. All findings are INFO level observations.*

---

## Probe Results & Deep Verification

### 1. Endpoint Contract Completeness & Runbook Collision Probe
- **Probe:** Dispatched `POST /api/v1/triage` with dependency overrides where `ITriageService.classify` emitted a hallucinated/mock runbook (`document_id="llm-hallucinated"`), while `ISearchService.search_runbooks` returned a verified runbook (`document_id="search-real"`).
- **Inspection:** Inspected `src/main.py:41-43`:
  ```python
  return TriageResult(
      **result.model_dump(exclude={"matched_runbooks"}), matched_runbooks=runbooks
  )
  ```
- **Observed:** The response returned HTTP 200 with schema:
  ```json
  {
    "ticket_id": "T-1234",
    "category": "Billing",
    "severity": "P2_HIGH",
    "summary": "Test summary",
    "suggested_action": "Test action",
    "matched_runbooks": [
      {
        "document_id": "search-real",
        "title": "Search RB",
        "relevance_score": 0.95
      }
    ]
  }
  ```
  `"llm-hallucinated"` was completely excluded and superseded by the search service result. All fields and enum constraints (`category`, `severity`) match `PRD.md:156-163` exactly.
- **Verdict: PASS.**

### 2. Search Service Edge Cases Probe
- **Probe A (Duplicate document IDs):** Injected 2 items with identical `document_id="rb-1"`.
  - **Result:** Returned both items (`['rb-1', 'rb-1']`). Documented as INFO finding F-01.
- **Probe B (Missing `@search.score`):** Injected search item `{"document_id": "rb-1", "title": "Runbook 1"}` without `@search.score`.
  - **Result:** Cleanly fell back to `relevance_score = 0.0` via `.get("@search.score", 0.0)`.
- **Probe C (Missing required fields `document_id` or `title`):** Injected search items missing `title` or `document_id`.
  - **Result:** Raised `KeyError` within `search_runbooks()`, which was caught and wrapped into `SearchServiceError("runbook search failed: ...")`. Translated to HTTP 502 in the API. Fails loud without data corruption.
- **Verdict: PASS.**

### 3. Security & Payload Path Probe
- **Regex Secrets Scan:** Executed pattern `(api[_-]?key|access[_-]?key|secret|password|token)\s*=\s*["\'][^"\']+["\']` across the entire codebase excluding `.git` and `.venv`.
  - **Result:** Exactly 1 non-test hit: `src/services/__init__.py:64 -> api_key="mock"` in `_build_mock_client()`. This is the documented, tested offline mock client path.
- **Content-Type & Malformed Payload Ingestion:**
  - `Content-Type: text/plain` -> HTTP 422 (`Input should be a valid dictionary or object to extract fields from`).
  - Empty body (`{}`) -> HTTP 422 (`Field required`).
  - Malformed JSON (`{bad json`) -> HTTP 422 (`JSON decode error`).
- **Verdict: PASS.**

### 4. Agentic Surfaces (aimock MCP) Fault Injection Probe
- **Probe A (tools/call without session header):** Dispatched `POST /mcp` with `method: "tools/call"` omitting `Mcp-Session-Id`.
  - **Result:** HTTP 400 with `{"error": "Missing mcp-session-id header"}`.
- **Probe B (tools/call with unknown tool name):** Dispatched `tools/call` with `name: "non_existent_tool"` and valid session header.
  - **Result:** HTTP 200 with JSON-RPC error response:
    ```json
    {"jsonrpc": "2.0", "id": 3, "error": {"code": -32602, "message": "Unknown tool: non_existent_tool"}}
    ```
- **Verdict: PASS.** Fails loud with strict compliance to MCP / JSON-RPC 2.0 protocol specifications.

### 5. Measured End-to-End Latency
- **Probe:** Executed 5 consecutive round-trip requests against `POST /api/v1/triage` via `TestClient` backed by real `aimock` (port-bound HTTP) and `FakeSearchService`:
  - Sample 1: 6.96 ms
  - Sample 2: 6.30 ms
  - Sample 3: 5.53 ms
  - Sample 4: 4.93 ms
  - Sample 5: 4.78 ms
  - **Average: 5.70 ms** (Min: 4.78 ms, Max: 6.96 ms)
- **Verdict: PASS.** Sub-10ms in offline mock environment; comfortably satisfies the PRD < 3.0s requirement.

### 6. DOX Structural Integrity
- **Index Check:** Root `AGENTS.md` Child DOX Index includes `aimock/AGENTS.md`.
- **Children on Disk:** All 8 `AGENTS.md` files exist on disk:
  1. `AGENTS.md` (root rail)
  2. `aimock/AGENTS.md`
  3. `docs/AGENTS.md`
  4. `kb/AGENTS.md`
  5. `scripts/AGENTS.md`
  6. `skills/AGENTS.md`
  7. `src/AGENTS.md`
  8. `tests/AGENTS.md`
- **DOX Verification:** `./scripts/sdd-dox-check .` executed and returned exit code 0 (`DOX_PASS`).
- **Verdict: PASS.**

---

## Confidence Note: Real Azure Tenant vs Mocked Surfaces

All test and validation suites run completely offline without cloud credentials:
- **What is verified with 100% confidence offline:**
  1. Complete FastAPI endpoint lifecycle, validation rules, HTTP status codes (200, 422, 502), and error payloads.
  2. Pydantic v2 schemas, Literal enum constraints, whitespace rejection, and string length ceilings.
  3. Azure OpenAI structured outputs prompt formation, flat schema generation (`additionalProperties: false`, zero `$defs`), response parsing, and error escalation.
  4. Azure AI Search SDK parameter construction (`search_mode="all"`, `select=["document_id", "title"]`, `top=2`), field mapping, score handling, and fail-loud exception handling.
  5. MCP agentic protocol handshake, session management, tool listing, and tool invocation.
  6. Bicep template syntax, resource declarations, Managed Identity assignment, and RBAC role definitions (`bicep build` passes with zero diagnostics).

- **What requires a live Azure tenant / cloud sandbox for final verification:**
  1. **Azure Active Directory Token Exchange:** Verifying that `DefaultAzureCredential` obtains valid bearer tokens from the User-Assigned Managed Identity inside Azure Container Apps at runtime.
  2. **Azure OpenAI Content Filters & Quotas:** Verifying behavior when enterprise prompts encounter Azure OpenAI content moderation filters or tenant-level TPM rate limits.
  3. **Azure AI Search Real Index Scoring:** Verifying actual BM25 + vector hybrid scoring weights and semantic ranker performance against live documents in `kb-runbooks-index`.
  4. **Container Apps Ingress & Scaling:** Live verification of cold-start latency when scaling from 0 to 1 replica under 0.5 vCPU / 1.0Gi memory constraints.

---

## Final Project Status: Readiness per PRD Success Criteria

| PRD Success Criterion | Status | Evidence |
|---|---|---|
| 1. `POST /api/v1/triage` correctly parses and enriches standard and critical test fixtures within schema boundaries, end-to-end in under 3 seconds (G5). | **MET** | Verified via `test_triage_api.py` and independent probe (average 5.70ms). Standard and critical fixtures verified. |
| 2. All unit tests pass with >= 85% code coverage (G4). | **MET** | 46 tests passed with 100.00% statement coverage. Enforced via `--cov-fail-under=85`. |
| 3. `ruff check`/`ruff format` clean, `mypy src/ --strict` zero errors (G1, G2). | **MET** | G1 and G2 pass with zero diagnostics. |
| 4. `az bicep build --file infra/main.bicep` compiles clean ARM-JSON with zero warnings (G3). | **MET** | `bicep build infra/main.bicep` compiles clean ARM-JSON with zero warnings. |
| 5. Zero plaintext secrets in any file or environment setting, with authentication through Managed Identity only. | **MET** | `run-gates.sh` secrets scan exits `SECRETS_CLEAN`. Only documented `api_key="mock"` exception exists for offline client. |

**Overall Conclusion:** The project successfully fulfills all requirements and success criteria specified in `PRD.md` and `TASKS.md`. The codebase is clean, well-tested, fully documented, and ready for project completion and handoff.
