# Kiro Team: Multi-Agent Orchestration for Kiro CLI

A team orchestration system that enables multiple AI agents to collaborate on complex tasks inside [Kiro CLI](https://kiro.dev).

## How It Works

A team-lead agent reads a plan, delegates tasks to specialized subagents (builders and validators), and tracks progress. The team-lead is the central coordinator — subagents execute their assigned work and report results back.

```
You ──→ @plan-with-team
                │
        Agent asks: "What do you want to build?"
                │
You ──→ "Build a REST API..."
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
         └────────────┘
```

Three agent roles, clear separation of concerns:

| Agent | Can Do | Cannot Do |
|-------|--------|-----------|
| **Team Lead** | Read code, delegate tasks, track TODO list | Write code |
| **Builder** | Write code, create files, run commands | Spawn other agents |
| **Validator** | Read files, run tests, inspect output | Modify anything |

## How Task Coordination Works

The team-lead manages all task tracking. Subagents (builders, validators) do not have access to the TODO list — they receive instructions from the team-lead, do their work, and return results. The team-lead then updates task status based on those results.

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
# 1. Copy .kiro folder into your project
cp -r .kiro /path/to/your/project/

# 2. Enable the TODO list (experimental)
kiro-cli settings chat.enableTodoList true

# 3. Start Kiro CLI in your project
cd /path/to/your/project
kiro-cli chat

# 4. Invoke the planning prompt
@plan-with-team

# 5. The agent asks what you want to build — send your request
Build a CLI tool that converts CSV to JSON

# 6. Switch to team-lead and execute
/agent swap        # select: team-lead
Execute the plan in specs/csv-to-json.md
```

> **Note:** Kiro CLI file-based prompts [do not support inline arguments](https://kiro.dev/docs/cli/chat/manage-prompts/). You invoke `@plan-with-team` first, then the agent asks for your task description in a follow-up message.

## Phases

### Phase 1: Planning

The `@plan-with-team` prompt activates the planning agent. It only creates a plan — no code is written.

```bash
@plan-with-team
# Agent responds: "What would you like to build?"

Add user authentication with JWT tokens
```

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
8. Reports results

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

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Kiro CLI Process                        │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                   Agent Layer                         │  │
│  │                                                       │  │
│  │  ┌─────────────┐                                      │  │
│  │  │ Default     │  @plan-with-team prompt              │  │
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
│   └── validator-prompt.md     ← Validator behavior
└── prompts/
    └── plan-with-team.md       ← Planning prompt (invoked with @)
```

> **Note:** All agent configs must be directly in `.kiro/agents/` — subdirectories are not supported for subagent resolution.

### Agent Configuration

Each agent is defined by a JSON config + a markdown prompt:

**team-lead.json** — the orchestrator:
```json
{
  "name": "team-lead",
  "tools": ["read", "subagent", "todo"],
  "allowedTools": ["read", "subagent", "todo"],
  "toolsSettings": {
    "subagent": {
      "trustedAgents": ["builder", "validator"]
    }
  },
  "model": "claude-sonnet-4"
}
```

Key points:
- Has `subagent` tool to spawn builders and validators
- Does NOT have `write` or `shell` — cannot modify files directly
- Can use `todo` tool for task tracking (experimental, enable separately)
- `trustedAgents` allows spawning without permission prompts each time


**builder.json** — the implementer:
```json
{
  "name": "builder",
  "tools": ["read", "write", "shell"],
  "allowedTools": ["read", "write", "shell"],
  "model": "claude-sonnet-4"
}
```

Key points:
- Has `read`,`write` and `shell` — can create/modify files and run commands
- Does NOT have `subagent` — cannot spawn other agents

**validator.json** — the verifier:
```json
{
  "name": "validator",
  "tools": ["read", "shell"],
  "toolsSettings": {
    "shell": { "autoAllowReadonly": true }
  },
  "model": "claude-sonnet-4"
}
```

Key points:
- Has `read` and `shell` (read-only) — can inspect but not modify
- Does NOT have `write` — cannot change files
- Shell is auto-allowed for read-only commands

### Design Principles

Each agent gets only the tools it needs (least privilege):

```
Team Lead:  read, subagent (+ todo in main session)
            ↑ can read and delegate, but CANNOT write files

Builder:    read, write, shell
            ↑ can modify files, but CANNOT spawn agents

Validator:  read, shell (read-only)
            ↑ can inspect, but CANNOT modify anything
```

## Kiro CLI Features Used

| Feature | What It Does Here |
|---------|-------------------|
| [Custom Agents](https://kiro.dev/docs/cli/custom-agents) | Define team-lead, builder, validator with specific tools |
| [Subagents](https://kiro.dev/docs/cli/chat/subagents) | Team lead spawns builders/validators as child agents |
| [Prompts](https://kiro.dev/docs/cli/chat/manage-prompts) | `@plan-with-team` reusable planning template |
| [TODO Lists](https://kiro.dev/docs/cli/experimental/todo-lists) | Team-lead tracks task progress (not accessible to subagents) |

## Walkthrough: Building a Calculator API

### Step 1: Create the Plan

```bash
$ cd my-project
$ kiro-cli chat
```

```
> @plan-with-team
```

The agent asks what you want to build. Send your request:

```
> Build a REST API with endpoints for add, subtract, multiply, divide
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

Edit `.kiro/prompts/plan-with-team.md` to change what the planning prompt generates. The team lead reads the plan as plain text, so any structured markdown format works — just keep it consistent.

## Comparison with Claude Code

This project is a port of the [claude-code-hooks-mastery](https://github.com/anthropics/claude-code-hooks-mastery) team orchestration pattern. There are significant differences in how the two systems work:

| Capability | Claude Code | Kiro CLI |
|---|---|---|
| Task list | `TaskCreate/Update/List/Get` — shared, all agents read/write | `todo` — team-lead only, subagents cannot access |
| Spawn child agent | `Task` tool with `run_in_background`, `resume`, per-task `model` | `subagent` tool, up to 4 parallel, no resume |
| Agent definitions | `.claude/agents/*.md` (YAML frontmatter, subdirs work) | `.kiro/agents/*.json` + `*-prompt.md` (flat directory only) |
| Slash commands | `.claude/commands/*.md` with arguments | `.kiro/prompts/*.md` (no inline arguments) |
| Post-tool hooks | Python scripts in `.claude/hooks/` | `hooks` field in agent JSON config |
| Subagent tools | Full tool access | Limited: read, write, shell, MCP only |

The biggest difference is task coordination. In Claude Code, builders call `TaskGet` to read their assignment and `TaskUpdate` to mark it complete — it's a truly shared board. In Kiro CLI, the team-lead is the sole coordinator: it dispatches work, receives results, and updates the TODO list itself. Subagents are blind to the task list.

## Command Reference

| Command | What It Does |
|---------|-------------|
| `@plan-with-team` | Activate the planning prompt (then send your request) |
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

**Plan prompt writes code instead of just creating a plan**
- Verify `.kiro/prompts/plan-with-team.md` contains the `**PLANNING ONLY**` instruction
- The prompt should only output a spec file to `specs/`

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
- `grep` — search file contents
- `glob` — find files by pattern
- `web_search` / `web_fetch` — web access
- `use_aws` — AWS commands
- `introspect` — CLI info
- `thinking` — reasoning tool

If your agent config includes these tools, they'll be silently unavailable when the agent runs as a subagent.

## Requirements

- Kiro CLI 1.23+ (subagents support)
- Optional — enable TODO list for team-lead task tracking:
  ```bash
  kiro-cli settings chat.enableTodoList true
  ```

## License

MIT
