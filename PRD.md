# PRD: Enterprise Support Ticket Triage & Enrichment Agent (ticket-triage-agent)
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#prd-)

## Problem Statement
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#problem-statement)

**Who has this problem:** Enterprise B2B Tier-1 support engineers who receive hundreds of technical service requests daily from enterprise customers.

**The observable pain today:** Each ticket takes 8–12 minutes of manual effort to read, categorize into an issue domain, determine SLA urgency, and hunt down the correct internal runbook before routing. This manual work causes frequent SLA breaches on critical incidents, and adds latency to every customer support interaction.

**How they cope today:** Engineers manually read each ticket, apply tribal knowledge to classify the issue domain, estimate priority, and search internal wikis/runbooks by guesswork. Categorization is inconsistent across engineers and depends heavily on individual experience.

**Why now:** Azure OpenAI structured outputs now produce reliable, deterministic classifications; Azure AI Search hybrid retrieval makes runbook lookup feasible in sub-second time; and the enterprise already maintains a searchable knowledge index (`kb-runbooks-index`) ready to be consumed.

**Differentiation:** A stateless, managed-identity-only enrichment microservice that returns an enriched ticket payload in under 3 seconds — no direct customer auto-response, no ticket auto-closing, no CRM mutations. It augments humans rather than replacing them.

---

## Thesis (Why Build It)
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#thesis-why-build-it)

**We believe** an automated triage agent (Azure OpenAI classification + Azure AI Search RAG enrichment) will cause Tier-1 support engineers to route critical incidents faster and more consistently, resulting in reduced SLA breach frequency and lower ticket handling time.

**We'll know we're RIGHT if** the triage agent enriches tickets in under 3 seconds end-to-end, achieves >= 85% unit test coverage, and passes all mechanical G1–G5 gates on every CI run.

**We'll know we're WRONG if** the enriched payloads are inaccurate/unusable, or if the added classification latency outweighs the time saved by engineers.

---

## Goal / Non-Goals
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#goal--non-goals)

### Goals
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#goals)

- Expose a secure `POST /api/v1/triage` REST endpoint on Azure Container Apps to receive incoming ticket payloads (title, description, customer tier) and return an enriched ticket payload in under 3 seconds.
- Deterministically classify requests into fixed business domains (Billing, Authentication, Infrastructure, Product Defect) and assign SLA severity (P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW) using Azure OpenAI structured outputs.
- Enrich tickets via RAG: query Azure AI Search with hybrid search, locate the top-2 matching internal runbooks, and synthesize a 2-sentence suggested resolution for the human agent.
- Authenticate all cloud dependencies (Azure OpenAI, Azure AI Search) strictly through `azure.identity.DefaultAzureCredential` via a User-Assigned Managed Identity (zero plaintext secrets).
- Provide modular Bicep templates deploying the Container App, required service connections, and role-based access control (RBAC).

### Non-Goals
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#non-goals)

- Auto-responding directly to end-user customers (human support engineers must approve suggestions).
- Auto-closing tickets without human sign-off.
- Modifying CRM databases directly (the agent functions as a stateless enrichment microservice).

---

## Users / Personas
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#users--personas)

| Persona | Needs | Behaviors |
|---------|-------|-----------|
| Tier-1 Support Engineer | Fast, consistent categorization and SLA priority; suggested resolution steps | Routes tickets after reviewing the enriched payload; approves/edits the AI suggestion |
| Support Team Lead (Ops) | Fewer SLA breaches; consistent triage across the team | Monitors SLA metrics and routing consistency; reviews triage quality |
| Platform / DevOps Engineer | Secure, IaC-provisioned service with managed identity auth | Deploys via Bicep; manages RBAC roles and service connections |

---

## User Stories
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#user-stories)

- As a **Tier-1 support engineer**, I want to receive a pre-categorized ticket with an SLA severity and suggested action so that I can route it correctly in seconds instead of 8–12 minutes.
- As a **support team lead**, I want consistent, deterministic classifications so that SLA breaches on critical incidents are reduced.
- As a **platform engineer**, I want a zero-secret, managed-identity-authenticated service provisioned via Bicep so that deployment is repeatable and secure.

