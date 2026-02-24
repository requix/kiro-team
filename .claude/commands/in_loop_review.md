# In-Loop Review

Quick checkout and review workflow for agent work validation.

## Variables

branch: $ARGUMENTS

## Workflow

IMPORTANT: If no branch is provided, stop execution and report that a branch argument is required.

Follow these steps to quickly checkout and review work done by agents:

### Step 1: Pull and Checkout Branch
- Run `git fetch origin` to get latest remote changes
- Run `git checkout {branch}` to switch to the target branch

### Step 2: Prepare Environment
- Read and execute: `.claude/commands/prepare_app.md` to verify the agent environment

### Step 3: Verify Agent Configs
- Read and execute: `.claude/commands/start.md` to verify kiro-cli environment status

### Step 4: Manual Review
- The agent environment is now ready for manual review
- Run `git diff origin/main` to review all changes made in the branch
- Check `.kiro/agents/` for any agent config changes
- Check `.kiro/prompts/` for any prompt file changes

## Report

Report steps you've taken to prepare the environment for review.
