# Testing Guide — azure-triage-agent

This document details the testing architecture, quality gates, test suite organization, and operational procedures for validating the **Azure Support Ticket Triage & Enrichment Agent**.

---

## Testing Philosophy & Architecture

The testing framework is built around three core principles:
1. **Zero Cloud Dependency (Mock-First)**: Every external cloud dependency (Azure OpenAI, Azure AI Search, and agentic MCP tools) is simulated offline via deterministic fixtures (`aimock`) and in-process adapters (`FakeSearchService`). The entire test harness runs without an Azure account, tenant, or network credentials.
2. **Dual-Layer Assurance**:
   - **Unit Tests (`tests/unit/`)**: Granular, isolated unit tests validating individual classes, validation schemas, error conditions, and service factories with 100% line coverage.
   - **Practical End-to-End Tests (`tests/e2e/`)**: Full black-box integration tests executing against live `uvicorn` and `aimock` processes communicating over real TCP sockets, verifying complete HTTP request/response lifecycles, latency budgets, and concurrency.
3. **Fail-Loud Verification**: Tests explicitly assert that upstream provider failures (e.g. OpenAI rate limiting or search outages) result in immediate HTTP 502 errors rather than returning degraded, fabricated, or silent fallback data.

---

## Test Directory Structure

```
tests/
├── conftest.py                   # Root test configurations
├── fixtures/
│   └── tickets.json              # Standard, critical, and expected ticket payloads
├── unit/                         # Unit & isolated component tests (49 tests, 100% coverage)
│   ├── conftest.py               # aimock session fixture for unit tests
│   ├── test_schemas.py           # Pydantic v2 input/output schema validation tests
│   ├── test_config.py            # Environment variable loading & default settings tests
│   ├── test_triage.py            # Classification engine, structured outputs & error handling tests
│   ├── test_search.py            # Azure AI Search hybrid retrieval & FakeSearchService tests
│   ├── test_api.py               # FastAPI route contract & 422/502 status tests
│   ├── test_triage_api.py        # Dependency injection pipeline tests (TestClient)
│   ├── test_aimock_e2e.py        # Direct classification tests against aimock HTTP endpoint
│   └── test_aimock_mcp.py        # MCP protocol JSON-RPC initialize/tools handshake tests
└── e2e/                          # Practical live-server end-to-end tests (13 tests)
    ├── __init__.py
    ├── conftest.py               # Live server fixture (spawns real uvicorn + aimock over TCP)
    ├── test_api_lifecycle.py     # Live HTTP tests: /healthz, triage flows, SLA latency, concurrency
    └── test_validation_and_failures.py # Live HTTP tests: 429->502, 422 validations, oversized payloads
```

---

## Mechanical Quality Gates (G1–G5)

