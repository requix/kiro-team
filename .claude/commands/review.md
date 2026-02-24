# Review

Follow the `Instructions` below to **review work done against a specification file** (specs/*.md) to ensure implemented features match requirements. Use the spec file to understand the requirements and then use the git diff to understand the changes made. If there are issues, report them if not then report success.

## Variables

adw_id: $ARGUMENT
spec_file: $ARGUMENT
agent_name: $ARGUMENT if provided, otherwise use 'review_agent'
review_image_dir: `<absolute path to codebase>/agents/<adw_id>/<agent_name>/review_img/`

## Instructions

- Check current git branch using `git branch` to understand context
- Run `git diff origin/main` to see all changes made in current branch. Continue even if there are no changes related to the spec file.
- Find the spec file by looking for specs/*.md files in the diff that match the current branch name
- Read the identified spec file to understand requirements
- Verify `.kiro/` directory exists and validate agent configs parse correctly
- Review the changes via `git diff` to verify they match the spec requirements:
  - Check agent config changes (`.kiro/agents/*.json`)
  - Check prompt file changes (`.kiro/prompts/*.md`)
  - Compare implemented changes with spec requirements to verify correctness
- IMPORTANT: Issue Severity Guidelines
  - Think hard about the impact of the issue on the feature and the user
  - Guidelines:
    - `skippable` - the issue is non-blocker for the work to be released but is still a problem
    - `tech_debt` - the issue is non-blocker for the work to be released but will create technical debt that should be addressed in the future
    - `blocker` - the issue is a blocker for the work to be released and should be addressed immediately. It will harm the user experience or will not function as expected.
- IMPORTANT: Return ONLY the JSON array with test results
  - IMPORTANT: Output your result in JSON format based on the `Report` section below.
  - IMPORTANT: Do not include any additional text, explanations, or markdown formatting
  - We'll immediately run JSON.parse() on the output, so make sure it's valid JSON
- Ultra think as you work through the review process. Focus on the critical functionality paths and the correctness of agent configurations.

## Setup

IMPORTANT: Read and **Execute** `.claude/commands/prepare_app.md` now to prepare the agent environment for the review.

## Evidence Generation

After completing the review, generate a composite evidence file:

1. **Collect evidence data:**
   - `git_diff_stat`: Output of `git diff --stat origin/main` (summary of changes)
   - `agent_configs_status`: Validation results for each agent config in `.kiro/agents/` (valid JSON, required fields present, prompt files referenced correctly)
   - `spec_summary`: Brief description of what the spec requires and whether the implementation matches

2. **Create the evidence directory:**
   - `<absolute path to codebase>/agents/<adw_id>/<agent_name>/review_evidence/`

3. **Write the evidence markdown file** to `<evidence_directory>/evidence.md` with these sections:
   - **Header**: Timestamp and worktree path
   - **Git Diff Summary**: The `git diff --stat` output showing what files changed
   - **Agent Configuration Validation**: Which configs were checked and their status
   - **Spec Compliance Assessment**: How well the implementation matches the spec

4. **Include the evidence file path** in the `screenshots` field of the output JSON (this reuses the existing field so the R2 upload pipeline picks it up automatically)

## Report

- IMPORTANT: Return results exclusively as a JSON array based on the `Output Structure` section below.
- `success` should be `true` if there are NO BLOCKING issues (implementation matches spec for critical functionality)
- `success` should be `false` ONLY if there are BLOCKING issues that prevent the work from being released
- `review_issues` can contain issues of any severity (skippable, tech_debt, or blocker)
- `screenshots` should contain the path to the generated evidence markdown file
- This allows subsequent agents to quickly identify and resolve blocking errors while documenting all issues

### Output Structure

```json
{
    success: "boolean - true if there are NO BLOCKING issues (can have skippable/tech_debt issues), false if there are BLOCKING issues",
    review_summary: "string - 2-4 sentences describing what was built and whether it matches the spec. Written as if reporting during a standup meeting. Example: 'The team-lead agent has been updated with delegation capabilities to builder and validator agents. The configuration matches the spec requirements for multi-agent orchestration. Agent prompt files are correctly referenced and contain appropriate instructions.'",
    review_issues: [
        {
            "review_issue_number": "number - the issue number based on the index of this issue",
            "screenshot_path": "string - /absolute/path/to/screenshot_or_empty_string.png",
            "issue_description": "string - description of the issue",
            "issue_resolution": "string - description of the resolution",
            "issue_severity": "string - severity of the issue between 'skippable', 'tech_debt', 'blocker'"
        },
        ...
    ],
    screenshots: ["agents/<adw_id>/<agent_name>/review_evidence/evidence.md"]
}
```
