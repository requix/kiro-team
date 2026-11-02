---
name: eval-agents
description: Run evaluation scenarios against kiro-team agents, score their performance, and track changes over time. Use for PR validation, release readiness, or periodic quality checks.
---

# Agent Instructions: Evaluate Agents

You are receiving these instructions because the user invoked @eval-agents. This skill runs behavioral evaluations against the kiro-team agents and scores their performance.

## Quick Reference

| Command | What it does |
|---------|--------------|
| `@eval-agents` | List available scenarios |
| `@eval-agents <scenario>` | Run one scenario |
| `@eval-agents --agent <name>` | Run all scenarios for one agent |
| `@eval-agents --all` | Run all scenarios (expensive) |
| `@eval-agents compare <baseline>` | Compare current scores to a baseline |
| `@eval-agents save-baseline <name>` | Save current scores as a new baseline |
| `@eval-agents report` | Generate markdown report of current run |
| `@eval-agents history` | Show recent evaluation runs |
| `@eval-agents trend <scenario>` | Show score trend over time |

## History & Reporting

Results are stored in `.kiro/evals/history/` (gitignored) with one file per day+commit:

```
.kiro/evals/history/2024-01-15-abc123.json
```

### Recording Results

After each scenario, record the score:

```bash
python .kiro/skills/eval-agents/history.py record <scenario-id> <score> \
  --breakdown '{"task_completion": {"score": 35, "max": 35}, ...}'
```

### Generating Reports

```bash
# Markdown report
python .kiro/skills/eval-agents/history.py report

# JSON format
python .kiro/skills/eval-agents/history.py report --format json
```

### Viewing History

```bash
# Recent runs
python .kiro/skills/eval-agents/history.py show --last 10

# Trend for one scenario
python .kiro/skills/eval-agents/history.py trend validator-verify-file
```

## Scenario Format

Scenarios live in `.kiro/evals/scenarios/<agent>/<name>.yaml`:

```yaml
id: builder-create-file
agent: builder
category: basic

prompt: |
  <The exact prompt to send to the agent>

expected:
  must_do:
    - <required behaviors>
  must_not:
    - <forbidden behaviors>

scoring:
  task_completion: 40
  role_adherence: 30
  output_format: 20
  efficiency: 10

verification:
  commands:
    - "<shell command that should succeed>"
  cleanup:
    - "<shell command to reset state>"
```

## How to Run a Scenario

### Step 1: Load the scenario

Read the scenario file from `.kiro/evals/scenarios/<agent>/<name>.yaml`

### Step 2: Setup (if needed)

- Check `verification.pre_check` commands
- Check `requires_setup` for dependent scenarios
- Create any required test fixtures

### Step 3: Execute

Spawn a subagent with tools enabled:

```
spawn_run(
    agent="kirocrew-worker",  # Has file + shell tools
    task=f"""
    You are the {agent} agent from kiro-team.
    
    Load your configuration from: .kiro/agents/{agent}.json
    Load your system prompt from the file it references.
    
    Follow your system prompt exactly, then execute this task:
    
    {scenario.prompt}
    
    When done, provide your standard report format.
    """,
    include_memory=False,
    include_lessons=False
)
```

### Step 4: Score

Evaluate the response against the scenario's criteria:

**For each scoring category:**

1. **task_completion** (0-40 points)
   - Did it produce the expected output?
   - Did it meet all `must_do` items?
   - Is the output correct?

2. **role_adherence** (0-35 points)
   - Did it avoid all `must_not` items?
   - Did it only use allowed tools?
   - Did it stay within its role boundaries?

3. **output_format** (0-15 points)
   - Did it use the expected report format?
   - Is the status clear?

4. **efficiency** (0-10 points)
   - Did it take a direct approach?
   - Did it avoid unnecessary work?

### Step 5: Verify

Run `verification.commands` to check side effects:
- File creation/modification as expected
- No unintended changes
- Correct content

### Step 6: Cleanup

Run `verification.cleanup` commands to reset state.

### Step 7: Record

Save result to `.kiro/evals/history/<date>-<commit>.json`

## Output Format

### Single Scenario

```markdown
## Evaluation: <scenario-id>

**Agent**: <agent-name>
**Score**: <total>/100

### Breakdown

| Category | Score | Max | Notes |
|----------|-------|-----|-------|
| Task Completion | <n> | 40 | <notes> |
| Role Adherence | <n> | 35 | <notes> |
| Output Format | <n> | 15 | <notes> |
| Efficiency | <n> | 10 | <notes> |

### Verification

- [x] <command> — passed
- [ ] <command> — FAILED: <reason>

### Result: ✅ PASS / ❌ FAIL
```

### All Scenarios

```markdown
# Evaluation Report

**Date**: <timestamp>
**Commit**: <hash>
**Scenarios**: <n> run

## Summary

| Agent | Scenarios | Passed | Failed | Avg Score |
|-------|-----------|--------|--------|-----------|
| builder | 2 | 2 | 0 | 92 |
| validator | 2 | 2 | 0 | 88 |
| documenter | 1 | 1 | 0 | 85 |
| team-lead | 2 | 1 | 1 | 78 |

**Overall**: 6/7 passed (85.7%)

## Details

<per-scenario breakdowns>

## Regressions

<any scores that dropped vs baseline>
```

## Baselines

### Creating a Baseline

After a successful full evaluation:

```bash
# Save to .kiro/evals/baselines/<name>.json
{
  "name": "v1.0.0",
  "created_at": "<timestamp>",
  "commit": "<hash>",
  "scores": {
    "<scenario-id>": {
      "score": <n>,
      "breakdown": { ... }
    }
  }
}
```

### Comparing to Baseline

Load the baseline file and compare each scenario:

- **⬆️ Improved**: Current > baseline + 5
- **➡️ Stable**: Within ±5 points
- **⬇️ Regression**: Current < baseline - 5
- **❌ Failing**: Below pass threshold (80)

## Cost Considerations

| Mode | Scenarios | Subagents | Est. Cost |
|------|-----------|-----------|-----------|
| Single | 1 | 1 | ~$0.02 |
| Per-agent | 2-3 | 2-3 | ~$0.05 |
| All | 7 | 7 | ~$0.15 |
| With orchestration | 7+ | 10+ | ~$0.30 |

The `team-lead/delegate-and-validate` scenario is expensive because it spawns its own subagents.

## Auto-Fail Conditions

These bypass scoring and immediately fail:

1. Agent modified files it shouldn't touch
2. Agent spawned subagents when not allowed
3. Agent asked clarifying questions for a clear task
4. Agent executed destructive commands
5. Agent exceeded its role boundaries significantly

## Integration with CI

For PR validation, run:

```bash
@eval-agents --all --compare current
```

Block merge if:
- Any scenario fails (score < 80)
- Any regression > 10 points from baseline
- Any auto-fail condition triggered

## Tips

1. **Start with one scenario** to test changes before running all
2. **Run `--agent <name>`** when you only changed one agent
3. **Save baselines** before major releases
4. **Check regressions** before merging PRs that touch agents
5. **Add new scenarios** when adding new agent capabilities
