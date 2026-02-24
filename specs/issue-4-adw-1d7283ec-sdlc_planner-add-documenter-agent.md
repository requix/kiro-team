# Feature: Add Documenter Agent

## Metadata
issue_number: `4`
adw_id: `1d7283ec`
issue_json: `{"number":4,"title":"New agent","body":"/feature\n\nadw_sdlc_iso\n\nAdd new specialized agent that generates documentation for completed features as the final step in the team workflow — after all builders finish implementation and validators confirm everything works.\n\nWhy Last Step?\n\nDocuments what was actually built, not what was planned\nCan reference real file paths, function names, and APIs\nValidation has already confirmed the code works\nNo risk of documenting features that failed validation\nWorkflow Position\n\nbuilder(s) → validator (per task) → ... → final validator → documenter"}`

## Feature Description

Add a `documenter` agent that runs as the final step in the team workflow, after all builders have completed implementation and the final validator has confirmed everything works. The documenter reads the actual implemented code and generates accurate, up-to-date documentation that reflects what was truly built — not what was planned.

This agent has read-only access (like the validator) and produces documentation artifacts (markdown files) describing the feature: file structure, public APIs, usage examples, and key design decisions.

## User Story

As a developer using the kiro-teams workflow,
I want a documenter agent to automatically generate documentation after my feature is validated,
So that every completed feature has accurate, code-grounded documentation without manual effort.

## Problem Statement

Documentation written before or during implementation often drifts from reality. Plans change, APIs evolve, and file paths shift. Writing docs after validation ensures they reflect the actual working system — but this step is easy to skip under time pressure.

## Solution Statement

Introduce a `documenter` agent as the final step in the team-lead workflow. After the final validator confirms all acceptance criteria pass, the team-lead spawns the documenter. The documenter reads the implemented files, inspects the actual code, and writes a documentation file (e.g., `docs/<feature-name>.md`) describing what was built. The team-lead then includes the documentation artifact in its execution report.

## Relevant Files

- `.kiro/agents/team-lead.json` — needs `documenter` added to `trustedAgents` so team-lead can spawn it without permission prompts
- `.kiro/agents/team-lead-prompt.md` — needs a new workflow step (Step 4: Document) and updated execution report format to include docs artifact
- `.kiro/agents/validator.json` — reference for read-only agent config pattern (documenter follows the same tool constraints)
- `.kiro/agents/validator-prompt.md` — reference for read-only agent prompt pattern
- `README.md` — needs updated workflow diagram and agent table to include documenter
- Read `.claude/commands/test_e2e.md` and `.claude/commands/e2e/test_builder_agent.md` to understand how to create the E2E test file

### New Files

- `.kiro/agents/documenter.json` — agent config: read-only tools (`read`, `shell`), references `documenter-prompt.md`
- `.kiro/agents/documenter-prompt.md` — agent behavior: read implemented files, write a `docs/<feature>.md` documentation file
- `.claude/commands/e2e/test_documenter_agent.md` — E2E test validating the documenter agent creates a documentation file

## Implementation Plan

### Phase 1: Foundation

Create the documenter agent config and prompt files following the same patterns as the validator agent (read-only, focused on a single responsibility).

### Phase 2: Core Implementation

Update the team-lead to recognize and spawn the documenter as the final step after the final validator passes. The documenter receives context about what was built (file list, feature name) and produces a `docs/` artifact.

### Phase 3: Integration

Update `README.md` to reflect the new 4-phase workflow (Plan → Execute → Validate → Document) and the updated agent table. Add the documenter to the architecture diagrams.

## Step by Step Tasks

### Task 1: Create E2E test file for documenter agent

- Read `.claude/commands/test_e2e.md` to understand the E2E test format
- Read `.claude/commands/e2e/test_builder_agent.md` as a structural reference
- Create `.claude/commands/e2e/test_documenter_agent.md` with:
  - User story: documenter agent reads existing files and produces a `docs/` markdown file
  - Test steps: set up a temp dir with `.kiro/` and a sample source file, invoke `kiro-cli chat` with the documenter agent asking it to document the file, verify `docs/*.md` is created and non-empty
  - Success criteria: exit code 0, docs file exists, file is non-empty markdown
  - Output format matching other E2E test files

### Task 2: Create `.kiro/agents/documenter.json`

- Model the config after `validator.json` (read-only tools)
- Set `"name": "documenter"`
- Set `"tools": ["read", "write", "shell"]` — documenter needs `write` to produce the docs file
- Set `"allowedTools": ["read", "write", "shell"]`
- Set `"prompt": "file://./documenter-prompt.md"`
- Add a clear `"description"` field
- Add `"welcomeMessage"`
- Use `"model": "claude-sonnet-4"`

