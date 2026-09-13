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
- [ ] agy AC verification → `docs/validation/slice-02.md`

**Module Checkpoint:**
- [ ] All tests pass, >= 85% coverage
- [ ] aimock-mocked edge cases caught (throttle 429, malformed JSON, empty content)
- [ ] Cross-agent validation passed (agy)

---

## Phase 3 — Retrieval + full pipeline (Slice 03)

### Module: `search-service` + API e2e

#### Plan (Agent: builder)
- [ ] AC: `ISearchService.search_runbooks(query, top=2)` returns up to 2 `RunbookReference` (id, title, relevance_score); empty list on no match
- [ ] AC: hybrid search against `kb-runbooks-index` (Azure AI Search SDK); failures surface, no silent fallback
- [ ] AC: `POST /api/v1/triage` end-to-end enriches in < 3s (G5) — measured against mocked search + LLM
- [ ] AC (agy F-03): unbounded fields — `max_length` on ticket_id/subject/body + API payload ceiling
- [ ] Edge cases: empty runbook match, search index unavailable, degraded suggestion, oversized payload

#### Implement (Agent: builder)
- [ ] `src/services/search_service.py` (Azure SDK hybrid search; local fake adapter for offline tests)
- [ ] `tests/unit/test_search.py` (mocked client / fake adapter)
- [ ] Wire `triage_service` + `search_service` into `src/main.py` POST handler (200 TriageResult)
- [ ] `tests/unit/test_triage_api.py` e2e (FastAPI TestClient + aimock LLM + fake search)
- [ ] `aimock/` fixtures for search + any MCP/A2A agentic surfaces

#### Validate (Agent: **agy**)
- [ ] G5: e2e Triage API test passes (standard + critical fixtures)
- [ ] G4 coverage >= 85% for full suite; G1/G2/G3 green
- [ ] aimock chaos: 500s / malformed / mid-stream drops caught
- [ ] agy AC verification → `docs/validation/slice-03.md`

**Module Checkpoint:**
- [ ] Full suite green with recorded evidence
- [ ] End-to-end latency measured (report actual ms)
- [ ] Cross-agent validation passed (agy)

---

## Done

(append as slices complete)
