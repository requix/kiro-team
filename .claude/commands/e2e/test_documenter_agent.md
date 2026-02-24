# E2E Test: Documenter Agent

Tests that the documenter agent reads existing source files and produces a `docs/` markdown file.

## Timeout

5 minutes

## User Story

As a developer, I want the documenter agent to read implemented files and generate a `docs/<feature>.md` documentation file so that every completed feature has accurate, code-grounded documentation.

## Test Steps

1. **Setup: Create clean test directory**
   - Create a temporary test directory: `mkdir -p /tmp/kiro_test_documenter`
   - Copy `.kiro/` directory to the test directory: `cp -r .kiro /tmp/kiro_test_documenter/`
   - Create a sample source file to document: write `/tmp/kiro_test_documenter/calculator.py` with a few functions (add, subtract, multiply, divide)
   - Change to test directory: `cd /tmp/kiro_test_documenter`

2. **Execute documenter agent**
   - Run: `kiro-cli chat "Document the calculator feature. The feature name is 'calculator'. The following files were changed: calculator.py. Please read the file and write docs/calculator.md" --agent documenter --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_documenter_output.txt`
   - **Verify**: kiro-cli exits with code 0

3. **Validate docs file creation**
   - Check that `docs/calculator.md` was created
   - Run: `test -f docs/calculator.md && echo "Docs file created" || echo "Docs file missing"`
   - **Verify**: `docs/calculator.md` file exists

4. **Validate docs file content**
   - Read the created file
   - **Verify**: File is non-empty and contains markdown content (headings, descriptions)

5. **Generate Evidence**
   - Create evidence directory at `<codebase>/agents/<adw_id>/<agent_name>/logs/documenter_agent/`
   - Write an `evidence.md` file containing:
     - **Header**: Test name (`documenter_agent`), timestamp, agent name, kiro-cli exit code, duration, pass/fail
     - **Artifacts Created**: List of files created (e.g., `docs/calculator.md`) with sizes
     - **Key File Snippets**: First 30 lines of `docs/calculator.md`
     - **kiro-cli Output**: Last 50 lines of `/tmp/kiro_test_documenter_output.txt`
   - Include the evidence file path (relative to codebase) in the `screenshots` field

6. **Cleanup**
   - Remove test directory: `rm -rf /tmp/kiro_test_documenter`

## Success Criteria

- kiro-cli executes with documenter agent without errors (exit code 0)
- `docs/calculator.md` is created on disk
- File is non-empty and contains markdown content

## Output Format

```json
{
  "test_name": "documenter_agent",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/documenter_agent/evidence.md"],
  "error": null
}
```
