# scripts

## Purpose

Project-local automation (validate helpers, dev tasks).

## Ownership

- Owns: executable scripts in this directory
- Parent owns: which gates are required by AGENTS.md Verification Gate

## Local Contracts

- Prefer portable shell or project-native task runners
- Record validate output under `docs/validation/` when acting as a gate
- No secrets in scripts; env-var names only

## Work Guidance

- Keep `sdd-validate` (or equivalent) runnable from project root
- Fail loud on missing tools

## Verification

- `./scripts/sdd-validate .` (or documented equivalent) exits non-zero on real failures

## Child DOX Index

- None
