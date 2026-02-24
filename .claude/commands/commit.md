# Generate Git Commit

Based on the `Instructions` below, take the `Variables` follow the `Run` section to create a git commit with a properly formatted message. Then follow the `Report` section to report the results of your work.

## Variables

agent_name: $ARGUMENT
issue_class: $ARGUMENT
issue: $ARGUMENT

## Instructions

- Generate a concise commit message in the format: `<agent_name>: <issue_class>: <commit message>`
- The `<commit message>` should be:
  - Present tense (e.g., "add", "fix", "update", not "added", "fixed", "updated")
  - 50 characters or less
  - Descriptive of the actual changes made
  - No period at the end
- Examples:
  - `sdlc_planner: feat: add user authentication module`
  - `sdlc_implementor: bug: fix login validation error`
  - `sdlc_planner: chore: update dependencies to latest versions`
- Extract context from the issue JSON to make the commit message relevant
- Don't include any 'Generated with...' or 'Authored by...' in the commit message. Focus purely on the changes made.

## Run

1. Run `git diff HEAD` to understand what changes have been made
2. Remove any ADW internal artifacts from tracking before staging:
   ```
   git rm -rf --cached --ignore-unmatch .claude/ .mcp.json agents/ logs/ specs/
   ```
3. Run `git add -A` to stage all changes
4. Run `git commit -m "<generated_commit_message>"` to create the commit

## Report

Return ONLY the commit message that was used (no other text)