---

## Functional Requirements
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#functional-requirements)

### FR-1: Ingest & Validate Ticket Payload
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#fr-1-ingest--validate-ticket-payload)

- **Description:** Accept a `POST /api/v1/triage` request with `TicketPayload` (`ticket_id`, `customer_tier`, `subject`, `body`) and validate it against the Pydantic schema.
- **Acceptance criteria:**
  - Valid payloads return HTTP 200 with a `TriageResult` within the schema boundaries.
  - Invalid payloads return a validation error (HTTP 422) with field-level detail.
  - `customer_tier` is constrained to `STANDARD`, `PREMIUM`, or `ENTERPRISE`.
- **Edge cases:** Empty `body`, missing `ticket_id`/`subject`, unknown `customer_tier` value, oversized payloads.

---

### FR-2: Deterministic Classification & Enrichment
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#fr-2-deterministic-classification--enrichment)

- **Description:** Use Azure OpenAI (gpt-4o-mini, temperature 0.0) with structured outputs to classify category and severity, then retrieve top-2 runbooks from Azure AI Search and synthesize a 2-sentence suggested action.
- **Acceptance criteria:**
  - `category` is one of `Billing`, `Authentication`, `Infrastructure`, `Product Defect`.
  - `severity` is one of `P1_CRITICAL`, `P2_HIGH`, `P3_MEDIUM`, `P4_LOW`.
  - `matched_runbooks` returns up to 2 `RunbookReference` items from hybrid search.
  - End-to-end enrichment completes in under 3 seconds.
- **Edge cases:** No matching runbooks (empty list), Azure OpenAI throttling/errors, search index unavailable, degraded suggestions.

---

## Module Breakdown (R-PIV slices)
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#module-breakdown-r-piv-slices)

Each module is an independently testable vertical slice. Plan → Implement → Validate per module, with a **different validator entity** than the builder.

| Module | Interface | Deliverable | Validation gate |
|--------|-----------|-------------|-----------------|
| `schema` | `TicketPayload` / `TriageResult` | `src/schemas.py`, `src/config.py` | G1 lint, G2 mypy, schema unit tests |
| `triage-service` | `ITriageService` | `src/services/triage_service.py` | G4 unit tests (mocked Azure OpenAI) |
| `search-service` | `ISearchService` | `src/services/search_service.py` | G4 unit tests (mocked search client) |
| `api` | FastAPI app | `src/main.py` (`POST /api/v1/triage`) | G5 end-to-end Triage API test |
| `infra` | Bicep deployment | `infra/main.bicep` + modules | G3 `az bicep build` |

---

## Interface Definitions
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#interface-definitions)

### `ITriageService`
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#itriageservice)

```python
class ITriageService:
    def classify(self, payload: TicketPayload) -> TriageResult:
        """Classify category/severity and enrich with runbooks.

        Uses DefaultAzureCredential + Azure OpenAI structured outputs.
        Raises on missing config or failed classification; no bare except.
        """
```

```python
class ISearchService:
    def search_runbooks(self, query: str, top: int = 2) -> list[RunbookReference]:
        """Hybrid-search the kb-runbooks-index for the top-N matching runbooks."""
```

### Schemas (Enterprise Rails)
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#schemas-enterprise-rails)

```python
from pydantic import BaseModel, Field


class TicketPayload(BaseModel):
    ticket_id: str
    customer_tier: str = Field(description="STANDARD, PREMIUM, or ENTERPRISE")
    subject: str
    body: str


class RunbookReference(BaseModel):
    document_id: str
    title: str
    relevance_score: float


class TriageResult(BaseModel):
    ticket_id: str
    category: Literal["Billing", "Authentication", "Infrastructure", "Product Defect"]
    severity: Literal["P1_CRITICAL", "P2_HIGH", "P3_MEDIUM", "P4_LOW"]
    summary: str
    suggested_action: str
    matched_runbooks: list[RunbookReference]
```

