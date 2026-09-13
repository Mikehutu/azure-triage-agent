# Independent Validation Report — Slice 02: Classification Engine (Azure OpenAI)

- **Date:** 2026-09-13
- **Role:** Independent Validator (agy)
- **Target:** Slice 02 (`triage-service` — Azure OpenAI structured outputs classification)
- **Evaluated Commit:** `6c525e2`
- **Methodology:** Clean-room artifacts-only evaluation against `PRD.md` (FR-2, Interface Definitions) and `TASKS.md` Phase 2. The builder's claim document (`docs/validation/slice-02.md`) was treated strictly as claim-only; every claim was independently verified with live test runs, code inspection, and custom probes.

---

## Validator verdict: PASS

All 5 Acceptance Criteria are mechanically verified, fully covered by automated tests, and adhere strictly to the PRD and TASKS contracts. Slice 01 findings F-01 (Bicep CPU float) and F-02 (whitespace-only payload rejection) have been confirmed resolved. The classification service correctly implements runtime protocol conformance, strict JSON schema definition without `$defs`/`$ref`, fail-loud error handling with zero bare excepts, and network-isolated dependency injection.

---

## Acceptance Criteria Matrix

| AC | Criterion | Verdict | Evidence (command / line reference) |
|---|---|---|---|
| **AC-1** | `src/services/triage_service.py` defines `ITriageService` protocol + `AzureOpenAITriageService`. `classify()` returns `TriageResult` with category ∈ {Billing, Authentication, Infrastructure, Product Defect} and severity ∈ {P1_CRITICAL..P4_LOW}. Conforms to PRD Interface Definitions. | **VERIFIED** | `src/services/triage_service.py:29-38` defines `@runtime_checkable class ITriageService(Protocol)`. `AzureOpenAITriageService` implements `classify(TicketPayload) -> TriageResult`. Category and Severity enums strictly match `PRD.md:158-159`. All schema types match `PRD.md:143-163`. `uv run pytest tests/unit/test_triage.py` (10 passed). |
| **AC-2** | Production client path uses `DefaultAzureCredential` via `azure_ad_token_provider` (no hardcoded keys). Fail loud: provider errors, empty content, malformed JSON, out-of-enum values, and mismatched `ticket_id` ALL raise `TriageServiceError` without bare except or silent fallback. | **VERIFIED** | `src/services/__init__.py:22-38` configures `_build_managed_identity_client` using `DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default").token` with zero secrets. `src/services/triage_service.py:106-145` raises `TriageServiceError` on all failure branches. Covered by `test_provider_error_raises_triage_error`, `test_empty_content_raises`, `test_malformed_json_raises`, `test_out_of_enum_value_raises`, `test_mismatched_ticket_id_raises`, and `test_create_service_managed_identity_branch`. |
| **AC-3** | F-02 resolution: whitespace-only body/subject rejected with HTTP 422 / ValidationError. | **VERIFIED** | `src/schemas.py:30-36` implements `@field_validator("subject", "body")` rejecting `not value.strip()`. `tests/unit/test_schemas.py:53-61` tests whitespace-only body (`"   \t\n  "`) and subject (`"   "`). Independent probe verified FastAPI route returns HTTP 422 with `loc: ['body', 'body']` and `loc: ['body', 'subject']`. |
| **AC-4** | `aimock` harness works end-to-end over REAL HTTP (billing fixture → Billing/P2_HIGH; 429 error fixture → `TriageServiceError`; catch-all is LAST; first-match-wins). | **VERIFIED** | `aimock/aimock.json` configures Azure provider fixtures. `aimock/fixtures/llm/chat.json` defines first-match-wins fixtures with catch-all `{}` at lines 35-39. `uv run pytest tests/unit/test_aimock_e2e.py -v -rs` executed against live `aimock` process listening on ephemeral port: both `test_aimock_classification_billing` and `test_aimock_throttling_surfaces_error` passed. |
| **AC-5** | Full gates pass (`bash scripts/run-gates.sh` ends with `ALL_GATES_PASS`; G4 >=85% coverage; `SECRETS_CLEAN`). `PATH="$PWD/.venv/bin:$PATH" ./scripts/sdd-validate .` exits `MECH_PASS`. `./scripts/sdd-dox-check .` exits `DOX_PASS`. | **VERIFIED** | `bash scripts/run-gates.sh` exited 0 (G1 PASS, G2 PASS, G3 PASS, G4 PASS 30/30 passed with 100% statement coverage across 104 statements, SECRETS_CLEAN, ALL_GATES_PASS). `sdd-validate` exited 0 (`MECH_PASS`). `sdd-dox-check` exited 0 (`DOX_PASS` across all 7 indexed children). |

