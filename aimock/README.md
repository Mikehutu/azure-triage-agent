# aimock — offline mocks for agentic surfaces

Deterministic, keyless mocks for everything this agent talks to: Azure OpenAI
chat completions (this slice), Azure AI Search + MCP/A2A agentic surfaces
(coming in Slice 03). Dev/test harness only — **never a runtime dependency**.

## Run

```bash
# from repo root (fixture paths in aimock.json resolve against process CWD)
aimock -c aimock/aimock.json -p 4010
curl http://127.0.0.1:4010/openai/deployments/gpt-4o-mini/chat/completions \
  -H "api-key: mock" -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"billing invoice is wrong"}],"model":"gpt-4o-mini"}'
```

## Fixture rules (the ones that bite)

- **First match wins, in file order** → empty catch-all `match: {}` must be LAST.
- `userMessage` matches the last user message (substring by default).
- Fixture paths in `aimock.json` resolve against **process CWD** (project root), not the config dir.
- `error` fixtures (e.g. 429) exercise fail-loud paths: our service must raise, never fall back.
- **MCP mock**: `mcp` stanza mounts JSON-RPC on the same port (`POST /mcp`). Handshake order (verified): `initialize` (server issues `Mcp-Session-Id` header) → `notifications/initialized` **with `mcp-session-id` header** (202) → `tools/list` / `tools/call` with that header.
- **A2A/vector stanzas** mount the same way (see aimock `fixtures/examples/`); not used yet — pattern ready.
- Never commit real keys; dummy `api-key: mock` only. See skill `ai-mock-testing` for chaos/record-replay.

## What is mocked where (Slice 03 split)
- Azure OpenAI chat → **aimock** (`fixtures/llm/chat.json`, azure provider).
- Agentic surface (MCP tool) → **aimock** (`mcp` stanza, verified handshake test).
- Azure AI Search → **in-process `FakeSearchService`** (aimock has no Azure Search REST support). Real SDK path unit-tested with a recording fake client.

## Verification

```bash
uv run pytest tests/unit/test_aimock_e2e.py -v   # spawns aimock on a free port, skips if not installed
```
