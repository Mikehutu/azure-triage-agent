# tests

## Purpose

Automated tests and fixtures proving behavior against acceptance criteria.

## Ownership

- Owns: test code and fixtures under `tests/`
- Parent owns: definition of done / AC in PRD and TASKS

## Local Contracts

- Tests are evidence, not the definition of correct — map to written AC
- `tests/unit/`: fast, isolated unit tests mocking external clients (enforced >=85% code coverage, 100% achieved)
- `tests/e2e/`: practical black-box integration tests against live `uvicorn` and `aimock` processes over TCP sockets
- Zero cloud credential dependencies: all external dependencies use offline mock fixtures (`aimock`) or adapters (`FakeSearchService`)
- No network/flaky dependencies without explicit marking

## Work Guidance

- Name tests after behavior under test
- Keep unit tests fast and runnable with `uv run pytest tests/unit/ -v`
- Run live e2e tests via `bash scripts/run-e2e.sh` or `uv run pytest tests/e2e/ --no-cov -v`
- See `docs/TESTING.md` for comprehensive architecture and test scenarios

## Verification

- `uv run pytest tests/unit/ -v` exits 0 with 100% coverage
- `bash scripts/run-e2e.sh` exits 0 with all live HTTP tests passing
- `bash scripts/run-gates.sh` passes all G1–G5 gates

## Child DOX Index

- None