---

## Verification of Builder Claims (`docs/validation/slice-02.md`)

| Builder Claim | Status | Validator Verification Notes |
|---|---|---|
| `ITriageService.classify` returns `TriageResult` with valid category and severity | **CONFIRMED** | Verified in `src/services/triage_service.py` and tested via `test_triage.py`. |
| `create_triage_service` uses `DefaultAzureCredential` in production branch; fail loud on errors | **CONFIRMED** | Verified in `src/services/__init__.py:22-38`. `test_create_service_managed_identity_branch` proves token provider callable and no `api_key`. |
| Whitespace-only body/subject rejected | **CONFIRMED** | Tested at unit schema level and FastAPI endpoint integration level. |
| Unit tests mock client; aimock fixtures cover success + throttling/malformed | **CONFIRMED** | DI client mock verified in unit tests; aimock tested over real HTTP socket. |
| Standard + critical test fixtures defined | **CONFIRMED** | `tests/fixtures/tickets.json` contains standard and critical tickets with expected classifications. |
| Gates G1-G4 + secrets scan pass (30 passed, 100% coverage, MECH_PASS, DOX_PASS) | **CONFIRMED** | Verified with recorded script runs; exit code 0 across all gates. |

---

## Findings Table

| ID | Severity | Location | Description | Recommendation |
|---|---|---|---|---|
| **F-01** | **INFO** | `src/services/triage_service.py:134` | **Unguarded `choices[0]` index access:** If an upstream response or faulty mock returns an empty choices list (`completion.choices = []`), `choices[0]` raises an unhandled `IndexError` rather than being caught and transformed into `TriageServiceError`. | Consider catching `(IndexError, AttributeError)` or validating `if not completion.choices:` before indexing, raising `TriageServiceError("classification returned no choices")`. |
| **F-02** | **INFO** | `src/services/__init__.py:47` & `scripts/run-gates.sh:30` | **Secrets gate regex exception:** `_build_mock_client` hardcodes `api_key="mock"`, requiring a specific exemption filter `grep -v 'api_key="mock"'` in `run-gates.sh`. While strictly safe (key value is literally `"mock"`, only invoked when `Settings.mock=True`, and real keys cannot match the filter), keeping dummy keys in `src/` requires maintaining whitelist exceptions. | For Slice 03 or future hardening, consider defaulting mock API key from environment configuration (`settings.azure_openai_api_key`) or passing dummy keys only from test fixtures to keep `src/` 100% free of secret assignment tokens. |
| **F-03** | **INFO** | `src/schemas.py:25-28` | **Unbounded String Fields (Carried over from Slice 01):** `TicketPayload` fields lack `max_length` bounds. | As scheduled in `TASKS.md` Phase 3, implement field limits and API payload size ceilings during Slice 03 API hardening. |

*Note: Zero MAJOR or MINOR findings. All findings are INFO level observations.*

---

## Probe Results & Deep Verification

### 1. DI Boundary Network Isolation
- **Probe:** Replaced `socket.socket` with a poison function raising an assertion if any network socket is opened. Executed `AzureOpenAITriageService.classify` with a recording mock client.
- **Observed:** `service.classify()` executed cleanly without touching the network stack. Pure dependency injection is maintained; no client initialization or implicit network access occurs in `classify()`.
- **Verdict: PASS.**

