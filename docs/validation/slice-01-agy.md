# Independent Validation Report — Slice 01: Core Skeleton, Schemas & Bicep Baseline

- **Date:** 2026-09-13
- **Role:** Independent Validator (agy)
- **Target:** Slice 01 (`schema` + `config` + API shell + Bicep baseline)
- **Evaluated Commit:** `0eed6cd`
- **Methodology:** Clean-room artifacts-only evaluation against PRD and TASKS contracts. The builder's report (`docs/validation/slice-01.md`) was treated as claim-only; every claim was independently verified with live commands and custom probe executions.

---

## Validator verdict: PASS-WITH-CONCERNS

All 5 Acceptance Criteria are mechanically verified and meet the Slice 01 specification. However, a **PASS-WITH-CONCERNS** verdict is rendered due to a real-cloud deployment risk identified in the Bicep container configuration (**F-01**: `cpu: 1` with `memory: '1.0Gi'` risks deployment rejection under Azure Container Apps consumption pairing rules) and an edge-case validation gap (**F-02**: whitespace-only ticket bodies pass validation). Neither finding blocks local development of Slice 02, but both should be addressed prior to real infrastructure deployment.

---

## Acceptance Criteria Matrix

| AC | Criterion | Verdict | Evidence (command / line reference) |
|---|---|---|---|
| **AC-1** | `src/schemas.py` defines `TicketPayload`, `RunbookReference`, `TriageResult` exactly per PRD (fields, Literal enums for category/severity/tier, no secrets) | **VERIFIED** | `src/schemas.py:10-47` matches PRD Interface Definitions (PRD lines 140–163) and FR-1 constraints. All enums constrained via `Literal[...]`. `TicketPayload` enforces `model_config = {"extra": "forbid"}` and `min_length=1` on text fields. `uv run pytest tests/unit/test_schemas.py` (9 passed). |
| **AC-2** | `src/config.py` uses `pydantic-settings`; only env var NAMES referenced; no hardcoded credentials anywhere in `src/` or `infra/` | **VERIFIED** | `src/config.py:14-32` implements `Settings(BaseSettings)` with `env_prefix="AZURE_TRIAGE_"`, default endpoints point to placeholder domains (`placeholder.openai.azure.com`), no secrets. Grep check: `grep -rniE "(api[_-]?key\|access[_-]?key\|secret\|password\|token)[[:space:]]*=[[:space:]]*[\"'][^\"']+" src/ infra/` exited with code 1 (zero matches). |
| **AC-3** | `POST /api/v1/triage` returns 422 with field-level detail for: unknown `customer_tier`, missing `ticket_id`, empty body, unknown extra fields | **VERIFIED** | `tests/unit/test_api.py` and independent probe script run against `FastAPI` test client: <br>1. Unknown tier (`"GOLD"`): HTTP 422, `loc: ['body', 'customer_tier']`<br>2. Missing `ticket_id`: HTTP 422, `loc: ['body', 'ticket_id']`<br>3. Empty body (`""`): HTTP 422, `loc: ['body', 'body']`<br>4. Unknown extra field (`"extra": 1`): HTTP 422, `loc: ['body', 'extra']`<br>5. Empty JSON body (`{}`): HTTP 422, lists 4 missing fields.<br>Command: `uv run pytest tests/unit/ -v` (16 passed). |
| **AC-4** | `infra/main.bicep` compiles with ZERO warnings; user-assigned managed identity; least-privilege built-in roles; NO secrets in env; scale-to-zero; scale max 3; CPU/memory set | **VERIFIED** | `bicep build infra/main.bicep` exited with code 0 (zero warnings, zero errors). Verified in `infra/main.bicep`: user-assigned identity (L34–40, L81–86); role `5e0bd9bd-7b93-4f28-af87-19fc36ad61bd` (Cognitive Services OpenAI User, L31, L58–66); role `1407120a-92aa-4202-b7e9-c0e197c71c8f` (Search Index Data Reader, L32, L68–76); env vars carry resource endpoints/names only (L103–120); `minReplicas: 0`, `maxReplicas: 3` (L130–131); `cpu: 1`, `memory: '1.0Gi'` (L121–126). |
| **AC-5** | Full gate suite passes (`bash scripts/run-gates.sh` ends with `ALL_GATES_PASS`; G4 needs >=85% coverage) | **VERIFIED** | `bash scripts/run-gates.sh` executed cleanly (exit code 0):<br>- G1: `ruff check . && ruff format --check .` -> PASS<br>- G2: `mypy src/ --strict` -> PASS (4 files, 0 errors)<br>- G3: `bicep build infra/main.bicep` -> PASS (0 diagnostics)<br>- G4: `pytest tests/unit/ -v` -> PASS (16 tests passed, 100% statement coverage: 46/46 statements)<br>- SECRETS: Regex scan -> `SECRETS_CLEAN`<br>- Terminal output: `ALL_GATES_PASS`. |

