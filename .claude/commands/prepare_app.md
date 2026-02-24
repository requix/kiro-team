# Prepare Agent Environment

Setup the kiro agent environment for review or testing.

## Setup

1. Verify `.kiro/` directory structure is intact:
   - Check `.kiro/agents/` directory exists
   - Check `.kiro/prompts/` directory exists (if applicable)
   - List all agent config files found

2. Validate all agent JSON configs parse correctly:
   - Run `python3 -m json.tool .kiro/agents/<agent>.json > /dev/null` for each agent file
   - Report any parsing errors

3. Verify kiro-cli is available and authenticated:
   - Run `kiro-cli --version` to confirm it's installed
   - Check `~/.local/share/kiro-cli/data.sqlite3` exists for auth

4. Create clean `specs/` directory for test plans if needed:
   - Run `mkdir -p specs/` to ensure the directory exists

Note: Kiro agents are config-only - no dependencies to install, no servers to start, no databases to reset.
