---
name: plan-with-team
description: Create a detailed implementation plan for a task and save it to specs/ directory. Use when the user wants to plan a feature, fix, or enhancement for multi-agent team execution with builder, validator, and documenter agents.
---

# Agent Instructions: Plan With Team

You are receiving these instructions because the user invoked @plan-with-team. The user's message that triggered this skill IS their task description. Everything the user wrote is what you need to plan. Do NOT ask for clarification — plan it now.

## What To Do

1. Take the user's message as the task to plan
2. Create a spec file at `specs/<kebab-case-name>.md`
3. Use the format below
4. Report what you created

## Rules

- NEVER ask "What would you like to build?" — the user already told you
- PLANNING ONLY — do NOT write code or deploy agents
- Generate a kebab-case filename from the task (e.g., `azure-blob-storage-module`)
- Do NOT prepend `issue-`, `adw-`, or any prefix to the filename
- Explore the codebase first to understand existing patterns

## Spec Format

```markdown
# Plan: <task name>

## Task Description
<describe the task in detail>

## Objective
<clearly state what will be accomplished>

## Problem Statement
<define the specific problem or opportunity>

## Solution Approach
<describe the proposed solution>

## Relevant Files
<list files relevant to the task>

### New Files
<list new files to be created>

## Team Orchestration

> **Worktree Isolation**: The team-lead creates an isolated git worktree for this spec using `scripts/worktree-create.sh`. All builders work inside this worktree. After final validation, changes are merged back via `scripts/worktree-merge.sh`.

### Team Members

- **Builder**
  - Name: <unique name>
  - Role: <specific focus>
  - Agent: builder

- **Validator**
  - Name: <unique name>
  - Role: Verify implementation meets criteria
  - Agent: validator

- **Documenter**
  - Name: <unique name>
  - Role: Generate documentation
  - Agent: documenter

## Step by Step Tasks

### 1. <Task Name>
- **Task ID**: <kebab-case-id>
- **Depends On**: none
- **Assigned To**: <team member>
- **Agent**: builder
- **Actions**:
  - <action>
- **Acceptance Criteria**:
  - <criterion>

### N-1. Final Validation
- **Task ID**: validate-all
- **Depends On**: <all previous>
- **Assigned To**: validator
- **Agent**: validator
- **Checks**:
  - Run all validation commands
  - Verify acceptance criteria met

### N. Documentation
- **Task ID**: generate-docs
- **Depends On**: validate-all
- **Assigned To**: documenter
- **Agent**: documenter
- **Actions**:
  - Generate documentation in `app_docs/`

## Acceptance Criteria
<measurable criteria>

## Validation Commands
<commands to verify>

## Notes
<optional context>
```

## After Creating The Plan

Output this summary:

```
✅ Implementation Plan Created

File: specs/<filename>.md
Topic: <brief description>

Key Components:
- <component 1>
- <component 2>

Team Members:
- <member>: <role>

Tasks:
1. <task> → <assigned to>
2. <task> → <assigned to>

To execute this plan:
1. Switch to team-lead agent: /agent swap → team-lead
2. Say: "Execute the plan in specs/<filename>.md"
```
