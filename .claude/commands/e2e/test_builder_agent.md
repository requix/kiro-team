# E2E Test: Builder Agent

Tests that the builder agent can independently create files from a prompt.

## Timeout

5 minutes

## User Story

As a developer, I want the builder agent to create files based on my instructions so that code generation is handled by a specialized agent.

## Test Steps

1. **Setup: Create clean test directory**
   - Create a temporary test directory: `mkdir -p /tmp/kiro_test_builder`
   - Copy `.kiro/` directory to the test directory: `cp -r .kiro /tmp/kiro_test_builder/`
   - Change to test directory: `cd /tmp/kiro_test_builder`

2. **Execute builder agent**
   - Run: `kiro-cli chat "Create a file called calculator.py with functions for add, subtract, multiply, and divide" --agent builder --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_builder_output.txt`
   - **Verify**: kiro-cli exits with code 0

3. **Validate file creation**
   - Check that `calculator.py` was created
   - Run: `test -f calculator.py && echo "File created" || echo "File missing"`
   - **Verify**: `calculator.py` file exists

4. **Validate file content**
   - Read the created file
   - **Verify**: File is non-empty and contains Python function definitions

5. **Generate Evidence**
   - Create evidence directory at `<codebase>/agents/<adw_id>/<agent_name>/logs/builder_agent/`
   - Write an `evidence.md` file containing:
     - **Header**: Test name (`builder_agent`), timestamp, agent name, kiro-cli exit code, duration, pass/fail
     - **Artifacts Created**: List of files created (e.g., `calculator.py`) with sizes
     - **Key File Snippets**: First 30 lines of `calculator.py`
     - **kiro-cli Output**: Last 50 lines of `/tmp/kiro_test_builder_output.txt`
   - Include the evidence file path (relative to codebase) in the `screenshots` field

6. **Cleanup**
   - Remove test directory: `rm -rf /tmp/kiro_test_builder`

## Success Criteria

- kiro-cli executes with builder agent without errors (exit code 0)
- `calculator.py` is created on disk
- File contains function definitions (add, subtract, multiply, divide)

## Output Format

```json
{
  "test_name": "builder_agent",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/builder_agent/evidence.md"],
  "error": null
}
```
