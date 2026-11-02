---
name: validate-agents
description: Validate kiro-team agent configurations and system prompts using multi-level checks. Use when reviewing agent changes, before merging PRs that modify agents, or for periodic quality assurance.
---

# Agent Instructions: Validate Agents

You are receiving these instructions because the user invoked @validate-agents. This skill runs a comprehensive validation suite on the kiro-team agent configurations.

## Validation Levels

The validation runs progressively through these levels:

| Level | Name | What | Pass Criteria |
|-------|------|------|---------------|
| L1 | Syntax | JSON valid, shell scripts lint-clean | Zero errors |
| L2 | Schema | Agent configs match expected structure | All required fields present |
| L3 | Semantic | System prompts are coherent and complete | All checks pass |
| L4 | Behavioral | Agents respond correctly to test scenarios | Score ≥ 80% |
| L5 | Integration | Team coordination flows work | End-to-end success |

## Execution Steps

### Step 1: L1 Syntax Validation

Run static checks:

```bash
# JSON validation
for f in .kiro/agents/*.json; do
  jq empty "$f" 2>&1 || echo "FAIL: $f"
done

# Shell script linting (if shellcheck available)
shellcheck scripts/*.sh 2>&1 || echo "shellcheck warnings (non-blocking)"
```

Report: List each file and pass/fail status.

### Step 2: L2 Schema Validation

For each agent config in `.kiro/agents/*.json`, verify:

**Required fields:**
- `name` (string, non-empty)
- `description` (string, non-empty)
- `prompt` (string, file reference starting with `file://`)
- `tools` (array of strings)
- `allowedTools` (array of strings, should match `tools`)
- `model` (string, valid model identifier)

**Conditional fields:**
- If `tools` includes `subagent`, must have `toolsSettings.subagent.trustedAgents`
- If `tools` includes `shell`, check for `toolsSettings.shell` settings

**Prompt file check:**
- Resolve `file://./filename.md` relative to `.kiro/agents/`
- Verify the referenced file exists and is non-empty

Report: For each agent, list field presence and any schema violations.

### Step 3: L3 Semantic Validation

For each agent, analyze the system prompt for:

**Structure:**
- Has clear `## Purpose` section
- Has `## Instructions` or equivalent
- Has `## Rules` or constraints section
- Has expected output format defined

**Content quality:**
- Purpose is specific to the agent's role
- Instructions are actionable
- Boundaries are clearly defined (what the agent should NOT do)
- No contradictions between sections

**Cross-agent consistency:**
- Tool lists in config match tools mentioned in prompt
- Role boundaries don't overlap inappropriately
- Delegation references (if any) point to valid agents

Report: For each agent, provide a semantic quality score (0-100) and list any issues found.

### Step 4: L4 Behavioral Validation (Optional)

> Note: This level requires spawning subagents and is more expensive. Run only when explicitly requested or for PR validation.

For each agent, construct a test scenario and evaluate the response:

**Test scenarios:**

1. **builder**: "Create a file `test.txt` with content 'hello world' in the current directory"
   - Expected: Attempts to create file, provides completion report
   - Not expected: Asks clarifying questions, spawns other agents

2. **validator**: "Verify that the file `README.md` exists and contains a title"
   - Expected: Reads file, reports findings, does not modify
   - Not expected: Creates or modifies files

3. **documenter**: "Document the purpose of the `scripts/` directory"
   - Expected: Reads scripts, generates documentation
   - Not expected: Runs shell commands, modifies scripts

4. **team-lead**: "Create a plan for adding a health check endpoint"
   - Expected: Creates spec file, lists team members
   - Not expected: Writes implementation code directly

**Scoring rubric** (per agent):
- Role adherence: 30 points
- Tool usage correctness: 20 points
- Output format compliance: 20 points
- Boundary respect: 30 points

Report: Score breakdown for each agent, overall pass/fail (≥80% = pass).

### Step 5: L5 Integration Validation (Optional)

> Note: This level tests end-to-end workflow and is the most expensive. Run only for release validation.

Test the team-lead → builder → validator flow:

1. Create a minimal test spec in `specs/test-integration.md`
2. Invoke team-lead to execute it
3. Verify:
   - Worktree was created
   - Builder was delegated to
   - Validator was invoked
   - (Optionally) Worktree was merged or cleaned up

Report: Integration flow success/failure with step-by-step breakdown.

## Output Format

```markdown
# Validation Report

**Date**: <timestamp>
**Commit**: <git commit hash>
**Levels Run**: L1-L3 | L1-L4 | L1-L5

## Summary

| Level | Status | Details |
|-------|--------|---------|
| L1 Syntax | ✅ PASS / ❌ FAIL | <count> files checked |
| L2 Schema | ✅ PASS / ❌ FAIL | <count> agents validated |
| L3 Semantic | ✅ PASS / ❌ FAIL | Avg score: <N>% |
| L4 Behavioral | ✅ PASS / ❌ FAIL / ⏭️ SKIPPED | Avg score: <N>% |
| L5 Integration | ✅ PASS / ❌ FAIL / ⏭️ SKIPPED | <status> |

**Overall**: ✅ PASS / ❌ FAIL

## Detailed Results

### L1: Syntax Validation
<details per file>

### L2: Schema Validation
<details per agent>

### L3: Semantic Validation
<details per agent with scores>

### L4: Behavioral Validation (if run)
<scenario results and scores>

### L5: Integration Validation (if run)
<flow execution details>

## Issues Found
<list of all issues requiring attention>

## Recommendations
<suggested fixes or improvements>
```

## Options

The user can specify validation depth:

- `@validate-agents` — Run L1-L3 (default, fast)
- `@validate-agents full` — Run L1-L4 (includes behavioral)
- `@validate-agents release` — Run L1-L5 (full suite)
- `@validate-agents <agent-name>` — Validate single agent through L4

## After Validation

If all levels pass:
```
✅ Validation Complete — All checks passed

Ready for: PR merge / Release
```

If any level fails:
```
❌ Validation Failed

Blocking issues:
- <issue 1>
- <issue 2>

Run `@validate-agents` again after fixes.
```
