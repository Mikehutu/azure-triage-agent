# tests

## Purpose

Automated tests and fixtures proving behavior against acceptance criteria.

## Ownership

- Owns: test code and fixtures under `tests/`
- Parent owns: definition of done / AC in PRD and TASKS

## Local Contracts

- Tests are evidence, not the definition of correct — map to written AC
- Prefer regression tests for bug fixes
- No network/flaky dependencies without explicit marking

## Work Guidance

- Name tests after behavior under test
- Validator entity should not be the same chat that implemented when isolation is available

## Verification

- Test runner exits 0 with failures = 0 for the scoped suite

## Child DOX Index

- None
