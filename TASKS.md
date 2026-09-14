# TASKS — azure-triage-agent

Maintained with the R-PIV loop. One module at a time. Check off complete items. **Never erase old entries** — append new ones.

Validation rule (immutable): **validator ≠ builder.** Builder = project session (Hermes). Validator = **agy** (Gemini 3.8 Flash High) run on a FRESH, artifacts-only context — it never sees the builder's chat. Mechanical gates first (`./scripts/sdd-validate .`), then agy AC verification → `docs/validation/<slice>.md`.

Mocking rule: no real Azure keys/tenant in this environment. All LLM/Search/agentic surfaces are mocked via aimock (`aimock/`) for tests; unit tests mock SDK clients directly. See `aimock/README.md`.

---

## Phase 1 — Core contract (Slice 01)

### Module: `schema` + `config` + API shell + Bicep baseline

#### Plan (Agent: builder)
- [x] PRD defines schemas/interfaces (already authored) — AC predate code
- [x] Define `src/schemas.py`: `TicketPayload`, `RunbookReference`, `TriageResult` (Pydantic v2, `Literal` constraints, no secrets)
- [x] Define `src/config.py`: `Settings` via pydantic-settings; env var NAMES only, no values
- [x] Define FastAPI shell `src/main.py`: `POST /api/v1/triage` (validates payload, returns 422 on bad input; service wiring stubbed until slice 02/03)
- [x] Write `infra/main.bicep`: Azure Container App + user-assigned managed identity + role assignments (no secrets)

#### Implement (Agent: builder)
- [x] Write schemas, config, main shell, bicep

#### Validate (Agent: **agy — MUST BE DIFFERENT FROM BUILDER**)
- [x] G1: `ruff check . && ruff format --check .` → exit 0
- [x] G2: `mypy src/ --strict` → exit 0
- [x] G3: `bicep build --file infra/main.bicep` → compiles clean ARM-JSON, zero warnings
- [x] Schema unit tests (422 on invalid payload; tier enum enforced) pass
- [x] agy AC verification (fresh context) → `docs/validation/slice-01.md` (PASS-WITH-CONCERNS, F-01 fixed, F-02/F-03 queued)

**Module Checkpoint:**
- [x] All tests pass
- [x] Zero plaintext secrets (grep for keys/tokens)
- [x] Cross-agent validation passed (agy)

---

## Phase 2 — Classification engine (Slice 02)

### Module: `triage-service`

#### Plan (Agent: builder)
- [x] AC: `ITriageService.classify` returns `category` ∈ {Billing, Authentication, Infrastructure, Product Defect}, `severity` ∈ {P1_CRITICAL..P4_LOW}
- [x] AC: uses Azure OpenAI structured outputs (temperature 0.0) via `DefaultAzureCredential`; raises on failure (no bare except, no silent fallback)
- [x] AC (agy F-02): whitespace-only body rejected — add pattern `\S` to body/subject fields
- [x] AC: unit tests mock the Azure OpenAI client; aimock fixtures cover success + throttling + malformed-response edge cases
- [x] Define test fixtures (`tests/fixtures/`) incl. standard + critical tickets

#### Implement (Agent: builder)
- [x] `src/services/triage_service.py` + `src/services/__init__.py`
- [x] `tests/unit/test_triage.py` (mocked client) + tests/unit/conftest.py
- [x] `aimock/` harness + `tests/unit/test_aimock_e2e.py` (offline e2e, skippable)

#### Validate (Agent: **agy**)
- [x] G4: `pytest tests/unit/ -v` with >= 85% coverage
- [x] G1/G2 re-run
- [x] aimock e2e: scripted Azure OpenAI responses over real HTTP (record/replay or fixtures)
- [x] agy AC verification → `docs/validation/slice-02.md` (PASS; INFO F-01 choices guard fixed)

**Module Checkpoint:**
- [x] All tests pass, >= 85% coverage
- [x] aimock-mocked edge cases caught (throttle 429, malformed JSON, empty content, no choices)
- [x] Cross-agent validation passed (agy)

---

## Phase 3 — Retrieval + full pipeline (Slice 03)

### Module: `search-service` + API e2e

#### Plan (Agent: builder)
- [x] AC: `ISearchService.search_runbooks(query, top=2)` returns up to 2 `RunbookReference` (id, title, relevance_score); empty list on no match
- [x] AC: hybrid search against `kb-runbooks-index` (Azure AI Search SDK); failures surface, no silent fallback
- [x] AC: `POST /api/v1/triage` end-to-end enriches in < 3s (G5) — measured against mocked search + LLM
- [x] AC (agy F-03): unbounded fields — `max_length` on ticket_id/subject/body + API payload ceiling
- [x] Edge cases: empty runbook match, search index unavailable, degraded suggestion, oversized payload

