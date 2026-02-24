# Resolve Failed E2E Test

Fix a specific failing E2E test using the provided failure details.

## Instructions

1. **Analyze the E2E Test Failure**
   - Review the JSON data in the `Test Failure Input`, paying attention to:
     - `test_name`: The name of the failing test
     - `test_path`: The path to the test file (you will need this for re-execution)
     - `error`: The specific error that occurred
   - Understand what the test is trying to validate from an agent interaction perspective

2. **Understand Test Execution**
   - Read `.claude/commands/test_e2e.md` to understand how E2E tests are executed
   - Read the test file specified in the `test_path` field from the JSON
   - Note the test steps, user story, and success criteria

3. **Reproduce the Failure**
   - IMPORTANT: Use the `test_path` from the JSON to re-execute the specific E2E test
   - Follow the execution pattern from `.claude/commands/test_e2e.md`
   - Observe the kiro-cli output and confirm you can reproduce the exact failure
   - Compare the error you see with the error reported in the JSON

4. **Fix the Issue**
   - Based on your reproduction, identify the root cause
   - Make minimal, targeted changes to resolve only this E2E test failure
   - Consider common kiro-agent failure modes:
     - Agent config syntax errors (malformed JSON)
     - Missing or incorrect prompt file references
     - kiro-cli timeout or authentication failures
     - Agent not producing expected output artifacts on disk
     - Agent delegation failures (team-lead failing to invoke sub-agents)
     - Incorrect agent tool permissions
   - Ensure the fix aligns with the user story and test purpose

5. **Validate the Fix**
   - Re-run the same E2E test step by step using the `test_path` to confirm it now passes
   - IMPORTANT: The test must complete successfully before considering it resolved
   - Do NOT run other tests or the full test suite
   - Focus only on fixing this specific E2E test

## Test Failure Input

$ARGUMENTS

## Report

Provide a concise summary of:
- Root cause identified (e.g., malformed agent config, missing prompt file, kiro-cli auth failure)
- Specific fix applied
- Confirmation that the E2E test now passes after your fix
