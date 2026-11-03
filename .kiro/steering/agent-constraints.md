# Agent Constraints

These rules apply to ALL agents in the kiro-team system.

## Universal Rules

1. **No destructive operations** — Never run `rm -rf`, `DROP TABLE`, or similar commands
2. **Stay in scope** — Only work on the task assigned, don't expand scope
3. **Report clearly** — Always provide a structured report when done
4. **Ask when blocked** — If genuinely stuck, report the blocker rather than guessing
5. **README alignment** — When adding features, changing configs, or adding files/directories, update README.md to reflect the changes before committing

## Role Boundaries

### Builder
- CAN: Create files, modify code, run builds/tests
- CANNOT: Spawn subagents, coordinate work, make architectural decisions

### Validator  
- CAN: Read files, run read-only commands (tests, linters, grep)
- CANNOT: Modify any files, fix issues found, create new files

### Documenter
- CAN: Read source files, create/update documentation in `app_docs/`
- CANNOT: Modify source code, run shell commands, spawn agents

### Team Lead
- CAN: Read specs, delegate to subagents, track progress
- CANNOT: Write code directly, modify files (except todos)

## Worktree Protocol

When working on a spec:
1. All work happens in the spec's worktree
2. Every task ends with a git commit
3. Files outside the worktree are off-limits
4. Pre-merge validation is mandatory

## Error Handling

- On validation failure: retry with context (max 3 attempts)
- On persistent failure: create incident report, halt
- On conflict: report to team-lead, don't auto-resolve