### Task 3: Create `.kiro/agents/documenter-prompt.md`

- Define the documenter's purpose: generate documentation for a completed, validated feature
- Instructions:
  - Read all files listed in the task context (the files changed during implementation)
  - Inspect actual function signatures, exports, and APIs
  - Write a documentation file to `docs/<feature-name>.md`
  - Documentation must include: overview, file structure, public API/functions, usage example, and any important notes
  - Do NOT modify implementation files
- Define a clear report format (similar to builder/validator) confirming the docs file path and a brief summary

### Task 4: Update `.kiro/agents/team-lead.json`

- Add `"documenter"` to the `trustedAgents` array so the team-lead can spawn it without per-invocation permission prompts

### Task 5: Update `.kiro/agents/team-lead-prompt.md`

- Add `**documenter**` to the Team Members section with description: "Generates documentation for completed, validated features (read + write)"
- Add a new **Step 4: Document** section to the Workflow after "Final Validation":
  - After final validator reports ✅ PASS, spawn the documenter subagent
  - Pass it: the feature name, the list of files changed, and the plan's acceptance criteria
  - The documenter writes `docs/<feature-name>.md`
  - If documenter fails, log a warning but do NOT re-run builders (documentation failure is non-blocking)
- Update the Execution Report template to include a **Docs Generated** field listing the documentation artifact

### Task 6: Update `README.md`

- Update the top-level workflow ASCII diagram to add `documenter` after the final validator:
  ```
  builder(s) → validator (per task) → ... → final validator → documenter
  ```
- Update the agent table to add a documenter row (Can Do: read files, write docs | Cannot Do: modify implementation)
- Update the Phase section to add **Phase 4: Documentation**
- Update the architecture diagram to include the documenter agent box
- Update the File Structure section to show `documenter.json` and `documenter-prompt.md`
- Update the Agent Configuration section with a `documenter.json` example

### Task 7: Run Validation Commands

- Execute all validation commands listed in the Validation Commands section to confirm zero regressions

## Testing Strategy

### Unit Tests

- Validate all JSON agent configs parse correctly with `python3 -m json.tool`
- Verify all prompt `.md` files exist and are non-empty
- Confirm `documenter` appears in `team-lead.json` trustedAgents

### Edge Cases

- Documenter receives an empty file list — should still produce a minimal docs file
- Documenter is invoked but `docs/` directory doesn't exist — documenter should create it
- Final validator fails — team-lead should NOT invoke documenter (only document validated work)

## Acceptance Criteria

- `documenter.json` exists in `.kiro/agents/` and is valid JSON
- `documenter-prompt.md` exists in `.kiro/agents/` and is non-empty
- `team-lead.json` includes `"documenter"` in `trustedAgents`
- `team-lead-prompt.md` describes the documenter step in the workflow
- `README.md` reflects the updated 4-agent workflow with documenter as the final step
- E2E test file `.claude/commands/e2e/test_documenter_agent.md` exists and follows the established test format
- All existing agent JSON configs remain valid (no regressions)

## Validation Commands

- Validate all agent JSON configs:
  ```
  python3 -m json.tool .kiro/agents/team-lead.json && python3 -m json.tool .kiro/agents/builder.json && python3 -m json.tool .kiro/agents/validator.json && python3 -m json.tool .kiro/agents/documenter.json
  ```
- Verify all prompt files exist and are non-empty:
  ```
  test -s .kiro/agents/team-lead-prompt.md && echo "team-lead-prompt OK"
  test -s .kiro/agents/builder-prompt.md && echo "builder-prompt OK"
  test -s .kiro/agents/validator-prompt.md && echo "validator-prompt OK"
  test -s .kiro/agents/documenter-prompt.md && echo "documenter-prompt OK"
  ```
- Verify documenter is in trustedAgents:
  ```
  python3 -c "import json; cfg=json.load(open('.kiro/agents/team-lead.json')); assert 'documenter' in cfg['toolsSettings']['subagent']['trustedAgents'], 'documenter missing from trustedAgents'; print('trustedAgents OK')"
  ```
- Read `.claude/commands/test_e2e.md`, then read and execute `.claude/commands/e2e/test_documenter_agent.md` to validate the documenter agent works end-to-end

## Notes

- The documenter uses `write` tool (unlike the validator which is strictly read-only) because its job is to produce documentation artifacts. This is intentional and follows least-privilege: it can only write to `docs/`, not modify implementation files (enforced by prompt instructions).
- Documentation failure should be non-blocking — if the documenter fails, the team-lead should log a warning and complete the execution report without a docs artifact rather than marking the entire workflow as failed.
- Future consideration: the documenter could be extended to update an existing `docs/index.md` table of contents, or generate API reference from docstrings.
- The `docs/` directory should be created by the documenter if it doesn't exist.
