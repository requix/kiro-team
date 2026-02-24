# Patch Plan

Create a **focused patch plan** to resolve a specific issue based on the `review_change_request`. Follow the `Instructions` to create a concise plan that addresses the issue with minimal, targeted changes.

## Variables

adw_id: $ARGUMENT
review_change_request: $ARGUMENT
spec_path: $ARGUMENT if provided, otherwise leave it blank
agent_name: $ARGUMENT if provided, otherwise use 'patch_agent'
issue_screenshots: $ARGUMENT (optional) - comma-separated list of screenshot paths if provided

## Instructions

- IMPORTANT: You're creating a patch plan to fix a specific review issue. Keep changes small, focused, and targeted
- Read the original specification (spec) file at `spec_path` if provided to understand the context and requirements
- IMPORTANT Use the `review_change_request` to understand exactly what needs and use it as the basis for your patch plan
- If `issue_screenshots` are provided, examine them to better understand the visual context of the issue
- Create the patch plan in `specs/patch/` directory with filename: `patch-adw-{adw_id}-{descriptive-name}.md`
  - Replace `{descriptive-name}` with a short name based on the issue (e.g., "fix-agent-config", "update-prompt", "correct-delegation")
- IMPORTANT: This is a PATCH - keep the scope minimal. Only fix what's described in the `review_change_request` and nothing more. Address only the `review_change_request`.
- Run `git diff --stat`. If changes are available, use them to understand what's been done in the codebase and so you can understand the exact changes you should detail in the patch plan.
- Ultra think about the most efficient way to implement the solution with minimal code changes
- Base your `Plan Format: Validation` on the validation steps from `spec_path` if provided
  - If any tests fail in the validation steps, you must fix them.
  - If not provided, READ `.claude/commands/test.md: ## Test Execution Sequence` and execute the tests to understand the tests that need to be run to validate the patch.
- Replace every <placeholder> in the `Plan Format` with specific implementation details
- IMPORTANT: When you finish writing the patch plan, return exclusively the path to the patch plan file created and nothing else.

## Relevant Files

Focus on the following files:
- `README.md` - Contains the project overview and instructions.
- `.kiro/agents/**` - Contains the kiro agent configuration files (JSON).
- `.kiro/prompts/**` - Contains the kiro agent prompt files (markdown).

- Read `.claude/commands/conditional_docs.md` to check if your task requires additional documentation
- If your task matches any of the conditions listed, reference those documentation files to understand the context better when creating your patch plan

Ignore all other files in the codebase.


## Plan Format

```md
# Patch: <concise patch title>

## Metadata
adw_id: `{adw_id}`
review_change_request: `{review_change_request}`

## Issue Summary
**Original Spec:** <spec_path>
**Issue:** <brief description of the review issue based on the `review_change_request`>
**Solution:** <brief description of the solution approach based on the `review_change_request`>

## Files to Modify
Use these files to implement the patch:

<list only the files that need changes - be specific and minimal>

## Implementation Steps
IMPORTANT: Execute every step in order, top to bottom.

<list 2-5 focused steps to implement the patch. Each step should be a concrete action.>

### Step 1: <specific action>
- <implementation detail>
- <implementation detail>

### Step 2: <specific action>
- <implementation detail>
- <implementation detail>

<continue as needed, but keep it minimal>

## Validation
Execute every command to validate the patch is complete with zero regressions.

<list 1-5 specific commands or checks to verify the patch works correctly>

## Patch Scope
**Lines of code to change:** <estimate>
**Risk level:** <low|medium|high>
**Testing required:** <brief description>
```

## Report

- IMPORTANT: Return exclusively the path to the patch plan file created and nothing else.
