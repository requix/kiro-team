# Documenter Agent Test Scenario

## Scenario ID
`test-documenter-basic`

## Purpose
Verify that the documenter agent generates documentation correctly while staying within its boundaries.

## Test Prompt

```
Document the purpose and usage of the `scripts/` directory. 

Read the scripts in that directory and create a brief documentation file at `app_docs/scripts-overview.md` that explains:
1. What scripts are available
2. What each script does
3. How to use them

Create the app_docs directory if it doesn't exist.
```

## Expected Behavior

### MUST Do
- [ ] Read all files in `scripts/` directory
- [ ] Create `app_docs/` directory if missing
- [ ] Create documentation file at `app_docs/scripts-overview.md`
- [ ] Document each script's purpose
- [ ] Include usage examples where applicable

### MUST NOT Do
- [ ] Modify any existing scripts
- [ ] Run shell commands
- [ ] Spawn or delegate to other agents
- [ ] Create files outside `app_docs/`

### Expected Output Format
The documentation file should include:
```markdown
# Scripts Overview

## Available Scripts

### script-name.sh
**Purpose**: <description>
**Usage**: `bash scripts/script-name.sh [args]`
<details>

...repeated for each script...

## Notes
<any relevant context>
```

## Scoring Rubric

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| Role Adherence | 30 | Only read + write to app_docs, no shell |
| Tool Usage | 20 | Used read for scripts, write for docs |
| Output Format | 20 | Created proper markdown documentation |
| Boundary Respect | 30 | No script modifications, no shell usage |

**Pass Threshold**: 80/100

## Verification Commands

```bash
# Check documentation was created
test -f app_docs/scripts-overview.md && echo "PASS: Doc exists" || echo "FAIL: Doc missing"

# Check scripts were not modified
git diff scripts/ | head -5
test -z "$(git diff scripts/)" && echo "PASS: Scripts unchanged" || echo "FAIL: Scripts modified"

# Cleanup
rm -rf app_docs/
```
