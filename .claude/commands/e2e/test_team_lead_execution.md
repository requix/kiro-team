# E2E Test: Team Lead Execution

Tests that the team-lead agent can delegate work to sub-agents and produce artifacts.

## Timeout

10 minutes

## User Story

As a developer, I want the team-lead agent to orchestrate work by delegating to builder and validator agents so that complex tasks are handled by specialized agents.

## Test Steps

1. **Setup: Create clean test directory**
   - Create a temporary test directory: `mkdir -p /tmp/kiro_test_team_lead`
   - Copy `.kiro/` directory to the test directory: `cp -r .kiro /tmp/kiro_test_team_lead/`
   - Change to test directory: `cd /tmp/kiro_test_team_lead`

2. **Execute team-lead agent**
   - Run: `kiro-cli chat "Create a simple Python script called greet.py that prints 'Hello, Team!' when run" --agent team-lead --no-interactive --trust-all-tools --wrap never 2>&1 | tee /tmp/kiro_test_team_lead_output.txt`
   - **Verify**: kiro-cli exits with code 0

3. **Validate artifact creation**
   - Check that the requested file was created on disk
   - Run: `test -f greet.py && echo "File created" || echo "File missing"`
   - **Verify**: `greet.py` file exists

4. **Validate artifact content**
   - Read the created file
   - **Verify**: File contains Python code and is non-empty

5. **Generate Evidence**
   - Create evidence directory at `<codebase>/agents/<adw_id>/<agent_name>/logs/team_lead_execution/`
   - Write an `evidence.md` file containing:
     - **Header**: Test name (`team_lead_execution`), timestamp, agent name, kiro-cli exit code, duration, pass/fail
     - **Artifacts Created**: List of files created (e.g., `greet.py`) with sizes
     - **Key File Snippets**: First 30 lines of created artifacts
     - **kiro-cli Output**: Last 50 lines of `/tmp/kiro_test_team_lead_output.txt`
   - Include the evidence file path (relative to codebase) in the `screenshots` field

6. **Cleanup**
   - Remove test directory: `rm -rf /tmp/kiro_test_team_lead`

## Success Criteria

- kiro-cli executes with team-lead agent without errors (exit code 0)
- The requested artifact (greet.py) is created on disk
- The artifact contains valid content

## Output Format

```json
{
  "test_name": "team_lead_execution",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/team_lead_execution/evidence.md"],
  "error": null
}
```
