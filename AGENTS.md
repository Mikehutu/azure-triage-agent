# DOX framework

- DOX is highly performant AGENTS.md hierarchy installed here
- Agent must follow DOX instructions across any edits
- Upstream: https://github.com/agent0ai/dox — installed by sdd-kit (official contract below)
- SDD project-rail instructions follow the DOX sections. **No child may weaken DOX.**

## Core Contract

- AGENTS.md files are binding work contracts for their subtrees
- Work products, source materials, instructions, records, assets, and durable docs must stay understandable from the nearest applicable AGENTS.md plus every parent AGENTS.md above it

## Read Before Editing

1. Read the root AGENTS.md
2. Identify every file or folder you expect to touch
3. Walk from the repository root to each target path
4. Read every AGENTS.md found along each route
5. If a parent AGENTS.md lists a child AGENTS.md whose scope contains the path, read that child and continue from there
6. Use the nearest AGENTS.md as the local contract and parent docs for repo-wide rules
7. If docs conflict, the closer doc controls local work details, but no child doc may weaken DOX

Do not rely on memory. Re-read the applicable DOX chain in the current session before editing.

## Update After Editing

Every meaningful change requires a DOX pass before the task is done.

Update the closest owning AGENTS.md when a change affects:

- purpose, scope, ownership, or responsibilities
- durable structure, contracts, workflows, or operating rules
- required inputs, outputs, permissions, constraints, side effects, or artifacts
- user preferences about behavior, communication, process, organization, or quality
- AGENTS.md creation, deletion, move, rename, or index contents

Update parent docs when parent-level structure, ownership, workflow, or child index changes. Update child docs when parent changes alter local rules. Remove stale or contradictory text immediately. Small edits that do not change behavior or contracts may leave docs unchanged, but the DOX pass still must happen.

## Hierarchy

- Root AGENTS.md is the DOX rail: project-wide instructions, global preferences, durable workflow rules, and the top-level Child DOX Index
- Child AGENTS.md files own domain-specific instructions and their own Child DOX Index
- Each parent explains what its direct children cover and what stays owned by the parent
- The closer a doc is to the work, the more specific and practical it must be

## Child Doc Shape

- Create a child AGENTS.md when a folder becomes a durable boundary with its own purpose, rules, responsibilities, workflow, materials, or quality standards
- Work Guidance must reflect the current standards of the project or user instructions; if there are no specific standards or instructions yet, leave it empty
- Verification must reflect an existing check; if no verification framework exists yet, leave it empty and update it when one exists

Default section order:

- Purpose
- Ownership
- Local Contracts
- Work Guidance
- Verification
- Child DOX Index

## Style

- Keep docs concise, current, and operational
- Document stable contracts, not diary entries
- Put broad rules in parent docs and concrete details in child docs
- Prefer direct bullets with explicit names
- Do not duplicate rules across many files unless each scope needs a local version
- Delete stale notes instead of explaining history
- Trim obvious statements, repeated rules, misplaced detail, and warnings for risks that no longer exist

## Closeout

1. Re-check changed paths against the DOX chain
2. Update nearest owning docs and any affected parents or children
3. Refresh every affected Child DOX Index
4. Remove stale or contradictory text
5. Run existing verification when relevant
6. Report any docs intentionally left unchanged and why

---

# SDD project rail (root-owned)

Portable Spec-Driven Development harness. No machine-specific paths, model names, or provider credentials.

## Core Principle

**The agent's primary output is not code — it is the system that produces code.**

```
Spec → Success Criteria → Build → Verify → Eval → Reflect
```

Give agents **success criteria**, not step-by-step instructions — then let them iterate.

## Context Architecture

- **Static:** this file (DOX + rail), CLAUDE.md, system instructions
- **Dynamic:** child AGENTS.md on the edit path, task docs, tool results

Move as much context as possible to dynamic. DOX children are the designed local-rules layer.

## Agent = Model + Harness

Debug the harness before blaming the model: instructions (DOX chain), knowledge, tools, guardrails, orchestration, observability.

## Engineering Standards

1. **Spec first.** `PRD.md` defines what and why.
2. **Success criteria first.** AC **predate** code. Tests are evidence, not the definition of correct.
3. **Fail fast, fail loud.** Never swallow exceptions.
4. **Smallest change wins.** Surgical diffs.
5. **One function, one responsibility.**
6. **No bare `except:`.**
7. **Dependencies need approval.** Prefer stdlib.
8. **PIV-Loop.** Plan → Implement → Validate; validator ≠ builder (artifacts only).
9. **Never erase changelog history.** Append only.
10. **Credentials never in code or CLI.** Env-var names only.
11. **Type hints on public functions** (when the language supports them).
12. **Follow repo conventions** (`pathlib.Path` in Python projects).
13. **Claims need evidence.** Recorded command + exit code.
14. **Harness ownership.** DOX maintenance (children, indexes, local contracts) is mandatory. Rewrites of Engineering Standards / Verification Gate / Core Principle need human YES.
15. **External product claims** cite `kb/SOURCES.md` when present.
16. **DOX before and after edits.** No blind edits; closeout pass required.

## Verification Gate

- [ ] DOX chain read for every touched path
- [ ] AC defined before implementation
- [ ] Mechanical gates pass (`./scripts/sdd-validate .`) with recorded results
- [ ] AC mapped to VERIFIED/REASONED evidence
- [ ] Validator ≠ implementer when isolation available
- [ ] CHANGELOG.md + TASKS.md updated
- [ ] DOX closeout done (or explicitly skipped with reason)
- [ ] Residual risk noted if shipping

## Evaluation Standards

1. Verify against criteria (commands + AC map)
2. Eval output + trajectory (includes DOX)
3. Human ship approval = accept residual risk
4. Reflect one sentence

## Slice Discipline

One vertical slice at a time; verify; report; do not batch unless asked.

## Project-specific (fill me)

<!-- Agents: do not delete this heading. -->

| Item | Value |
|---|---|
| Domain | azure-triage-agent |
| Primary stack / validate commands | |
| Product skills (in-repo) | `skills/` if present |
| Extra CRITICAL risks | |
| Official sources index | `kb/SOURCES.md` if used |

## User Preferences

When the user requests a durable behavior change, record it here or in the relevant child AGENTS.md.

## Child DOX Index

| Path | Owns |
|---|---|
| `docs/AGENTS.md` | Docs, plans, issues, validation, handoff |
| `kb/AGENTS.md` | Official-doc grounding corpus |
| `scripts/AGENTS.md` | Local automation / validate |
| `src/AGENTS.md` | Implementation |
| `tests/AGENTS.md` | Automated tests |
| `skills/AGENTS.md` | In-repo product/domain skills |

Root-owned: `PRD.md`, `TASKS.md`, `CHANGELOG.md`, `PLANNING.md`, `INFRASTRUCTURE.md`, `README.md`, `CLAUDE.md`, root `AGENTS.md`.

New durable folder? Copy `docs/DOX-CHILD-TEMPLATE.md` → `<dir>/AGENTS.md`, fill sections, add to this index.
