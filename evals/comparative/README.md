# Comparative Evaluations

Compare **kiro-team** (multi-agent) vs **kiro-default** (standard kiro-cli) on identical tasks.

## Purpose

Answer: "When is kiro-team worth the orchestration overhead?"

## What We Measure

| Metric | Description | How |
|--------|-------------|-----|
| **Quality** | Did it meet spec? Correct? Complete? | Acceptance checks (see below) |
| **Cost** | Credits billed by kiro-cli | `meteringUsage` events in `output.log` |
| **Tokens** | Input + output, when the backend reports them | `inputTokens` / `outputTokens` in `output.log` |
| **Time** | Wall-clock start to done | `duration.txt` |
| **Exit code** | Did kiro-cli finish cleanly? | `exit_code.txt` |
| **Scope** | Stayed on task or drifted? | Manual review |

kiro-cli bills in credits and usually does not report token counts, so credits are the cost metric. A metric with no data is recorded as `null` and the comparison says `n/a`. It never counts as 0, so a missing log can't look like a cheap run.

## Structure

```
comparative/
├── scenarios/           # Task specs (identical for both approaches)
├── fixtures/            # Starting code for each scenario
├── checks/              # Behavioral checks that call the code under test
│   ├── timed_cache.py   # validation-trap
│   └── paginate.py      # validator-feedback
├── runners/
│   ├── common.sh            # Shared helpers (model check, kiro-cli wrapper)
│   ├── run-kiro-default.sh
│   ├── run-kiro-team.sh     # Uses the agents in this repo's .kiro/agents
│   └── run-comparison.sh    # Runs both, collects metrics
├── metrics/
│   ├── check_acceptance.py  # Scores a workspace against the scenario
│   ├── collect.py           # Parse logs into metrics.json
│   └── report.py            # Generate comparison report
├── tests/               # Tests for the harness itself
└── results/             # Output (gitignored)
```

## Scenario Format

```yaml
id: simple-bugfix
name: "Simple Bug Fix"
description: "Fix an off-by-one error in a single file"
complexity: low
expected_winner: kiro-default  # Hypothesis

task: |
  Fix the off-by-one error in src/counter.py.

fixture: fixtures/simple-bugfix/

acceptance:
  # Regex on a file: pattern must match, not_pattern must not
  - description: "Bug is fixed"
    file: src/counter.py
    not_pattern: "return len\\(items\\) \\+ 1"
  # Command run in the workspace with bash -o pipefail
  - description: "Tests pass"
    command: "python -m pytest tests/ -q"
    exit_code: 0
  # Counting command: output must be an int within bounds
  - description: "No unrelated changes"
    command: "git diff --name-only eval-base | wc -l"
    max_value: 1
```

Commands run inside the workspace. Two placeholders are available: `{workspace}` and `{checks}` (the `checks/` directory). The runner commits the fixture and tags it `eval-base`, so `git diff eval-base` shows everything the agent changed.

A command check fails if any step of its pipeline fails. The one exception is grep's "no match" (exit 1 with output `0`), which counts as a real zero.

## Writing Good Checks

Prefer checks that run the code over checks that grep it. A grep often matches the TODO comment that describes the task, so an agent that does nothing still scores. Check every new scenario against its untouched fixture:

```bash
python3 metrics/check_acceptance.py --scenario scenarios/<name>.yaml --baseline
```

The baseline should fail every check except "tests pass" style checks. The harness tests enforce this for every scenario.

## Running Comparisons

```bash
# Run single scenario on both approaches
./runners/run-comparison.sh scenarios/simple-bugfix.yaml

# Run all scenarios and write results/comparison-report.md
./runners/run-comparison.sh --all

# Pin a model for both approaches
./runners/run-comparison.sh --all --model claude-sonnet-4

# Regenerate the report from existing results
python3 metrics/report.py results/ > results/comparison-report.md
```

`run-kiro-team.sh` copies the agents from this repo's `.kiro/agents` into the workspace. It exits with an error if they are missing, instead of running some other agent.

## Testing the Harness

```bash
# From the repo root. Needs pyyaml and pytest; no kiro-cli needed.
python -m pytest evals/comparative/tests -q
```

The tests check that untouched fixtures score low, that reference solutions score 100%, that a cache without a lock fails the concurrency check, and that the collector and report handle missing data. A fake `kiro-cli` covers the runners.

## Expected Findings

| Scenario Type | Likely Winner | Why |
|---------------|---------------|-----|
| Simple, well-defined | kiro-default | Less orchestration overhead |
| Multi-file, coordinated | kiro-team | Better task decomposition |
| Ambiguous requirements | kiro-team | Validator catches drift |
| Subtle bugs (race, edge cases) | kiro-team | Validator runs the tests the builder skipped |
| Large codebase navigation | kiro-team | Specialized agents |

## Adding a Scenario

1. Create `scenarios/<name>.yaml` with task + acceptance criteria
2. Add fixture files to `fixtures/<name>/` if needed
3. Run `./runners/run-comparison.sh scenarios/<name>.yaml`
4. Review results in `results/<name>/`
