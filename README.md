# azure-triage-agent

Enterprise support ticket triage & enrichment agent for Azure: classifies tickets (category + SLA severity), retrieves top-2 runbooks via Azure AI Search, and returns an enriched payload for human Tier-1 agents — stateless, managed-identity-only, no auto-responses.

## Status
Spec-driven (SDD) project. See `PRD.md` for the product contract and `TASKS.md` for slice status. Built with the sdd-kit loop: one vertical slice at a time, validated by an isolated validator (agy), all agentic surfaces mocked with aimock — **no Azure keys/tenant required** for local development, tests, or evaluation.

## Quick start
```bash
uv sync                                  # create .venv + install deps
uv run pytest tests/unit/ -v             # tests (mock-backed, offline)
uv run ruff check . && uv run ruff format --check .   # G1
uv run mypy src/ --strict                # G2
bicep build --file infra/main.bicep      # G3 (compile check)
aimock -c aimock/aimock.json -p 4010 &   # optional LLM/search/agentic mocks
uv run uvicorn src.main:app --port 8000  # run API (mock mode)
```

## Mocking (no Azure needed)
- `aimock/` — deterministic fixtures for Azure OpenAI (chat completions, structured outputs), plus MCP/A2A mocks for future agentic surfaces. Chaos injection (500s, malformed, mid-stream drops) to catch edge cases before production.
- Unit tests mock Azure SDK clients directly; the API e2e runs against mocks + a fake search adapter.

## Spec files
| File | Purpose |
|---|---|
| `PRD.md` | What and why |
| `PLANNING.md` | Phase roadmap |
| `TASKS.md` | R-PIV slices |
| `CHANGELOG.md` | Append-only history |
| `INFRASTRUCTURE.md` | Runtime and deploy |
| `AGENTS.md` | Agent harness |
| `CLAUDE.md` | Coding conventions |
| `docs/HANDOFF.md` | Multi-session handoff |

## Development rules
Follow `AGENTS.md`. One slice at a time. Validate before the next slice. Validator (agy) ≠ builder, always. No real cloud credentials in code, env docs, or commits.
- Tip: for single-file test runs use `--no-cov` (global addopts enforces >=85% only for the full suite).
