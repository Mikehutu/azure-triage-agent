# CLAUDE.md — SDD Coding Conventions

> **Note:** The filename `CLAUDE.md` is a common convention for coding-agent instructions across tools. Content is agent-agnostic.


## Workflow

1. **DOX first** — Read root `AGENTS.md` (official DOX contract) and every child `AGENTS.md` on the path you will touch. See `docs/dox.md`.
2. **Spec first** — Understand the problem before touching code. Read `PRD.md` and the relevant `TASKS.md` slice first.
3. **Success criteria first** — Define what "done" looks like before implementing. The eval defines success, not the demo.
4. **Smallest change wins** — Prefer targeted edits over rewrites. Don't refactor code you weren't asked to touch.
5. **Verify after every change** — Run syntax checks, linters, tests; `sdd-dox-check` when docs/structure moved.
6. **DOX closeout** — Update owning AGENTS.md / Child DOX Index when contracts or structure changed; report intentional skips.
7. **Post-action eval** — After completion, do a quick output eval: does it meet the criteria? Is the trajectory sound?

## Code Style

- Python 3.11+, stdlib preferred. Only add dependencies with explicit approval.
- Functions do one thing. If you need "and" to describe a function, split it.
- Type hints on public functions. Simple types on private ones.
- Prefer `pathlib.Path` over `os.path`.
- No bare `except:`. Catch specific exceptions.
- Follow the repo's existing conventions over any personal preference.

## Testing

- Tests before code (TDD) for new logic.
- Each module's validation uses a DIFFERENT entity than its builder.
- A task is not done until its tests pass with 0 failures.

## Documentation

- Follow the SDD factory model: spec → criteria → impl → verify → eval.
- `CHANGELOG.md`: append only, never erase older entries.
- `TASKS.md`: check off completed items; add new phases by appending.

## Error Handling

- Fail fast and loud. Surface errors, don't swallow them.
- When blocked, report the blocker and wait for direction. Don't guess.
- Investigation before change: reproduce, then root-cause, then fix.

## Reporting

- Say what you did and why.
- Be precise about uncertainty: "I'm not sure X supports Y" tells the reader what to verify; "I think it should work" doesn't.
