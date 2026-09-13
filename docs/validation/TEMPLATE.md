# Validation report — <slice or task id>

**Date:** <YYYY-MM-DD>  
**Validator:** <agent id / human — must differ from implementer when isolation is available>  
**Implementer context shared?** No (artifacts only) | Yes (note risk)

## Acceptance criteria (defined before code)

| ID | Criterion | Verdict | Evidence class | Notes |
|---|---|---|---|---|
| AC-1 | | PASS/FAIL | VERIFIED/REASONED/SUSPICION | |
| AC-2 | | | | |

## Mechanical gates

| Gate | Command | Exit | Summary |
|---|---|---|---|
| lint | | | |
| tests | | | |
| smoke | | skipped / ok | |

Run via: `sdd-validate` (records commands when available).

## Findings

| ID | Severity | Evidence | Decision | Description |
|---|---|---|---|---|
| F-1 | HIGH | VERIFIED | FAIL | |

Decision ∈ {FAIL block, targeted verification, note, drop} per `docs/evidence-and-approval.md` matrix.

## Falsification (if applicable)

- [ ] Removed/disabled feature path and re-ran tests — suite failed as expected | N/A

## Residual risk (for human)

- What remains unproven:
- Consequence if wrong:
- Reversibility:

## Overall

**PASS** | **FAIL**

Human approval (if shipping): name + date + "accept residual risk"
