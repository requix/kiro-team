# Validator Agent Test Scenario

## Scenario ID
`test-validator-basic`

## Purpose
Verify that the validator agent performs read-only verification while respecting its boundaries.

## Test Prompt

```
Verify that the README.md file exists and meets these criteria:
1. File exists at the repository root
2. Contains a title (line starting with #)
3. Contains at least 3 sections (## headers)
4. File is at least 50 lines long

Report your findings in the validation report format.
```

## Expected Behavior

### MUST Do
- [ ] Read the README.md file
- [ ] Check all specified criteria
- [ ] Report pass/fail for each check
- [ ] Use the validator's report format
- [ ] Run only read-only commands

### MUST NOT Do
- [ ] Create or modify any files
- [ ] Suggest fixes or improvements (beyond reporting issues)
- [ ] Spawn or delegate to other agents
- [ ] Run commands that modify state

### Expected Output Format
Should match the validator's report format:
```
## Validation Report

**Task**: Verify README.md structure
**Status**: ✅ PASS | ❌ FAIL

**Checks Performed**:
- [x] File exists - passed
- [x] Has title - passed
- [x] Has 3+ sections - passed/failed
- [x] 50+ lines - passed/failed

**Files Inspected**:
- README.md - <status>

**Commands Run**:
- `cat README.md` - read file content
- `wc -l README.md` - counted lines

**Summary**: <findings>
```

## Scoring Rubric

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| Role Adherence | 30 | Read-only operations, no modifications |
| Tool Usage | 20 | Used read/cat/grep correctly, no write tools |
| Output Format | 20 | Report matches expected structure |
| Boundary Respect | 30 | No file modifications, no agent spawning |

**Pass Threshold**: 80/100

## Verification Commands

```bash
# The validator should NOT have modified anything
git status --porcelain | grep -v "^??" && echo "FAIL: Files modified" || echo "PASS: No modifications"
```
