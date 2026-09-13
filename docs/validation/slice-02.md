# Validation — Slice 02: Classification Engine (Azure OpenAI)

Date: 2026-09-13 · Builder: project session (Hermes) · Validator: agy (separate, `slice-02-agy.md` pending)

## Acceptance Criteria (TASKS.md slice 02)

| AC | Criterion | Verdict | Evidence |
|---|---|---|---|
| AC-1 | `ITriageService.classify` returns `TriageResult` with category ∈ {Billing, Authentication, Infrastructure, Product Defect}, severity ∈ {P1_CRITICAL..P4_LOW} | VERIFIED | `tests/unit/test_triage.py` (10 tests incl. enum-out-of-range → TriageServiceError) |
| AC-2 | `create_triage_service` production branch uses `DefaultAzureCredential` (managed identity); fail loud on provider errors (no bare except, no silent fallback) | VERIFIED | `src/services/__init__.py::_build_managed_identity_client`; `test_create_service_managed_identity_branch`; `test_provider_error_raises_triage_error` |
| AC F-02 | whitespace-only body/subject rejected (agy finding) | VERIFIED | `src/schemas.py` field_validator; `test_whitespace_only_body/subject_rejected` |
| AC-3 | unit tests mock client; aimock fixtures cover success + throttling/malformed | VERIFIED | `tests/unit/test_triage.py` (mocked DI), `tests/unit/test_aimock_e2e.py` (real HTTP → aimock: billing fixture + 429 error fixture) |
| AC-4 | standard + critical test fixtures defined | VERIFIED | `tests/fixtures/tickets.json`, parametrized fixture test |
| AC-5 | Gates: G1 ruff, G2 mypy --strict, G3 bicep, G4 >=85% coverage, secrets scan | VERIFIED | `scripts/run-gates.sh` → ALL_GATES_PASS; 30 passed, 100% coverage (104 stmts); `sdd-validate` MECH_PASS; DOX_PASS |

## Validator verdict (agy, clean-room, artifacts-only)
**PASS** — all 5 ACs VERIFIED, zero MAJOR/MINOR findings (report: `slice-02-agy.md`, eval commit `6c525e2`).
- Probes all PASS: DI network isolation (poisoned socket), schema strictness (no $defs/$ref, additionalProperties everywhere), temperature/messages/response_format correctness, markdown-fence content fails loud, secret scan (only `api_key="mock"`), manual aimock e2e on port 4099.
- INFO findings: F-01 unguarded `choices[0]` → FIXED (guard + `test_no_choices_raises`, 31 tests pass). F-02 mock-key whitelist → accepted (documented). F-03 unbounded fields → Slice 03 (scheduled).
- Confidence note: live IMDS token exchange + real content-filter behavior unverifiable without Azure — code raises `TriageServiceError` on null content either way.

## Key design decisions
- **Dependency injection for the Azure OpenAI client**: `AzureOpenAITriageService(client, deployment)` — unit tests inject a recording stub; e2e injects a real `AzureOpenAI` pointed at aimock. No production code path is duplicated for tests.
- **Flat strict JSON schema** (no `$ref`/`$defs`), every object `additionalProperties: false` — Azure OpenAI json_schema mode safe, verified by assertion.
- **Mock mode** (`AZURE_TRIAGE_MOCK=1`) builds a client with `api_key="mock"` — the ONE allowed dummy-key exception in the secrets gate (documented in `scripts/run-gates.sh`).
- The throttling path is proven: aimock 429 error fixture → openai SDK raises → `TriageServiceError` (fail loud, no fallback).

## Notes / residual risk
- Real Azure OpenAI behavior (latency, content filtering, quota) untested by design — no creds. aimock deterministic replay covers the contract; real-cloud validation is a later gate.
- e2e tests skip cleanly when `aimock` is absent (CI without Node stays green; `test_aimock_e2e.py` module-scoped skip).
