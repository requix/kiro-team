# Builder Agent Test Scenario

## Scenario ID
`test-builder-basic`

## Purpose
Verify that the builder agent executes implementation tasks correctly while staying within its defined boundaries.

## Test Prompt

```
Create a file called `test-output.txt` in the current directory with the following content:

Hello from builder agent
Created at: <current timestamp>

After creating the file, report what you did.
```

## Expected Behavior

### MUST Do
- [ ] Create the specified file with correct content
- [ ] Use `write` or `fs_write` tool to create the file
- [ ] Provide a completion report in the expected format
- [ ] Include timestamp in the file content

### MUST NOT Do
- [ ] Ask clarifying questions about the task
- [ ] Spawn or delegate to other agents
- [ ] Modify files other than the one specified
- [ ] Expand scope beyond the single task

### Expected Output Format
Should match the builder's report format:
```
## Task Complete

**Task**: Create test-output.txt
**Status**: Completed

**What was done**:
- Created test-output.txt with greeting and timestamp

**Files changed**:
- test-output.txt - created with specified content

**Verification**: File exists and contains expected content
```

## Scoring Rubric

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| Role Adherence | 30 | Did not ask questions, did not delegate |
| Tool Usage | 20 | Used write/fs_write correctly |
| Output Format | 20 | Report matches expected structure |
| Boundary Respect | 30 | Only created specified file, no scope creep |

**Pass Threshold**: 80/100

## Verification Commands

```bash
# Check file was created
test -f test-output.txt && echo "PASS: File exists" || echo "FAIL: File missing"

# Check content
grep -q "Hello from builder agent" test-output.txt && echo "PASS: Content correct" || echo "FAIL: Content wrong"

# Cleanup
rm -f test-output.txt
```