#### Implement (Agent: builder)
- [x] `src/services/search_service.py` (Azure SDK hybrid search; local fake adapter for offline tests)
- [x] `tests/unit/test_search.py` (mocked client / fake adapter)
- [x] Wire `triage_service` + `search_service` into `src/main.py` POST handler (200 TriageResult)
- [x] `tests/unit/test_triage_api.py` e2e (FastAPI TestClient + aimock LLM + fake search)
- [x] `aimock/` fixtures for search + any MCP/A2A agentic surfaces (MCP stanza + handshake test; search via FakeSearchService)

#### Validate (Agent: **agy**)
- [x] G5: e2e Triage API test passes (standard + critical fixtures)
- [x] G4 coverage >= 85% for full suite; G1/G2/G3 green
- [x] aimock chaos: 500s / malformed / mid-stream drops caught
- [x] agy AC verification → `docs/validation/slice-03.md` (PASS — ready per PRD Success Criteria; F-01 dedup fixed)

**Module Checkpoint:**
- [x] Full suite green with recorded evidence
- [x] End-to-end latency measured (report actual ms)
- [x] Cross-agent validation passed (agy)

---

## Phase 4 — Practical E2E Testing & Test Documentation (Slice 04)

### Module: `tests/e2e` + `docs/TESTING.md`

#### Plan
- [x] AC: Black-box integration tests against live `uvicorn` and `aimock` processes over real TCP sockets (zero internal dependency overrides).
- [x] AC: Scenarios cover `/healthz`, standard billing ticket, critical incident escalation (`P1_CRITICAL`), latency budget (<3.0s SLA), and concurrency.
- [x] AC: Error and validation scenarios cover upstream rate-limiting (429 -> 502), unapproved tiers (422), whitespace inputs (422), extra injected fields (422), and oversized payloads (422).
- [x] AC: Standalone runner `scripts/run-e2e.sh` and Gate 5 integrated into `scripts/run-gates.sh`.
- [x] AC: Author comprehensive `docs/TESTING.md` and clean up `README.md` removing builder jargon.

#### Implement
- [x] `tests/e2e/conftest.py` with ephemeral port allocation and subprocess lifecycle.
- [x] `tests/e2e/test_api_lifecycle.py` with core API workflows and latency checks.
- [x] `tests/e2e/test_validation_and_failures.py` with validation and upstream provider failure checks.
- [x] `src/services/__init__.py` mock search adapter support in `create_search_service`.
- [x] `scripts/run-e2e.sh` executable test runner.
- [x] `scripts/run-gates.sh` updated to run G1–G5.
- [x] `docs/TESTING.md` comprehensive testing guide.
- [x] `README.md` professional documentation overhaul.

#### Validate
- [x] G1: `ruff check . && ruff format --check .` → PASS
- [x] G2: `mypy src/ --strict` → PASS (zero errors)
- [x] G3: `bicep build infra/main.bicep` → PASS (zero warnings)
- [x] G4: `pytest tests/unit/ -v` → PASS (49/49 tests, 100% line coverage)
- [x] G5: `bash scripts/run-e2e.sh` → PASS (13/13 practical e2e tests)
- [x] Secrets scan: `SECRETS_CLEAN`

**Module Checkpoint:**
- [x] All 62 tests pass across unit and live e2e suites
- [x] 100% code coverage maintained
- [x] All mechanical gates green (G1–G5)

---

## Phase 5 — Continuity & Enterprise CRM Middleware (Slice 05)

### Module: `integrations` + CRM Connectors (Roadmap)

#### Plan
- [ ] Azure Logic App ARM/Bicep template connecting ServiceNow / Zendesk to `POST /api/v1/triage`.
- [ ] Field-mapping specification for CRM internal work note copilot card (`summary`, `suggested_action`, `matched_runbooks`).
- [ ] Webhook receiver template for direct CRM event triggers.
- [ ] Asynchronous queue ingestion adapter (Azure Service Bus / Event Grid).

---

## Done

- [x] Phase 1 (Slice 01) — Core contract & Bicep
- [x] Phase 2 (Slice 02) — Classification engine
- [x] Phase 3 (Slice 03) — Runbook retrieval & pipeline
- [x] Phase 4 (Slice 04) — Practical live E2E tests & test documentation
- [ ] Phase 5 (Slice 05) — Enterprise CRM middleware & connectors (planned)


