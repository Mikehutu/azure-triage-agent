# TASKS — azure-triage-agent

Maintained with the R-PIV loop. One module at a time. Check off complete items. **Never erase old entries** — append new ones.

## Phase N — <Phase Name>

### Module: `module-name`

#### Plan (Agent: <primary>)
- [ ] Define interface `IModuleName`
- [ ] Define types and error variants
- [ ] Write unit test skeletons (RED)

#### Implement (Agent: <primary>)
- [ ] Implement method 1
- [ ] Implement method 2

#### Validate (Agent: <VALIDATOR — MUST BE DIFFERENT FROM BUILD>)
- [ ] Run unit tests: `pytest tests/test_<module>.py -v`
- [ ] Run lint: `ruff check src/<module>/`
- [ ] Verify edge cases against interface contract

**Module Checkpoint:**
- [ ] All tests pass
- [ ] Complexity limits respected
- [ ] Cross-agent validation passed

---

## Done

### Phase N — <Phase Name>
- [x] Module 1: <summary>
- [x] Module 2: <summary>
