# E2E Test: Agent Error Handling

Tests that kiro agents handle invalid inputs gracefully without crashing.

## Timeout

3 minutes

## User Story

As a developer, I want kiro agents to handle edge cases and invalid inputs gracefully so that the system doesn't crash unexpectedly.

## Test Steps

1. **Setup: Create clean test directory**
   - Create a temporary test directory: `mkdir -p /tmp/kiro_test_error_handling`
   - Copy `.kiro/` directory to the test directory: `cp -r .kiro /tmp/kiro_test_error_handling/`
   - Change to test directory: `cd /tmp/kiro_test_error_handling`

2. **Test: Empty prompt handling**
   - Run: `kiro-cli chat "" --agent builder --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_error_empty.txt`
   - **Verify**: kiro-cli does not crash (may exit non-zero, but should not segfault or hang indefinitely)
   - Note: A non-zero exit code is acceptable here - we're testing that it handles the edge case without crashing

3. **Test: Non-existent agent reference**
   - Run: `kiro-cli chat "hello" --agent nonexistent_agent_12345 --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_error_bad_agent.txt`
   - **Verify**: kiro-cli produces a clear error message about the agent not being found
   - **Verify**: kiro-cli does not hang or crash silently

4. **Test: Valid agent with a simple task completes**
   - Run: `kiro-cli chat "Say hello" --agent builder --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_error_simple.txt`
   - **Verify**: kiro-cli exits with code 0

5. **Generate Evidence**
   - Create evidence directory at `<codebase>/agents/<adw_id>/<agent_name>/logs/agent_error_handling/`
   - Write an `evidence.md` file containing:
     - **Header**: Test name (`agent_error_handling`), timestamp, agent name, overall pass/fail status
     - **Artifacts Created**: List of any files created during the test with sizes
     - **Sub-test Results**: Summary of each error handling sub-test (empty prompt, bad agent, simple task) with exit codes and outcomes
     - **kiro-cli Output**: Last 50 lines of `/tmp/kiro_test_error_simple.txt` (the final sub-test)
   - Include the evidence file path (relative to codebase) in the `screenshots` field

6. **Cleanup**
   - Remove test directory: `rm -rf /tmp/kiro_test_error_handling`

## Success Criteria

- kiro-cli does not crash or hang on empty input
- kiro-cli produces a clear error for non-existent agents
- kiro-cli successfully handles a simple valid task
- No unhandled exceptions or segfaults

## Output Format

```json
{
  "test_name": "agent_error_handling",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/agent_error_handling/evidence.md"],
  "error": null
}
```
