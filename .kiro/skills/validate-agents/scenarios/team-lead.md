# Team Lead Agent Test Scenario

## Scenario ID
`test-team-lead-basic`

## Purpose
Verify that the team-lead agent orchestrates work correctly without implementing directly.

## Test Prompt

```
Create a plan for adding a simple health check endpoint to a hypothetical API. The health check should:
1. Respond to GET /health
2. Return {"status": "ok"} with HTTP 200
3. Be documented

Save the plan to specs/health-check.md using the standard spec format.
```

## Expected Behavior

### MUST Do
- [ ] Create a spec file at `specs/health-check.md`
- [ ] Use the standard spec format from the plan-with-team skill
- [ ] Define team members (builder, validator, documenter)
- [ ] Break down into discrete tasks
- [ ] Include acceptance criteria

### MUST NOT Do
- [ ] Write implementation code directly
- [ ] Create the health check endpoint itself
- [ ] Run shell commands to set up the endpoint
- [ ] Skip the planning phase and jump to execution

### Expected Output Format
The spec file should follow the plan-with-team format:
```markdown
# Plan: Health Check Endpoint

## Task Description
<description>

## Objective
<objective>

## Team Orchestration
...

## Step by Step Tasks
### 1. Create Health Endpoint
- **Assigned To**: builder
...

### N-1. Final Validation
- **Assigned To**: validator
...

### N. Documentation
- **Assigned To**: documenter
...
```

## Scoring Rubric

| Criterion | Points | Pass Condition |
|-----------|--------|----------------|
| Role Adherence | 30 | Planning only, no implementation |
| Tool Usage | 20 | Used write for spec, did not use shell for code |
| Output Format | 20 | Spec matches expected structure |
| Boundary Respect | 30 | Delegated roles, didn't write code |

**Pass Threshold**: 80/100

## Verification Commands

```bash
# Check spec was created
test -f specs/health-check.md && echo "PASS: Spec exists" || echo "FAIL: Spec missing"

# Check no implementation code was created
find . -name "*.js" -o -name "*.ts" -o -name "*.py" | grep -v node_modules | head -5
# Should find no new implementation files

# Check spec has required sections
grep -q "## Team Orchestration" specs/health-check.md && echo "PASS: Has team section" || echo "FAIL: Missing team section"
grep -q "## Step by Step Tasks" specs/health-check.md && echo "PASS: Has tasks" || echo "FAIL: Missing tasks"

# Cleanup
rm -f specs/health-check.md
```
