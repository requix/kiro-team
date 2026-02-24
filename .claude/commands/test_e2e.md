# E2E Test Runner

Execute end-to-end (E2E) tests using kiro-cli agent invocations. If any errors occur and assertions fail mark the test as failed and explain exactly what went wrong.

## Variables

adw_id: $ARGUMENT if provided, otherwise generate a random 8 character hex string
agent_name: $ARGUMENT if provided, otherwise use 'test_e2e'
e2e_test_file: $ARGUMENT

## Instructions

- Read the `e2e_test_file`
- Digest the `User Story` to first understand what we're validating
- IMPORTANT: Execute the `Test Steps` detailed in the `e2e_test_file` using kiro-cli commands
- Review the `Success Criteria` and if any of them fail, mark the test as failed and explain exactly what went wrong
- Review the steps that say '**Verify**...' and if they fail, mark the test as failed and explain exactly what went wrong
- Capture output logs as specified
- IMPORTANT: Return results in the format requested by the `Output Format`
- Execute kiro-cli commands with: `kiro-cli chat "..." --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_output.txt`
- Validate primarily via **artifact existence** (files created on disk) rather than parsing unstructured text output
- Check kiro-cli exit code (0 = success)
- Allow time for async operations (some agent tasks may take several minutes)
- If you encounter an error, mark the test as failed immediately and explain exactly what went wrong and on what step it occurred. For example: '(Step 1 ❌) kiro-cli exited with code 1: agent "builder" not found'
- Use `pwd` or equivalent to get the absolute path to the codebase for writing and displaying the correct paths to log files

## Setup

Read and Execute `.claude/commands/prepare_app.md` now to prepare the agent environment for the test.

## Log Directory

<absolute path to codebase>/agents/<adw_id>/<agent_name>/logs/<directory name based on test file name>/*.log

Each log file should be saved with a descriptive name that reflects what is being captured. The directory structure ensures that:
- Logs are organized by ADW ID (workflow run)
- They are stored under the specified agent name (e.g., e2e_test_runner_0, e2e_test_resolver_iter1_0)
- Each test has its own subdirectory based on the test file name (e.g., test_builder_agent → builder_agent/)

## Evidence Generation

After all test steps complete (pass or fail), generate a composite evidence file:

1. **Collect evidence data:**
   - `exit_code`: The kiro-cli exit code from the test run (0 = success)
   - `duration`: Wall-clock seconds the test took
   - `output_log_path`: Path to the captured kiro-cli output log (e.g., `/tmp/kiro_test_output.txt`)
   - `artifacts`: List of files created during the test (relative to the test working directory)
   - `working_dir`: The test working directory (absolute path)

2. **Create the evidence directory:**
   - `<absolute path to codebase>/agents/<adw_id>/<agent_name>/logs/<directory name based on test file name>/`

3. **Write the evidence markdown file** to `<evidence_directory>/evidence.md` with these sections:
   - **Header**: Test name, timestamp, agent name, exit code, duration, pass/fail status
   - **Artifacts Created**: Tree listing of all files created during the test with file sizes
   - **Key File Snippets**: First 30 lines of each artifact file (fenced code blocks with language hints)
   - **kiro-cli Output**: Last 50 lines of the kiro-cli output log

4. **Include the evidence file path** in the `screenshots` field of the output JSON (this reuses the existing field so the R2 upload pipeline picks it up automatically)

## Report

- Exclusively return the JSON output as specified in the test file
- Capture any unexpected errors
- IMPORTANT: Ensure all log files are saved in the `Log Directory`
- IMPORTANT: Include the evidence file path in the `screenshots` array

### Output Format

```json
{
  "test_name": "Test Name Here",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/<test_dir>/evidence.md"],
  "error": null
}
```
