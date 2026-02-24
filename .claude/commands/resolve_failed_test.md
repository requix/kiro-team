# Resolve Failed Test

Fix a specific failing test using the provided failure details.

## Instructions

1. **Analyze the Test Failure**
   - Review the test name, purpose, and error message from the `Test Failure Input`
   - Understand what the test is trying to validate
   - Identify the root cause from the error details

2. **Context Discovery**
   - Check recent changes: `git diff origin/main --stat --name-only`
   - If a relevant spec exists in `specs/*.md`, read it to understand requirements
   - Focus on `.kiro/agents/` and `.kiro/prompts/` for agent config issues
   - Check kiro-cli availability and authentication status if relevant

3. **Reproduce the Failure**
   - IMPORTANT: Use the `execution_command` provided in the test data
   - Run it to see the full error output
   - Confirm you can reproduce the exact failure

4. **Fix the Issue**
   - Make minimal, targeted changes to resolve only this test failure
   - Ensure the fix aligns with the test purpose and any spec requirements
   - Do not modify unrelated code or tests

5. **Validate the Fix**
   - Re-run the same `execution_command` to confirm the test now passes
   - Do NOT run other tests or the full test suite
   - Focus only on fixing this specific test

## Test Failure Input

$ARGUMENTS

## Report

Provide a concise summary of:
- Root cause identified
- Specific fix applied
- Confirmation that the test now passes
