# azure-triage-agent

<one-sentence description>

## Status
Spec-driven project. See `PRD.md` for the product contract and `TASKS.md` for slice status.

## Quick start
```bash
# install (adjust to stack)
pip install -e ".[dev]"   # or: npm install / cargo build / go build

# test
pytest -q                 # or: npm test / cargo test

# run
<command>
```

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
Follow `AGENTS.md`. One slice at a time. Validate before the next slice.
