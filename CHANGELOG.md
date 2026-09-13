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
