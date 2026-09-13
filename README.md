# azure-triage-agent

Enterprise support ticket triage & enrichment agent for Azure: classifies tickets (category + SLA severity), retrieves the top-2 matching runbooks via Azure AI Search, and returns an enriched payload for human Tier-1 agents — stateless, managed-identity-only, **no auto-responses, no CRM writes**.

Built with the **sdd-kit** loop (spec → slice → build → isolated validation) and a **mock-first harness**: every external surface (Azure OpenAI, MCP agentic tools, Azure AI Search) is mockable offline, so the whole pipeline is developed and verified **without any Azure keys or tenant**.

## Status: COMPLETE — 3/3 slices delivered, all agy-validated

| Slice | What | Validator verdict |
|---|---|---|
| 01 Core contract | schemas, config, FastAPI shell, Bicep (Container App + managed identity + RBAC) | agy **PASS-WITH-CONCERNS** → F-01 fixed |
| 02 Classification | Azure OpenAI structured outputs (temp 0.0, strict schema, fail-loud) | agy **PASS** → F-01 fixed |
| 03 Retrieval + pipeline | Azure AI Search hybrid + full `POST /api/v1/triage` (200, <3s) + MCP mock | agy **PASS** — "ready per PRD Success Criteria" → F-01 fixed |

**Verified:** 47 tests · 100% coverage (enforced ≥85%) · ruff clean · `mypy --strict` clean · Bicep zero-warning · secrets scan clean · `sdd-validate` MECH_PASS · DOX_PASS. Measured e2e latency ~5.7 ms (PRD budget: 3 s).

## Architecture

- `src/schemas.py` — Pydantic v2 contracts: `TicketPayload` (Literal enums, extra=forbid, non-blank, length ceilings) → `TriageResult`
- `src/services/triage_service.py` — `ITriageService` / `AzureOpenAITriageService`: structured-output classification; provider errors, empty content, malformed JSON, out-of-enum values, mismatched ticket_id, empty choices → **all raise `TriageServiceError`** (fail loud, no silent fallback)
- `src/services/search_service.py` — `ISearchService` / `AzureAISearchService` (hybrid `search_mode="all"`, deduped results) + `FakeSearchService` offline adapter; failures → `SearchServiceError`
- `src/main.py` — `POST /api/v1/triage` wired end-to-end; provider failures → **HTTP 502** (never a fabricated result)
- `infra/main.bicep` — Azure Container Apps (scale 0–3, 0.5 vCPU/1Gi), user-assigned managed identity, least-privilege RBAC (Azure OpenAI User, Search Index Data Reader), zero secrets

## Quick start (offline, no Azure keys)

```bash
uv sync                                    # deps + dev group
bash scripts/run-gates.sh                  # G1-G4 + secrets scan (fail-loud)
uv run pytest tests/unit/ -v               # 47 tests (--no-cov for single files)
bicep build infra/main.bicep               # G3 (standalone bicep; CI can use az bicep build)

# run the API against mocks:
aimock -c aimock/aimock.json -p 4010 &     # LLM + MCP mocks (from repo root)
AZURE_TRIAGE_MOCK=1 \
AZURE_TRIAGE_AZURE_OPENAI_ENDPOINT=http://127.0.0.1:4010 \
uv run uvicorn src.main:app --port 8000
```

## Mocking map (no Azure needed)

- **Azure OpenAI chat** → aimock (`aimock/fixtures/llm/chat.json`: success, mfa, fallback, **429 chaos**) — proven over real HTTP in tests; 429 must raise, never degrade
- **MCP agentic surface** → aimock `mcp` stanza (`get_runbook_notes`), full JSON-RPC handshake test (session-id header gotcha documented)
- **Azure AI Search** → `FakeSearchService` (aimock has no Azure Search REST); real SDK path unit-tested with a recording fake client
- **A2A / vector / AG-UI** → same stanza pattern, not yet used (see sdd-kit `docs/mock-first.md`)

## Validation evidence

| Report | Content |
|---|---|
| `docs/validation/slice-01.md` (+ `slice-01-agy.md`) | AC matrix + agy clean-room report |
| `docs/validation/slice-02.md` (+ `slice-02-agy.md`) | AC matrix + agy clean-room report |
| `docs/validation/slice-03.md` (+ `slice-03-agy.md`) | AC matrix + agy clean-room report (probes: runbook collision, MCP fault injection, 5.7 ms latency) |
| `docs/validation/latest.md` | Mechanical gate evidence (`sdd-validate`) |
| `docs/HANDOFF.md` | Multi-session state + environment notes |

## Spec files

| File | Purpose |
|---|---|
| `PRD.md` | What and why |
| `PLANNING.md` | Phase roadmap |
| `TASKS.md` | R-PIV slices (all checked) |
| `CHANGELOG.md` | Append-only history |
| `INFRASTRUCTURE.md` | Runtime and deploy |
| `AGENTS.md` / `CLAUDE.md` | Agent harness / conventions |
| `aimock/` | Mock harness (AGENTS.md registered in DOX index) |
| `kb/SOURCES.md` | Official-doc grounding (role GUIDs, structured outputs, aimock) |

## Development rules

Follow `AGENTS.md`. One slice at a time. Validate before the next slice. Validator (agy) ≠ builder, always. No real cloud credentials in code, env docs, or commits. Mock-first: no external surface is real until it has a mock + failure-mode fixture.
