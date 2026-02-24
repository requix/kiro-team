# E2E Test: Agent Config Validation

Validates that all kiro agent configuration files are valid JSON, exist on disk, and conform to the expected schema.

## Timeout

1 minute

## User Story

As a developer, I want to ensure all kiro agent configuration files are valid and complete so that kiro-cli can load and execute them without errors.

## Test Steps

1. **Verify `.kiro/agents/` directory exists**
   - Check that the directory `.kiro/agents/` is present
   - **Verify**: Directory exists and is not empty

2. **Validate team-lead agent config**
   - Run `python3 -m json.tool .kiro/agents/team-lead.json > /dev/null`
   - **Verify**: Command exits with code 0 (valid JSON)

3. **Validate builder agent config**
   - Run `python3 -m json.tool .kiro/agents/builder.json > /dev/null`
   - **Verify**: Command exits with code 0 (valid JSON)

4. **Validate validator agent config**
   - Run `python3 -m json.tool .kiro/agents/validator.json > /dev/null`
   - **Verify**: Command exits with code 0 (valid JSON)

5. **Check prompt files exist**
   - Verify `.kiro/prompts/plan-with-team.md` exists and is non-empty
   - **Verify**: File exists and has content (size > 0 bytes)

6. **Verify kiro-cli can list agents**
   - Run `ls -la .kiro/agents/*.json`
   - **Verify**: At least 3 agent config files are listed

## Generate Evidence

After all test steps complete (pass or fail), before reporting results:

1. Create the evidence directory at `<codebase>/agents/<adw_id>/<agent_name>/logs/agent_config_validation/`
2. Write an `evidence.md` file to that directory containing:
   - **Header**: Test name (`agent_config_validation`), timestamp, agent name, pass/fail status
   - **Artifacts Created**: List of agent config files found (`.kiro/agents/*.json`) and prompt files (`.kiro/prompts/*.md`) with file sizes
   - **Key File Snippets**: First 30 lines of each agent config JSON file
   - **Validation Results**: Which configs passed JSON validation and which failed
3. Include the evidence file path (relative to codebase) in the `screenshots` field of the output JSON

## Success Criteria

- All agent JSON files parse without errors
- All required prompt/markdown files exist and are non-empty
- `.kiro/agents/` directory contains at least 3 agent configs (team-lead, builder, validator)

## Output Format

```json
{
  "test_name": "agent_config_validation",
  "status": "passed|failed",
  "screenshots": ["agents/<adw_id>/<agent_name>/logs/agent_config_validation/evidence.md"],
  "error": null
}
```
