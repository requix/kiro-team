# Verify Kiro-CLI Environment

## Workflow

1. Check kiro-cli version:
   - Run `kiro-cli --version`
   - If it fails, let the user know kiro-cli is not installed or not in PATH

2. Check kiro-cli authentication:
   - Check if `~/.local/share/kiro-cli/data.sqlite3` exists
   - If it doesn't exist, let the user know they need to authenticate with `kiro-cli auth`

3. Check `.kiro/agents/` directory:
   - Verify the directory exists
   - List available agents (JSON files in the directory)
   - Report which agents are configured

4. Let the user know the kiro-cli environment status:
   - kiro-cli version
   - Authentication status
   - Available agents