The project enforces five automated mechanical quality gates, executed via [`scripts/run-gates.sh`](file:///home/mikehutu/projects/azure-triage-agent/scripts/run-gates.sh):

| Gate | Description | Command | Exit Criteria |
|---|---|---|---|
| **G1** | Code formatting & linting | `uv run ruff check . && uv run ruff format --check .` | 0 errors, clean format |
| **G2** | Static type checking | `uv run mypy src/ --strict` | 0 errors, strict mode |
| **G3** | Infrastructure IaC validation | `bicep build infra/main.bicep` | Compiles ARM template with 0 warnings |
| **G4** | Unit tests & code coverage | `uv run pytest tests/unit/ -v` | All pass, ≥85% coverage (100% achieved) |
| **G5** | Practical end-to-end tests | `bash scripts/run-e2e.sh` | 13/13 live HTTP tests pass |
| **SEC** | Zero hardcoded secrets scan | Automated grep scan in `run-gates.sh` | 0 hardcoded keys/secrets |

---

## Running the Tests

### 1. Run Complete Quality Pipeline (All Gates)

To execute all gates (G1 through G5 and the secrets scan) in sequence:

```bash
bash scripts/run-gates.sh
```

### 2. Run Practical End-to-End Tests

To execute only the live-server end-to-end tests:

```bash
bash scripts/run-e2e.sh
```

Alternatively, invoke pytest directly with coverage checks omitted (since the app runs in a separate subprocess):

```bash
uv run pytest tests/e2e/ --no-cov -v
```

### 3. Run Unit Tests with Code Coverage

```bash
uv run pytest tests/unit/ -v
```

To run a specific test file:

```bash
uv run pytest tests/unit/test_schemas.py -v
```

### 4. Run the Full Test Suite

Runs both unit tests and e2e tests together:

```bash
uv run pytest tests/ -v
```

---

## Practical End-to-End Test Details

The practical end-to-end tests located in [`tests/e2e/`](file:///home/mikehutu/projects/azure-triage-agent/tests/e2e/) validate real server behavior:

### Harness Lifecycle ([tests/e2e/conftest.py](file:///home/mikehutu/projects/azure-triage-agent/tests/e2e/conftest.py))
1. Allocates two dynamic ephemeral TCP ports on `127.0.0.1`.
2. Spawns `aimock` on port A with mock fixtures.
3. Spawns `uvicorn src.main:app` on port B with environment variables:
   - `AZURE_TRIAGE_MOCK=1`
   - `AZURE_TRIAGE_AZURE_OPENAI_ENDPOINT=http://127.0.0.1:<aimock_port>`
4. Polls `http://127.0.0.1:<api_port>/healthz` until healthy (HTTP 200).
5. Provides an [`httpx.Client`](file:///home/mikehutu/projects/azure-triage-agent/tests/e2e/conftest.py#L98) bound to the live base URL.
6. Gracefully terminates and reaps both subprocesses upon test session completion.

### Scenarios Covered
- **Liveness Probe**: `GET /healthz` returns `{"status": "ok"}` in <50ms.
- **Standard Triage**: `POST /api/v1/triage` processes a billing discrepancy ticket, validating that category is `Billing`, severity is `P2_HIGH`, summary and actions are generated, and matching runbooks are attached.
- **Critical Incident**: `POST /api/v1/triage` processes an authentication outage, validating category `Authentication` and severity `P1_CRITICAL`.
- **Latency Budget Enforcement**: Verifies average round-trip response latency is well within the 3.0-second SLA constraint (~5–30ms).
- **Concurrency & Statelessness**: Dispatches 10 parallel requests across a thread pool to verify that no race conditions or state leakages occur.
- **Upstream Rate Limiting (429 -> 502)**: Dispatches a request triggering a 429 response from OpenAI; verifies the API fails loud with HTTP 502 and clear error diagnostics.
- **Schema Validation (422)**: Confirms rejection of unknown customer tiers, whitespace-only fields, missing keys, unexpected extra fields (`extra="forbid"`), and oversized bodies (>20,000 characters).

---

## Offline Mock Harness (`aimock`)

The offline mock harness is configured in [`aimock/aimock.json`](file:///home/mikehutu/projects/azure-triage-agent/aimock/aimock.json):

- **Chat Completions**: Mapped to [`aimock/fixtures/llm/chat.json`](file:///home/mikehutu/projects/azure-triage-agent/aimock/fixtures/llm/chat.json) to simulate Azure OpenAI structured output responses.
  - Matches keywords (e.g. `"billing invoice"`, `"mfa outage"`, `"throttle test"`).
  - Simulates latency and upstream error conditions (e.g. 429 rate limit).
- **MCP Server**: Mounts JSON-RPC tool `get_runbook_notes` at `/mcp` for agentic tool testing.
- **Azure AI Search**: Handled in-process via [`FakeSearchService`](file:///home/mikehutu/projects/azure-triage-agent/src/services/search_service.py#L79-L89), providing deterministic runbook retrieval without network overhead.
