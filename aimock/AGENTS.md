# AGENTS.md — aimock/ (mock harness)

## Purpose
Deterministic offline mocks for external agentic surfaces (Azure OpenAI chat, Azure AI Search, MCP/A2A). Never a runtime dependency; test harness only.

## Ownership
Harness + fixtures. Owns aimock.json, fixtures/, README.md. Not part of the shipped service image.

## Local Contracts
- `aimock.json` fixture paths resolve against repo root (process CWD).
- Catch-all fixture must be last; first match wins in file order.
- Dummy keys only (`mock`); real credentials never enter this directory.

## Work Guidance
- Add a fixture per edge case BEFORE wiring a test that hits that surface (mock-first).
- For chaos paths (429, malformed, mid-stream drops) use error fixtures and assert our service raises `TriageServiceError` or equivalents — never a silent fallback.

## Verification
- `uv run pytest tests/unit/test_aimock_e2e.py -v` (skips cleanly if aimock absent).
- Manual: `aimock -c aimock.json -p 4010` then curl a chat completion.

## Child DOX Index
(none)
