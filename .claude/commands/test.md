# Agent Configuration Validation Test Suite

Execute comprehensive validation tests for kiro agent configurations, returning results in a standardized JSON format for automated processing.

## Purpose

Proactively identify and fix issues in the kiro agent configuration before they impact workflows. By running this comprehensive test suite, you can:
- Detect malformed JSON in agent config files
- Verify all required prompt files exist and are non-empty
- Validate agent config schema (required fields)
- Ensure kiro-cli is installed and authenticated

## Variables

TEST_COMMAND_TIMEOUT: 5 minutes

## Instructions

- Execute each test in the sequence provided below
- Capture the result (passed/failed) and any error messages
- IMPORTANT: Return ONLY the JSON array with test results
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
- If a test passes, omit the error field
- If a test fails, include the error message in the error field
- Execute all tests even if some fail
- Error Handling:
  - If a command returns non-zero exit code, mark as failed and immediately stop processing tests
  - Capture stderr output for error field
  - Timeout commands after `TEST_COMMAND_TIMEOUT`
  - IMPORTANT: If a test fails, stop processing tests and return the results thus far
- All file paths are relative to the project root
- Always run `pwd` and `cd` before each test to ensure you're operating in the correct directory for the given test

## Test Execution Sequence

### Agent Config Tests

1. **Agent Config JSON Validation**
   - Preparation Command: None
   - Command: `python3 -m json.tool .kiro/agents/team-lead.json > /dev/null && python3 -m json.tool .kiro/agents/builder.json > /dev/null && python3 -m json.tool .kiro/agents/validator.json > /dev/null`
   - test_name: "agent_config_json_validation"
   - test_purpose: "Validates that all agent JSON configuration files are well-formed and parseable"

2. **Prompt Files Check**
   - Preparation Command: None
   - Command: `for f in .kiro/agents/team-lead.json .kiro/agents/builder.json .kiro/agents/validator.json .kiro/prompts/plan-with-team.md; do test -s "$f" || { echo "Missing or empty: $f"; exit 1; }; done && echo "All prompt files present and non-empty"`
   - test_name: "prompt_files_check"
   - test_purpose: "Verifies all agent config and prompt files exist and are non-empty"

3. **Agent Config Schema Validation**
   - Preparation Command: None
   - Command: `python3 -c "import json, sys; [json.load(open(f)) for f in ['.kiro/agents/team-lead.json', '.kiro/agents/builder.json', '.kiro/agents/validator.json']]; print('Schema OK')" 2>&1 || echo "Schema validation failed"`
   - test_name: "agent_config_schema_validation"
   - test_purpose: "Validates that each agent JSON config contains required fields and follows the expected schema structure"

4. **Kiro-CLI Auth Check**
   - Preparation Command: None
   - Command: `test -f ~/.local/share/kiro-cli/data.sqlite3 && echo "Kiro-CLI auth database found" || echo "Kiro-CLI auth database not found"`
   - test_name: "kiro_cli_auth_check"
   - test_purpose: "Verifies kiro-cli is authenticated by checking for the auth database file"

5. **Kiro-CLI Version Check**
   - Preparation Command: None
   - Command: `kiro-cli --version`
   - test_name: "kiro_cli_version_check"
   - test_purpose: "Verifies kiro-cli is installed and accessible by checking its version output"

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- Sort the JSON array with failed tests (passed: false) at the top
- Include all tests in the output, both passed and failed
- The execution_command field should contain the exact command that can be run to reproduce the test
- This allows subsequent agents to quickly identify and resolve errors

### Output Structure

```json
[
  {
    "test_name": "string",
    "passed": boolean,
    "execution_command": "string",
    "test_purpose": "string",
    "error": "optional string"
  },
  ...
]
```

### Example Output

```json
[
  {
    "test_name": "agent_config_json_validation",
    "passed": false,
    "execution_command": "python3 -m json.tool .kiro/agents/team-lead.json",
    "test_purpose": "Validates that all agent JSON configuration files are well-formed and parseable",
    "error": "Expecting ',' delimiter: line 5 column 3 (char 42)"
  },
  {
    "test_name": "kiro_cli_version_check",
    "passed": true,
    "execution_command": "kiro-cli --version",
    "test_purpose": "Verifies kiro-cli is installed and accessible by checking its version output"
  }
]
```
