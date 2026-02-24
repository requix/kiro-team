# E2E Test: Validator Agent

Tests that the validator agent can inspect files and report findings.

## Timeout

5 minutes

## User Story

As a developer, I want the validator agent to review code files and report any issues so that code quality is checked by a specialized agent.

## Test Steps

1. **Setup: Create clean test directory with a file to validate**
   - Create a temporary test directory: `mkdir -p /tmp/kiro_test_validator`
   - Copy `.kiro/` directory to the test directory: `cp -r .kiro /tmp/kiro_test_validator/`
   - Create a sample Python file with an intentional issue:
     ```bash
     cat > /tmp/kiro_test_validator/sample.py << 'PYEOF'
     def add(a, b):
         return a + b

     def divide(a, b):
         return a / b

     result = add(1, 2)
     print(result)
     PYEOF
     ```
   - Change to test directory: `cd /tmp/kiro_test_validator`

2. **Execute validator agent**
   - Run: `kiro-cli chat "Review the file sample.py and report any issues or suggestions. Write your findings to a file called validation_report.md" --agent validator --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_validator_output.txt`
   - **Verify**: kiro-cli exits with code 0

3. **Validate output**
   - Check kiro-cli exit code is 0
   - Check that the validation report or output was produced
   - **Verify**: kiro-cli completed without crashing

4. **Generate Evidence**
   - Create evidence directory at `<codebase>/agents/<adw_id>/<agent_name>/logs/validator_agent/`
   - Write an `evidence.md` file containing:
     - **Header**: Test name (`validator_agent`), timestamp, agent name, kiro-cli exit code, duration, pass/fail
     - **Artifacts Created**: List of files created (e.g., `validation_report.md`, `sample.py`) with sizes
     - **Key File Snippets**: First 30 lines of any created report files
     - **kiro-cli Output**: Last 50 lines of `/tmp/kiro_test_validator_output.txt`
   - Include the evidence file path (relative to codebase) in the `screenshots` field

5. **Cleanup**
   - Remove test directory: `rm -rf /tmp/kiro_test_validator`

## Success Criteria

- kiro-cli executes with validator agent without errors (exit code 0)
- Agent produces output (either a report file or console output)
- Agent does not crash or timeout

## Output Format

```json
{
  "test_name": "validator_agent",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/validator_agent/evidence.md"],
  "error": null
}
```