---

## Findings Table

| ID | Severity | Location | Description | Recommendation |
|---|---|---|---|---|
| **F-01** | **MINOR** | `infra/main.bicep:124-125` | **Bicep CPU Deviation & Container Apps Allocation Ratio:** PRD specifies `CPU 0.5, Memory 1.0Gi`. Bicep declares `cpu: 1, memory: '1.0Gi'`. In Azure Container Apps Consumption workload profiles, vCPU and memory must adhere to fixed pairings (specifically 0.5 vCPU : 1.0 GiB, or 1.0 vCPU : 2.0 GiB). Deploying `1 vCPU` with `1.0Gi` memory will likely be rejected by Azure Resource Manager at deploy time. | Replace `cpu: 1` with `cpu: json('0.5')` in `infra/main.bicep`. As verified by probe, `cpu: json('0.5')` compiles with ZERO Bicep warnings, emits valid ARM JSON (`"[json('0.5')]"`), and preserves the 0.5 vCPU / 1.0Gi ratio. |
| **F-02** | **MINOR** | `src/schemas.py:27` | **Whitespace-Only Ticket Body:** `TicketPayload.body = Field(min_length=1)` rejects `""`, but permits whitespace-only strings (e.g., `"   \t\n  "`), which returns 501 rather than 422. Sending whitespace-only bodies to the classification LLM in Slice 02 will waste tokens and could cause hallucination. | Add a field validator or regex pattern (e.g. `pattern=r'\S'`) to `TicketPayload` in Slice 02 to reject whitespace-only subjects and bodies. |
| **F-03** | **INFO** | `src/schemas.py:24-27` | **Unbounded String Fields:** While `min_length=1` is enforced, there are no upper bounds (`max_length`) on `ticket_id`, `subject`, or `body`. A payload with a 10MB body or a 50,000 character ticket ID passes schema validation. | Address in Slice 03 as part of API gateway hardening (e.g., `max_length=64` for `ticket_id`, `max_length=256` for `subject`, and a body length ceiling or FastAPI payload size limit). |
| **F-04** | **INFO** | `src/main.py:36` | **Interim 501 HTTP Status for Valid Ingress:** Valid payloads return HTTP 501 ("triage pipeline not wired yet") instead of HTTP 200 with `TriageResult` (PRD FR-1). | Acceptable for Slice 01. TASKS.md Phase 1 scopes the API shell and validation only; service wiring is explicitly scheduled for Slice 02/03. Returning 501 conforms to the "fail loud, fail fast, never stub fake results" engineering rail. |

*Note: There are no MAJOR findings. Slice 01 is eligible to ship into Slice 02 planning.*

---

## Probe Results & Stress Testing

Independent probes were executed directly against the codebase and runtime components:

### 1. Interim 501 vs PRD FR-1 Contract
- **Test:** Dispatched valid `TicketPayload` (`{"ticket_id": "T-1", "customer_tier": "STANDARD", "subject": "Subject", "body": "Body"}`) to `POST /api/v1/triage`.
- **Observed:** HTTP 501 `{"detail": "triage pipeline not wired yet (slice 02)"}`.
- **Verdict: ACCEPTABLE.** Returning 501 is the correct architectural decision for Slice 01. Faking a 200 response with synthetic `TriageResult` values would violate SDD core standards ("fail loud, fail fast; never fake results"). Schema validation runs *before* the route handler, guaranteeing the validation contract is fully enforced.

