# E2E Test: Plan Creation

Tests that the `@plan-with-team` prompt produces a specification file in the `specs/` directory.

## Timeout

10 minutes

## User Story

As a developer, I want to use the plan-with-team prompt to generate a specification file so that I can plan work before implementing it.

## Test Steps

1. **Setup: Create clean test directory**
   - Create a temporary test directory: `mkdir -p /tmp/kiro_test_plan_creation`
   - Copy `.kiro/` directory to the test directory: `cp -r .kiro /tmp/kiro_test_plan_creation/`
   - Create specs directory: `mkdir -p /tmp/kiro_test_plan_creation/specs`
   - Change to test directory: `cd /tmp/kiro_test_plan_creation`

2. **Execute plan creation**
   - Run: `kiro-cli chat "Create a plan for adding a hello world function to a new file called hello.py. Save the plan as specs/hello-world.md" --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_plan_output.txt`
   - **Verify**: kiro-cli exits with code 0

3. **Validate plan artifact**
   - Check that a `.md` file was created in `specs/` directory
   - Run: `ls specs/*.md`
   - **Verify**: At least one markdown file exists in `specs/`

4. **Validate plan content**
   - Read the created plan file
   - **Verify**: File is non-empty and contains text content

5. **Generate Evidence**
   - Create evidence directory at `<codebase>/agents/<adw_id>/<agent_name>/logs/plan_creation/`
   - Write an `evidence.md` file containing:
     - **Header**: Test name (`plan_creation`), timestamp, agent name, kiro-cli exit code, duration, pass/fail
     - **Artifacts Created**: List of files created (spec files in `specs/`) with sizes
     - **Key File Snippets**: First 30 lines of the created spec file
     - **kiro-cli Output**: Last 50 lines of `/tmp/kiro_test_plan_output.txt`
   - Include the evidence file path (relative to codebase) in the `screenshots` field

6. **Cleanup**
   - Remove test directory: `rm -rf /tmp/kiro_test_plan_creation`

## Success Criteria

- kiro-cli executes without errors (exit code 0)
- A specification file is created in `specs/` directory
- The specification file is non-empty and contains plan content

## Output Format

```json
{
  "test_name": "plan_creation",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/plan_creation/evidence.md"],
  "error": null
}
```
