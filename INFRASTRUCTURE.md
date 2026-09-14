# INFRASTRUCTURE — azure-triage-agent

## Runtime
- **Platform:** Linux container (Azure Container Apps) running FastAPI (Python 3.11+); local dev on WSL2.
- **Entry point:** `uvicorn src.main:app` (package `qa_agent`-style: `src` layout, installed via `pip install -e .`).
- **Ports:** 8000 (local dev / container HTTP).

## Data
- **Store:** No local DB. Retrieval via Azure AI Search (existing enterprise index `kb-runbooks-index`); no migrations.
- **Corpus/cache:** none persisted; stateless service.

## Config & Secrets
- **Env vars (NAMES only, never values):** `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_SEARCH_SERVICE_ENDPOINT`, `AZURE_SEARCH_INDEX_NAME` (all consumed by Pydantic Settings in `src/config.py`). Optional `AZURE_TRIAGE_MOCK=1` for offline mode.
- **Secrets manager:** Azure Key Vault + User-Assigned Managed Identity; `DefaultAzureCredential` everywhere. Zero plaintext tokens/keys committed. For tests: aimock (`aimock/`) and mocked SDK clients only.

## Deploy
- **Build:** `uv build` / `docker build` (Container Apps); infra as code in `infra/main.bicep` (Container App + managed identity + RBAC role assignments).
- **CI/CD:** Automated via `scripts/run-gates.sh`: G1 `ruff check . && ruff format --check .` → G2 `mypy src/ --strict` → G3 `bicep build --file infra/main.bicep` → G4 `pytest tests/unit/ -v` (100% coverage, >=85% floor) → G5 practical e2e live server tests (`bash scripts/run-e2e.sh`) → zero-secrets scan.
  - Note: locally G3 is run with the standalone `bicep` CLI (`~/.local/bin/bicep`); in CI with `az bicep build`. Both compile the same Bicep.
- **Rollback:** Container Apps revision rollback; immutable image tag per release.

## Dev Environment
- **Setup:** `uv sync` (creates `.venv`, installs deps + dev group).
- **Test (All Gates):** `bash scripts/run-gates.sh` (runs G1–G5).
- **Test (Unit):** `uv run pytest tests/unit/ -v` (add `pytest -q` for quick).
- **Test (Practical E2E):** `bash scripts/run-e2e.sh` or `uv run pytest tests/e2e/ --no-cov -v`.
- **Lint:** `uv run ruff check . && uv run ruff format --check .`
- **Mock:** `aimock -c aimock/aimock.json -p 4010` for offline LLM/search/agentic mocks (see `aimock/README.md` and `docs/TESTING.md`).