### 2. Bicep CPU 0.5 vs 1.0 Investigation
- **Test:** Tested alternate Bicep resource definitions in an isolated sandbox:
  1. `cpu: 0.5` -> Failed compilation with `BCP020: Expected a function or property name` and `BCP055: Cannot access properties of type "0"` (Bicep language does not support float literal syntax).
  2. `cpu: '0.5'` -> Produced diagnostic `Warning BCP036: The property "cpu" expected a value of type "int | null" but the provided value is of type "'0.5'"`. (Violates AC-4 zero-warning mandate).
  3. `cpu: 1` (Builder's choice) -> Compiles with 0 warnings, but pairs 1 vCPU with 1.0Gi memory.
  4. `cpu: json('0.5')` -> **Compiles with 0 warnings and 0 errors**, generating valid ARM JSON `"[json('0.5')]"` which ARM resolves to number `0.5` at deploy time.
- **Verdict:** Builder's claim that naive `0.5` / `'0.5'` fails zero-warning build is confirmed; however, `json('0.5')` resolves both the Bicep warning constraint and the Azure Container Apps pairing constraint.

### 3. Ingress Edge Cases & Path Tampering
- **Whitespace-only body (`"   \t\n  "`):** Returned HTTP 501 (passed Pydantic validation). Flagged as **F-02**.
- **Ticket ID boundary (1 char):** `ticket_id: "X"` returned HTTP 501 (valid under `min_length=1`). Acceptable.
- **Ticket ID boundary (10,000 chars):** Returned HTTP 501 (passed validation). Flagged as **F-03**.
- **Customer tier case sensitivity (`"standard"`, `"Standard"`):** Returned HTTP 422 with `literal_error` on `customer_tier`. Correct per PRD FR-1.
- **Non-JSON `Content-Type` (`text/plain` with raw body):** Returned HTTP 422 `model_attributes_type`. Correct.
- **Trailing slash (`POST /api/v1/triage/`):** Returned HTTP 307 redirect to canonical `/api/v1/triage`. Correct FastAPI behavior.
- **Query tampering (`POST /api/v1/triage?admin=true&drop=1`):** Query parameters ignored, payload validated as expected. Correct.
- **HTTP method tampering (`GET /api/v1/triage`):** Returned HTTP 405 Method Not Allowed. Correct.

### 4. Security & Secret Exposure Audit
- **Grep Pattern Scan:** Executed regex scan across entire repository:
  `grep -rniE "(api[_-]?key|access[_-]?key|secret|password|token)[[:space:]]*=[[:space:]]*[\"'][^\"']+" . --exclude-dir=.git --exclude-dir=.venv`
  Returned exit code 1 (zero hardcoded secret assignments found).
- **`.gitignore` Audit:** Checked `.gitignore` lines 31–35. Contains `.env`, `.env.*`, `!.env.example`. No tracked or untracked `.env` files present on filesystem outside `.venv`.
- **Documentation Audit:** Inspected `README.md` and `INFRASTRUCTURE.md`. Neither requests or instructs users to commit or configure plaintext credentials. Both mandate `DefaultAzureCredential` via User-Assigned Managed Identity.

---

## Confidence Note (Cloud Verification Boundaries)

The following items were verified locally via static analysis, compilation, and unit mocks, and **could not be verified against a live Azure subscription**:
1. **Live Container Apps Resource Deployment:** Whether Azure Container Apps accepts `cpu: 1` paired with `memory: '1.0Gi'` without throwing a quota or ratio error (known Azure requirement: 1 vCPU requires 2.0Gi memory).
2. **Live RBAC Resolution:** Whether the service principal created for the User-Assigned Managed Identity is granted role assignment permissions on live Cognitive Services and Azure AI Search accounts without tenant-level policy restrictions.
3. **Live Token Acquisition:** `DefaultAzureCredential` behavior when executing within the Container Apps runtime container using IMDS (Instance Metadata Service).
