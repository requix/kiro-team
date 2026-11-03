# Kiro Team: Multi-Agent Orchestration for Kiro CLI

A team orchestration system that enables multiple AI agents to collaborate on complex tasks inside [Kiro CLI](https://kiro.dev).

## How It Works

A team-lead agent reads a plan, delegates tasks to specialized subagents (builders, validators, and a documenter), and tracks progress. The team-lead is the central coordinator — subagents execute their assigned work and report results back.

```
You ──→ @plan-with-team Build a REST API...
                │
                ▼
          ┌────────────┐
          │ Plan saved │  specs/rest-api.md
          └─────┬──────┘
                │
                ▼
        ┌───────────────┐
        │   Team Lead   │  reads plan, delegates, tracks progress
        └───────┬───────┘
                │
          ┌─────┴─────┐
          ▼           ▼
    ┌──────────┐ ┌──────────┐
    │  Builder │ │  Builder │  write code (up to 4 in parallel)
    └─────┬────┘ └─────┬────┘
          │            │
          ▼            ▼
   ┌───────────┐ ┌───────────┐
   │ Validator │ │ Validator │  verify each task immediately
   └────┬──────┘ └─────┬─────┘
        └──────┬───────┘
               ▼
         ┌────────────┐
         │ Validator  │  final end-to-end verification
         └─────┬──────┘
               │
               ▼
         ┌────────────┐
         │ Documenter │  generate documentation (non-blocking)
         └────────────┘
```

Four agent roles, clear separation of concerns:

| Agent | Can Do | Cannot Do |
|-------|--------|-----------|
| **Team Lead** | Read code, delegate tasks, track TODO list | Write code |
| **Builder** | Write code, create files, run commands | Spawn other agents |
| **Validator** | Read files, run tests, inspect output | Modify anything |
| **Documenter** | Read files, generate documentation | Modify implementation code, spawn agents, run commands |

## How Task Coordination Works

The team-lead manages all task tracking. Subagents (builders, validators, documenter) do not have access to the TODO list — they receive instructions from the team-lead, do their work, and return results. The team-lead then updates task status based on those results.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Team Lead (sole access to TODO list)                       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Reads plan from specs/                           │    │
│  │ 2. Creates TODO items for each task                 │    │
│  │ 3. Dispatches subagents with task instructions      │    │
│  │ 4. Receives results back from subagents             │    │
│  │ 5. Updates TODO list based on results               │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                   │
│              dispatches tasks via subagent tool             │
│                         │                                   │
│             ┌───────────┴───────────┐                       │
│             ▼                       ▼                       │
│  ┌──────────────────┐   ┌───────────────────┐               │
│  │ Builder          │   │ Validator         │               │
│  │ • receives task  │   │ • receives task   │               │
│  │ • writes code    │   │ • reads files     │               │
│  │ • reports back   │   │ • runs checks     │               │
│  │                  │   │ • reports back    │               │
│  └──────────────────┘   └───────────────────┘               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

> **Why can't subagents access the TODO list?** The `todo` tool is [not available in the subagent runtime](https://kiro.dev/docs/cli/chat/subagents#tool-availability). This is a Kiro CLI platform limitation, not a configuration choice. The team-lead acts as the single source of truth for task status.

## Quick Start

```bash
# 1. Copy .kiro folder and scripts into your project
cp -r .kiro /path/to/your/project/
cp -r scripts /path/to/your/project/scripts

# 2. Enable the TODO list (experimental)
kiro-cli settings chat.enableTodoList true

# 3. Start Kiro CLI in your project
cd /path/to/your/project
kiro-cli chat

# 4. Invoke the planning skill with your task description
@plan-with-team Build a CLI tool that converts CSV to JSON

# 5. Switch to team-lead and execute
/agent swap        # select: team-lead
Execute the plan in specs/csv-to-json.md
```

> **Note:** `plan-with-team` is implemented as an [Agent Skill](https://kiro.dev/docs/cli/chat/skills/) (`.kiro/skills/plan-with-team/SKILL.md`), not a prompt. Skills preserve the user's full message as input while loading the skill content as context — this means inline arguments work reliably in all modes (TUI, classic, and headless). If you invoke `@plan-with-team` without additional text, the agent infers a task from the repository context.

## Phases

### Phase 1: Planning

The `@plan-with-team` skill activates the planning agent. It only creates a plan — no code is written.

```bash
# Single-message workflow (recommended)
@plan-with-team Add user authentication with JWT tokens

# Without arguments — agent infers task from repo context and plans immediately
@plan-with-team
```

You can also invoke `@plan-with-team` without arguments — the agent will infer a task from the repository context (README, open issues, recent git history) and proceed to plan immediately.

This creates `specs/user-auth-jwt.md` containing:
- Task breakdown with dependencies
- Agent assignments (which builder does what)
- Acceptance criteria for each task
- Validation commands to verify the work

### Phase 2: Execution

Switch to the team-lead agent and point it at the plan:

```bash
/agent swap  # select: team-lead
Execute the plan in specs/user-auth-jwt.md
```

The team lead:
1. Reads the plan
2. Creates a TODO list from the tasks
3. Spawns builder subagent for a task
4. Immediately spawns validator subagent to verify that task
5. If validation passes, marks task complete and proceeds to next task
6. If validation fails, spawns builder again to fix issues
7. After all tasks complete, spawns validator for final end-to-end verification
8. Spawns documenter to generate documentation (non-blocking)
9. Reports results

### Phase 3: Validation

The validator agent runs after each builder task AND at the end:

**Incremental validation (after each task):**
- Verifies the specific task output
- Runs relevant checks for that component
- Reports pass/fail immediately
- Enables fast feedback and early bug detection

**Final validation (after all tasks):**
- Verifies integration between all components
- Runs end-to-end tests
- Checks overall acceptance criteria
- Reports comprehensive pass/fail

If any validation fails, the team lead re-deploys a builder to fix issues, then re-validates.

### Phase 4: Documentation

After final validation passes, the team lead spawns the documenter agent:

- Reads the plan and implementation files
- Generates a markdown documentation file in `app_docs/`
- Documents what was actually built (file paths, functions, APIs)
- This step is non-blocking — if the documenter fails, the workflow still succeeds

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kiro CLI Process                        │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Agent Layer                         │  │
│  │                                                       │  │
│  │  ┌─────────────┐                                      │  │
│  │  │ Default     │  @plan-with-team skill               │  │
│  │  │ Agent       │──────────────────────┐               │  │
│  │  └─────────────┘                      │               │  │
│  │                                       ▼               │  │
│  │  ┌─────────────┐              ┌──────────────┐        │  │
│  │  │ Team Lead   │◄──────────── │ specs/*.md   │        │  │
│  │  │ Agent       │              └──────────────┘        │  │
│  │  └──────┬──────┘                                      │  │
│  │         │ subagent tool                               │  │
│  │         │                                             │  │
│  │  ┌──────┴──────────────────────────────────────┐      │  │
│  │  │    TODO List (team-lead only)               │      │  │
│  │  │    Tracks task status, not shared           │      │  │
│  │  └──────┬──────────────────────┬───────────────┘      │  │
│  │         │                      │                      │  │
│  │    ┌────┴────┐                 │                      │  │
│  │    ▼         ▼                 ▼                      │  │
│  │  ┌───────┐ ┌───────┐     ┌───────────┐                │  │
│  │  │Builder│ │Builder│     │ Validator │                │  │
│  │  │Agent  │ │Agent  │     │ Agent     │                │  │
│  │  └───────┘ └───────┘     └───────────┘                │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Subagent Tool Availability               │  │
│  │  ✅ read │ ✅ write │ ✅ shell │ ✅ MCP tools        │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  File System                          │  │
│  │  .kiro/agents/*.json  │  specs/*.md  │  src/**/*      │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
.kiro/
├── agents/
│   ├── team-lead.json          ← Orchestrator config
│   ├── team-lead-prompt.md     ← Orchestrator behavior
│   ├── builder.json            ← Builder config
│   ├── builder-prompt.md       ← Builder behavior
│   ├── validator.json          ← Validator config
│   ├── validator-prompt.md     ← Validator behavior
│   ├── documenter.json         ← Documenter config
│   └── documenter-prompt.md    ← Documenter behavior
├── evals/
│   ├── scenarios/              ← Behavioral test scenarios
│   │   ├── builder/            ← 5 scenarios (incl. adversarial)
│   │   ├── validator/          ← 4 scenarios (incl. adversarial)
│   │   ├── documenter/         ← 2 scenarios (incl. adversarial)
│   │   └── team-lead/          ← 3 scenarios
│   ├── rubric.yaml             ← Scoring criteria (v2.0)
│   ├── baselines/              ← Named baseline results
│   └── history/                ← Run results (gitignored)
├── steering/
│   └── agent-constraints.md    ← Universal rules for all agents
├── prompts/
│   └── (deprecated - migrated to skills)
└── skills/
    └── plan-with-team/
        └── SKILL.md            ← Planning skill (invoked with @)

scripts/
├── validate-agents.sh          ← Static validation (67 checks)
├── run-evals.sh                ← List/run behavioral evals
├── install-hooks.sh            ← Install git hooks
├── pre-push                    ← Pre-push validation hook
├── worktree-create.sh          ← Creates isolated worktree for builder
└── worktree-merge.sh           ← Merges builder worktree and cleans up
```

> **Note:** All agent configs must be directly in `.kiro/agents/` — subdirectories are not supported for subagent resolution.

### Agent Configuration

Each agent is defined by a JSON config + a markdown prompt:

**team-lead.json** — the orchestrator:
```json
{
  "name": "team-lead",
  "tools": ["fs_read", "subagent", "todo"],
  "allowedTools": ["fs_read", "subagent", "todo"],
  "toolsSettings": {
    "subagent": {
      "trustedAgents": ["builder", "validator", "documenter"]
    }
  },
  "resources": ["file://.kiro/steering/**/*.md"],
  "model": "claude-sonnet-4"
}
```

Key points:
- Has `subagent` tool to spawn builders, validators, and documenter
- Does NOT have `fs_write` or `execute_bash` — cannot modify files directly
- Can use `todo` tool for task tracking (experimental, enable separately)
- `trustedAgents` allows spawning without permission prompts each time
- Receives steering constraints automatically via `resources`


**builder.json** — the implementer:
```json
{
  "name": "builder",
  "tools": ["fs_read", "fs_write", "execute_bash"],
  "allowedTools": ["fs_read", "fs_write", "execute_bash"],
  "resources": ["file://.kiro/steering/**/*.md"],
  "model": "claude-sonnet-4"
}
```

Key points:
- Has `fs_read`, `fs_write` and `execute_bash` — can create/modify files and run commands
- Does NOT have `subagent` — cannot spawn other agents
- Receives steering constraints automatically via `resources`

**validator.json** — the verifier:
```json
{
  "name": "validator",
  "tools": ["fs_read", "execute_bash", "grep", "glob"],
  "toolsSettings": {
    "execute_bash": { "autoAllowReadonly": true }
  },
  "resources": ["file://.kiro/steering/**/*.md"],
  "model": "claude-sonnet-4"
}
```

Key points:
- Has `fs_read`, `execute_bash` (read-only), `grep` and `glob` — can inspect but not modify
- Does NOT have `fs_write` — cannot change files
- Shell is auto-allowed for read-only commands
- `grep`/`glob` enable code search within subagent context

**documenter.json** — the documentation generator:
```json
{
  "name": "documenter",
  "tools": ["fs_read", "fs_write"],
  "allowedTools": ["fs_read", "fs_write"],
  "resources": ["file://.kiro/steering/**/*.md"],
  "model": "claude-sonnet-4"
}
```

Key points:
- Has `fs_read` and `fs_write` — can inspect files and create documentation
- Does NOT have `execute_bash` — documentation generation is purely file-based
- Does NOT have `subagent` — cannot spawn other agents
- Receives steering constraints automatically via `resources`

### Steering Files

All agents receive shared constraints via the `resources` field:

```json
"resources": ["file://.kiro/steering/**/*.md"]
```

This auto-injects `.kiro/steering/agent-constraints.md` into every agent's context, ensuring consistent behavior rules across the team.

### Design Principles

Each agent gets only the tools it needs (least privilege):

```
Team Lead:  fs_read, subagent (+ todo in main session)
            ↑ can read and delegate, but CANNOT write files

Builder:    fs_read, fs_write, execute_bash
            ↑ can modify files, but CANNOT spawn agents

Validator:  fs_read, execute_bash (read-only), grep, glob
            ↑ can inspect and search, but CANNOT modify anything

Documenter: fs_read, fs_write
            ↑ can read files and generate docs, but CANNOT run commands or spawn agents
```

## Kiro CLI Features Used

| Feature | What It Does Here |
|---------|-------------------|
| [Custom Agents](https://kiro.dev/docs/cli/custom-agents) | Define team-lead, builder, validator, documenter with specific tools |
| [Subagents](https://kiro.dev/docs/cli/chat/subagents) | Team lead spawns builders/validators/documenter as child agents |
| [Prompts](https://kiro.dev/docs/cli/chat/manage-prompts) | `@plan-with-team` reusable planning template |
| [TODO Lists](https://kiro.dev/docs/cli/experimental/todo-lists) | Team-lead tracks task progress (not accessible to subagents) |

## Walkthrough: Building a Calculator API

### Step 1: Create the Plan

```bash
$ cd my-project
$ kiro-cli chat
```

```
> @plan-with-team Build a REST API with endpoints for add, subtract, multiply, divide
```

Kiro generates `specs/calculator-api.md`:

```markdown
# Plan: Calculator API

## Task Description
Build a simple REST API with endpoints for basic arithmetic operations.

## Team Orchestration
### Team Members
- **Builder**: calc-builder — Implement calculator endpoints
- **Validator**: calc-validator — Verify implementation

## Step by Step Tasks

### 1. Setup Project
- Task ID: setup-project
- Depends On: none
- Assigned To: calc-builder
- Actions: Create package.json, install express

### 2. Create Calculator Routes
- Task ID: create-calc-routes
- Depends On: setup-project
- Assigned To: calc-builder
- Actions: POST /add, /subtract, /multiply, /divide with validation

### 3. Create Server Entry Point
- Task ID: create-server
- Depends On: create-calc-routes
- Assigned To: calc-builder
- Actions: Express server, mount routes, JSON body parser

### 4. Final Validation
- Task ID: validate-all
- Depends On: all above
- Assigned To: calc-validator
- Checks: Files exist, server starts, endpoints respond
```

### Step 2: Execute the plan

```bash
> /agent swap                      # select: team-lead
> Execute the plan in specs/calculator-api.md
```

What happens behind the scenes:

```
team-lead reads specs/calculator-api.md
    │
    ├─→ creates TODO list from plan (team-lead only)
    │
    ├─→ subagent(builder): "Setup project — create package.json with express"
    │       └─→ creates package.json, runs npm install
    │       └─→ reports back to team-lead
    │
    ├─→ subagent(validator): "Verify package.json and dependencies installed"
    │       └─→ checks files, reports: "✅ PASS"
    │
    ├─→ team-lead marks task 1 complete, dispatches next
    │
    ├─→ subagent(builder): "Create calculator routes with validation"
    │       └─→ creates src/routes/calculator.js
    │       └─→ reports back to team-lead
    │
    ├─→ subagent(validator): "Verify routes file structure and exports"
    │       └─→ checks code, reports: "✅ PASS"
    │
    ├─→ subagent(builder): "Create Express server entry point"
    │       └─→ creates src/index.js
    │       └─→ reports back to team-lead
    │
    ├─→ subagent(validator): "Verify server file and imports"
    │       └─→ checks code, reports: "✅ PASS"
    │
    └─→ subagent(validator): "Final validation — verify server starts and endpoints work"
            └─→ runs node src/index.js, tests endpoints
            └─→ reports: "✅ PASS. All checks passed."
    │
    └─→ subagent(documenter): "Document the calculator API feature"
            └─→ reads plan and implementation files
            └─→ creates app_docs/feature-calculator-api.md
            └─→ reports: "✅ Documentation generated."
```

### Step 3: Test the Result

```bash
$ cd src && npm start
# Server running on port 3000

$ curl -X POST http://localhost:3000/calculator/add \
    -H "Content-Type: application/json" \
    -d '{"a": 5, "b": 3}'
# {"result": 8}
```

## Task Dependency Graph

Tasks can run in parallel when they don't depend on each other (up to 4 subagents simultaneously):

```
                    ┌─────────────────┐
                    │ 1. Setup Project│
                    │   (builder)     │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
           ┌──────────────┐  ┌──────────────┐
           │ 2. Module A  │  │ 3. Module B  │   ← parallel
           │   (builder)  │  │   (builder)  │
           └──────┬───────┘  └──────┬───────┘
                  │                 │
                  └────────┬────────┘
                           ▼
                  ┌──────────────┐
                  │ 4. Integrate │
                  │   (builder)  │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ 5. Validate  │
                  │  (validator) │
                  └──────────────┘
```

In the plan spec, this is expressed as:

```markdown
### 2. Module A
- Depends On: setup-project
- Parallel: true

### 3. Module B
- Depends On: setup-project
- Parallel: true

### 4. Integrate
- Depends On: module-a, module-b
```

## Worktree Isolation for Spec Execution

Every spec execution runs inside an isolated git worktree. The team-lead creates it as its first step, all builders work sequentially inside it, and the worktree merges once at the end. This enables multi-spec parallelism — two specs can run in separate terminals without conflicting.

### How It Works

```
user requests spec execution
    │
    ├─→ worktree-create.sh my-feature  → .worktrees/my-feature/
    │
    │   team-lead orchestrates all builders sequentially
    │   inside .worktrees/my-feature/
    │
    ├─→ final validation passes        → ✅
    ├─→ worktree-merge.sh my-feature   → merged, worktree removed
    │
    └─→ .worktrees/ cleaned up
```

### Scripts

**`scripts/worktree-create.sh <spec-name>`**

Creates an isolated git worktree at `.worktrees/<spec-name>/` on a new branch `spec/<spec-name>`. Prints the absolute worktree path to stdout (the team-lead captures this and passes it to every subagent).

```bash
WORKTREE_PATH=$(bash scripts/worktree-create.sh add-auth-flow)
# → /path/to/project/.worktrees/add-auth-flow
```

Idempotent — if the worktree already exists, prints its path and exits successfully.

**`scripts/worktree-merge.sh <spec-name>`**

Merges the spec's branch back into the current branch, then removes the worktree and cleans up the branch.

```bash
bash scripts/worktree-merge.sh add-auth-flow
# → Merges spec/add-auth-flow, removes .worktrees/add-auth-flow/, deletes branch
```

If a merge conflict occurs, the merge is aborted, the worktree is preserved for manual resolution, and the script exits with code 1.

### Team-Lead Protocol

The team-lead follows this 3-step protocol for every spec execution:

1. **Create** — Run `worktree-create.sh <spec-name>` as the very first action. Capture the path.
2. **Execute** — All builders and validators work inside this single worktree. Pass the path to every subagent.
3. **Merge** — After final validation passes, run `worktree-merge.sh <spec-name>`. If conflict, report and preserve.

### File Structure

```
project/
├── .worktrees/              ← Created at runtime, gitignored
│   └── add-auth-flow/       ← Isolated copy for this spec execution
└── scripts/
    ├── worktree-create.sh   ← Creates spec worktree
    └── worktree-merge.sh    ← Merges and cleans up worktree
```

> **Note:** `.worktrees/` is gitignored. Worktrees are ephemeral — created during spec execution and removed after merging. They should not persist across sessions.

### When to Use Worktree Isolation

Worktree isolation is **always used** for spec execution. It is the default operating mode for the team-lead agent.

This enables **multi-spec parallelism**: run two specs in separate terminals, each with its own worktree, without conflicts. This replaces the previous multi-builder parallelism model which was complex and error-prone.

## Customization

### Adding a New Team Member

Create two files in `.kiro/agents/`:

**tester.json**:
```json
{
  "name": "tester",
  "description": "Writes and runs tests for completed features.",
  "prompt": "file://./tester-prompt.md",
  "tools": ["read", "write", "shell"],
  "model": "claude-sonnet-4"
}
```

**tester-prompt.md**:
```markdown
# Tester

## Purpose
You write tests for completed features. You create test files and run them.

## Instructions
- Read the implementation files to understand what to test
- Write test files covering happy path and edge cases
- Run the tests and report results
- Do NOT modify implementation code
```

Then update team-lead.json:

```json
"toolsSettings": {
  "subagent": {
    "trustedAgents": ["builder", "validator", "tester"]
  }
}
```

### Changing the Model

Each agent can use a different model:

```json
"model": "claude-sonnet-4"
```

### Modifying the Plan Format

Edit `.kiro/skills/plan-with-team/SKILL.md` to change what the planning skill generates. The team lead reads the plan as plain text, so any structured markdown format works — just keep it consistent.

## Comparison with Claude Code

This project is a port of the [claude-code-hooks-mastery](https://github.com/anthropics/claude-code-hooks-mastery) team orchestration pattern. There are significant differences in how the two systems work:

| Capability | Claude Code | Kiro CLI |
|---|---|---|
| Task list | `TaskCreate/Update/List/Get` — shared, all agents read/write | `todo` — team-lead only, subagents cannot access |
| Spawn child agent | `Task` tool with `run_in_background`, `resume`, per-task `model` | `subagent` tool, up to 4 parallel, no resume |
| Agent definitions | `.claude/agents/*.md` (YAML frontmatter, subdirs work) | `.kiro/agents/*.json` + `*-prompt.md` (flat directory only) |
| Slash commands | `.claude/commands/*.md` with arguments | `.kiro/skills/*/SKILL.md` (skills preserve user's full message as input) |
| Post-tool hooks | Python scripts in `.claude/hooks/` | `hooks` field in agent JSON config |
| Subagent tools | Full tool access | Limited: read, write, shell, MCP only |

The biggest difference is task coordination. In Claude Code, builders call `TaskGet` to read their assignment and `TaskUpdate` to mark it complete — it's a truly shared board. In Kiro CLI, the team-lead is the sole coordinator: it dispatches work, receives results, and updates the TODO list itself. Subagents are blind to the task list.

## Command Reference

| Command | What It Does |
|---------|-------------|
| `@plan-with-team` | Activate the planning prompt — provide your task inline: `@plan-with-team <task>` |
| `/agent swap` | Switch between agents (select team-lead) |
| `/agent list` | List available agents |
| `/read <file>` | Read a file in the chat |
| `/todo` | View current TODO list (main session only) |

## Troubleshooting

**"Agent not found" when team-lead tries to spawn builder**
- All agent JSON files must be directly in `.kiro/agents/` — subdirectories don't work for subagent resolution
- Verify the agent name in `trustedAgents` matches the JSON filename (without `.json`)

**"Agent not found" when switching to team-lead**
- Verify `.kiro/agents/team-lead.json` exists in your project root
- Check the JSON is valid: `cat .kiro/agents/team-lead.json | python3 -m json.tool`

**Plan skill writes code instead of just creating a plan**
- Verify `.kiro/skills/plan-with-team/SKILL.md` contains the `PLANNING ONLY` instruction
- The skill should only output a spec file to `specs/`

**Builder can't write files**
- Ensure builder.json includes `"write"` in the `tools` array
- Only `read`, `write`, `shell`, and MCP tools are available in subagent runtime

**TODO list not working**
- Enable it: `kiro-cli settings chat.enableTodoList true`
- Restart Kiro CLI after changing settings
- Remember: only the team-lead (main session) can access it, not subagents

## Subagent Limitations

Tools NOT available in the subagent runtime (per [Kiro docs](https://kiro.dev/docs/cli/chat/subagents#tool-availability)):

- `todo` — task tracking
- `web_search` / `web_fetch` — web access
- `use_aws` — AWS commands
- `introspect` — CLI info
- `thinking` — reasoning tool

> **Note:** `grep` and `glob` ARE available in subagents when explicitly configured in the agent's `tools` array (as done for the validator agent).

If your agent config includes unavailable tools, they'll be silently unavailable when the agent runs as a subagent.

## Requirements

- Kiro CLI 2.0+ (skills, TUI, headless mode support)
- Optional — enable TODO list for team-lead task tracking:
  ```bash
  kiro-cli settings chat.enableTodoList true
  ```

## Agent Validation & Evaluation

### Comparative Evaluation (kiro-team vs kiro-default)

Compare when multi-agent orchestration outperforms standard single-agent mode:

```bash
# Run all comparative scenarios
cd evals/comparative
bash runners/run-comparison.sh scenarios/simple-bugfix.yaml
bash runners/run-comparison.sh scenarios/multi-file-refactor.yaml
bash runners/run-comparison.sh scenarios/ambiguous-feature.yaml
```

Results go to `evals/comparative/results/<scenario>/` with metrics and acceptance scores.

**Current findings** (3 scenarios tested):

| Scenario | Complexity | kiro-default | kiro-team | Winner |
|----------|------------|--------------|-----------|--------|
| simple-bugfix | Low | 100% (21s) | 100% (51s) | kiro-default |
| multi-file-refactor | Medium | 100% (58s) | 100% (158s) | kiro-default |
| ambiguous-feature | Medium | 100% (29s) | 33% (29s) | kiro-default |

**Key insight**: kiro-team's clarification protocol (asking questions before acting) hurts in automated/fire-and-forget scenarios. kiro-default makes reasonable assumptions and proceeds, which scores higher in evals where no human responds.

**When to prefer kiro-team**:
- Interactive sessions where humans can answer clarifying questions
- Very complex tasks with many dependencies
- Tasks requiring specialized knowledge across multiple domains

**When to prefer kiro-default**:
- Automated pipelines (CI/CD, cron jobs)
- Well-defined tasks with clear acceptance criteria
- Fire-and-forget scenarios

See `evals/comparative/results/SUMMARY.md` for full analysis.

### Static Validation

Run 67 static checks on agent configs before committing:

```bash
bash scripts/validate-agents.sh
```

Checks include:
- JSON syntax and schema validation
- Prompt file existence and structure
- Tool configuration consistency
- Required fields presence

### Behavioral Evaluation

Run behavioral scenarios to test agent judgment:

```bash
# List available scenarios
bash scripts/run-evals.sh --all

# Run specific agent's scenarios
bash scripts/run-evals.sh --agent builder

# Run single scenario
bash scripts/run-evals.sh builder/ambiguous-config
```

14 scenarios total, including 4 adversarial tests:
- `builder/ambiguous-config` — handling vague requirements
- `builder/conflicting-constraints` — recognizing contradictions
- `validator/temptation-trap-fix` — read-only discipline when fix is obvious
- `documenter/incomplete-source` — not inventing features from TODOs

### Pre-push Hook

Install the validation hook to catch issues before push:

```bash
bash scripts/install-hooks.sh
```

This runs `validate-agents.sh` automatically on every `git push`.

## Contributing

Before publishing changes:

1. Run validation:
   ```bash
   bash scripts/validate-agents.sh
   ```

2. For significant changes, run evals:
   ```bash
   bash scripts/run-evals.sh --all
   ```


## License

MIT