---

## Infrastructure Requirements
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#infrastructure-requirements)

- **Runtime / deploy target:** Azure Container Apps (0–3 replicas, scale-to-zero enabled, CPU 0.5, Memory 1.0Gi) running the FastAPI service.
- **Data stores:** Azure AI Search service with existing enterprise index `kb-runbooks-index`.
- **Config / secrets:** All settings via Pydantic Settings (`src/config.py`); authentication via `azure.identity.DefaultAzureCredential` + User-Assigned Managed Identity. No hardcoded keys, tokens, or plaintext secrets — connection strings must not contain account keys.
- **CI/CD:** `ruff check` → `mypy src/ --strict` → `az bicep build` → `pytest tests/unit/` with >= 85% coverage (G1–G5 gates).

---

## Risks & Mitigations
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#risks--mitigations)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Azure OpenAI structured output drift / misclassification | Medium | temperature 0.0 for determinism; Literal-type schema constraints; unit tests on standard + critical fixtures |
| Search index returns irrelevant runbooks | Medium | hybrid search scoring; top-2 limit; relevance_score on each reference for agent review |
| Service dependencies unavailable (OpenAI/Search throttling) | High | fail-fast error handling; explicit errors surfaced to caller; no silent fallback |
| Secret leakage / role misconfiguration | High | DefaultAzureCredential + Managed Identity only; CI gate fails on hardcoded secrets; least-privilege RBAC |
| Container scale / cold start delays | Low | scale-to-zero with 0.5 CPU / 1.0Gi memory; under-3s target validated by G5 |

---

## Success Criteria
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#success-criteria)

1. `POST /api/v1/triage` correctly parses and enriches standard and critical test fixtures within schema boundaries, end-to-end in under 3 seconds (G5).
2. All unit tests pass with >= 85% code coverage (G4).
3. `ruff check`/`ruff format` clean, `mypy src/ --strict` zero errors (G1, G2).
4. `az bicep build --file infra/main.bicep` compiles clean ARM-JSON with zero warnings (G3).
5. Zero plaintext secrets in any file or environment setting, with authentication through Managed Identity only.

---

## Acceptance Criteria (Mechanical Gates)
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#acceptance-criteria-mechanical-gates)

| Gate | Command | Expected Outcome |
|------|---------|------------------|
| G1: Lint & Formatting | `ruff check . && ruff format --check .` | Exit code 0, clean formatting |
| G2: Type Checking | `mypy src/ --strict` | Exit code 0, zero type errors |
| G3: Infrastructure Validity | `az bicep build --file infra/main.bicep` | Compiles clean ARM-JSON with zero warnings |
| G4: Unit Tests | `pytest tests/unit/ -v` | All tests pass with >= 85% code coverage |
| G5: End-to-End Triage API | `pytest tests/unit/test_triage.py` | Correctly parses and enriches standard and critical test fixtures within schema boundaries |

---

## Delivery Slices (Backlog for TASKS.md)
[](https://github.com/Mikehutu/sdd-kit/blob/main/templates/PRD.md#delivery-slices-backlog-for-tasksmd)

### Slice 01: Core Skeleton, Schemas & Bicep Baseline
- Implement `src/schemas.py`, `src/config.py`, and basic FastAPI shell in `src/main.py`.
- Provide `infra/main.bicep` with Container App and Managed Identity declarations.
- **Pass G1, G2, G3.**

### Slice 02: Classification Engine with Azure OpenAI
- Implement `src/services/triage_service.py` using `DefaultAzureCredential` and Pydantic structured outputs.
- Add test fixtures and unit tests in `tests/unit/test_triage.py` mocking the Azure OpenAI client.
- **Pass G4.**

### Slice 03: Runbook Retrieval via Azure AI Search & Full Pipeline
- Implement `src/services/search_service.py` using Azure SDK hybrid search.
- Wire search enrichment into `POST /api/v1/triage`.
- **Pass G5** and produce validation evidence.
