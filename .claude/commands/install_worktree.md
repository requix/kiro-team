# Install Worktree

This command sets up an isolated worktree environment for kiro agent development.

## Parameters
- Worktree path: {0}

## Steps

1. **Navigate to worktree directory**
   ```bash
   cd {0}
   ```

2. **Verify `.kiro/` directory exists**
   - Check that `.kiro/agents/` directory exists (from target repo clone)
   - List available agent config files
   - If `.kiro/` is missing, report an error

3. **Verify kiro-cli is accessible**
   - Run `kiro-cli --version` to confirm it's available
   - No dependencies to install (kiro agents are config-only)

## Error Handling
- If `.kiro/` directory doesn't exist, report that the target repo may not have been cloned correctly
- Ensure all paths are absolute to avoid confusion

## Report
- List all agent config files found in `.kiro/agents/`
- Confirm kiro-cli is accessible
- Note any missing `.kiro/` directory or agent files
