# E2E Test: Full Workflow

Tests the complete plan -> execute -> validate cycle using kiro agents.

## Timeout

15 minutes

## User Story

As a developer, I want the full kiro agent workflow to work end-to-end: plan a feature, build it, then validate it, so that I can trust the multi-agent system to handle complete tasks.

## Test Steps

1. **Setup: Create clean test directory**
   - Create a temporary test directory: `mkdir -p /tmp/kiro_test_full_workflow`
   - Copy `.kiro/` directory to the test directory: `cp -r .kiro /tmp/kiro_test_full_workflow/`
   - Create specs directory: `mkdir -p /tmp/kiro_test_full_workflow/specs`
   - Change to test directory: `cd /tmp/kiro_test_full_workflow`

2. **Step 1: Plan - Create a spec**
   - Run: `kiro-cli chat "Create a plan for building a simple todo list module in Python. The module should have functions to add, remove, and list todos. Save the plan as specs/todo-module.md" --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_full_workflow_plan.txt`
   - **Verify**: kiro-cli exits with code 0
   - **Verify**: A spec file exists in `specs/` directory

3. **Step 2: Build - Implement the spec**
   - Run: `kiro-cli chat "Read the spec in specs/ and implement the todo list module as described. Create the file todo.py" --agent builder --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_full_workflow_build.txt`
   - **Verify**: kiro-cli exits with code 0
   - **Verify**: `todo.py` file is created on disk

4. **Step 3: Validate - Review the implementation**
   - Run: `kiro-cli chat "Review todo.py and verify it implements the todo list functionality correctly. Write your findings to validation_report.md" --agent validator --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_full_workflow_validate.txt`
   - **Verify**: kiro-cli exits with code 0

5. **Validate all artifacts exist**
   - Check: `specs/` directory has at least one `.md` file
   - Check: `todo.py` exists and is non-empty
   - **Verify**: All expected artifacts are present

6. **Generate Evidence**
   - Create evidence directory at `<codebase>/agents/<adw_id>/<agent_name>/logs/full_workflow/`
   - Write an `evidence.md` file containing:
     - **Header**: Test name (`full_workflow`), timestamp, agent name, overall pass/fail status
     - **Artifacts Created**: List of all files created across all phases (spec files, `todo.py`, report files) with sizes
     - **Key File Snippets**: First 30 lines of the spec file and `todo.py`
     - **kiro-cli Output**: Last 50 lines of the final phase output (`/tmp/kiro_test_full_workflow_validate.txt`)
     - **Phase Results**: Summary of each phase (plan/build/validate) with exit codes
   - Include the evidence file path (relative to codebase) in the `screenshots` field

7. **Cleanup**
   - Remove test directory: `rm -rf /tmp/kiro_test_full_workflow`

## Success Criteria

- All three phases (plan, build, validate) complete with exit code 0
- Spec file is created in `specs/` directory
- Implementation file (`todo.py`) is created on disk
- Validator agent runs without errors

## Output Format

```json
{
  "test_name": "full_workflow",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/full_workflow/evidence.md"],
  "error": null
}
```