### 2. Schema Strictness & Absence of `$defs`/`$ref`
- **Probe:** Inspected the JSON output of `_strict_schema()`:
  - Verified no `$defs` or `$ref` strings exist in the schema.
  - Verified root object defines `"additionalProperties": False`.
  - Verified nested items schema for `matched_runbooks` defines `"additionalProperties": False`.
  - Verified all declared root properties match `required`: `['category', 'matched_runbooks', 'severity', 'suggested_action', 'summary', 'ticket_id']`.
  - Verified all nested runbook properties match `required`: `['document_id', 'relevance_score', 'title']`.
- **Verdict: PASS.** Strictly conforms to Azure OpenAI Structured Outputs requirements.

### 3. Temperature, Model, Messages, and Response Format
- **Probe:** Inspected request payload passed to `chat.completions.create` captured by recording client in `test_classify_builds_correct_request`:
  - `temperature == 0.0`
  - `model == "gpt-4o-mini"` (matches configured deployment)
  - `messages[0]["role"] == "system"` (contains system prompt with strict classification guidance)
  - `messages[1]["role"] == "user"` (formats `ticket_id`, `customer_tier`, `subject`, `body`)
  - `response_format["type"] == "json_schema"`
  - `response_format["json_schema"]["strict"] is True`
  - `response_format["json_schema"]["name"] == "triage_result"`
- **Verdict: PASS.**

### 4. Edge Cases: Markdown Fences & Surrounding Whitespace
- **Probe A (Whitespace around JSON):** Fed `"  \n\t  " + valid_json + " \n\n  "` as completion content.
  - **Result:** Successfully parsed by `json.loads` and validated into `TriageResult`.
- **Probe B (Markdown code fences):** Fed `"```json\n" + valid_json + "\n```"` as completion content.
  - **Result:** Raised `TriageServiceError` (`classification returned invalid payload: Expecting value: line 1 column 1`).
  - **Note:** In Azure OpenAI with `strict: True` structured outputs, the API guarantees pure JSON without fences. If fences were ever produced by an upstream proxy error, the service fails loud as expected.
- **Verdict: PASS.**

### 5. Security Scan & Secrets Audit
- **Regex Scan:** Executed pattern `(api[_-]?key|access[_-]?key|secret|password|token)\s*=\s*["\'][^"\']+["\']` across all Python files in `src/`.
  - **Result:** Exactly 1 match found: `src/services/__init__.py:47 -> api_key="mock"`.
- **Fixture Scan:** Audited all JSON files in `tests/fixtures/` and `aimock/fixtures/`.
  - **Result:** Zero secret patterns, zero 32-character hex tokens, zero JWT structures.
- **`.gitignore` Audit:** Verified `.env` and environment file variants are tracked in `.gitignore`.
- **Verdict: PASS.**

### 6. Live Manual End-to-End Execution via aimock (Port 4099)
- **Probe:** Launched standalone `aimock -c aimock/aimock.json -p 4099` as a background process from repository root.
- **Execution:** Instantiated `AzureOpenAI(azure_endpoint="http://127.0.0.1:4099", api_key="mock")` and initialized `AzureOpenAITriageService`. Dispatched `TicketPayload` with `subject="billing invoice mismatch query"`.
- **Observed:**
  - HTTP request resolved over loopback TCP to `aimock`.
  - Returned structured classification: `ticket_id='T-8001'`, `category='Billing'`, `severity='P2_HIGH'`, `matched_runbooks=[]`.
  - Service parsed and returned a valid `TriageResult` instance.
- **Verdict: PASS.**

---

## Confidence Note (Cloud Verification Boundaries)

The following aspects were verified locally via mocks, `aimock` HTTP replay, and static contract analysis, and **could not be verified against a live Azure subscription**:
1. **Live Azure OpenAI Managed Identity Token Exchange:** Verification that the live `DefaultAzureCredential()` token acquired from Azure IMDS in Container Apps is accepted by Cognitive Services scope `https://cognitiveservices.azure.com/.default` without tenant-specific conditional access policies.
2. **Azure OpenAI Production Quota / Content Filtering:** Production behavior when Azure OpenAI Content Safety filters trigger (e.g. `finish_reason: "content_filter"` returning null content). The service is confirmed to raise `TriageServiceError("classification returned empty content")` when content is null.
