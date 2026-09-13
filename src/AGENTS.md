# src

## Purpose

Primary implementation source tree.

## Ownership

- Owns: application/library code under `src/`
- Parent owns: cross-cutting engineering standards, release criteria

## Local Contracts

- Follow root CLAUDE.md / language conventions
- Public APIs typed where the stack supports it
- No credentials in source; configuration via env names

## Work Guidance

- Smallest change that meets written AC
- Pair behavior changes with tests under `tests/` (or project equivalent)

## Verification

- Project lint + test commands (see INFRASTRUCTURE.md / root Project-specific)

## Child DOX Index

- Add child AGENTS.md when a package/subsystem becomes its own durable boundary
