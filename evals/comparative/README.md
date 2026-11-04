# Comparative Evaluations

Compare **kiro-team** (multi-agent) vs **kiro-default** (standard kiro-cli) on identical tasks.

## Purpose

Answer: "When is kiro-team worth the orchestration overhead?"

## What We Measure

| Metric | Description | How |
|--------|-------------|-----|
| **Quality** | Did it meet spec? Correct? Complete? | Rubric scoring |
| **Tokens** | Total input + output | Parse logs |
| **Time** | Wall-clock start to done | Timestamp diff |
| **Errors** | Validation failures, retries | Count in logs |
| **Scope** | Stayed on task or drifted? | Manual review |

## Structure

```
comparative/
├── scenarios/           # Task specs (identical for both approaches)
│   ├── simple-bugfix.yaml
│   ├── multi-file-refactor.yaml
│   └── ...
├── fixtures/            # Test repos/files for scenarios
├── runners/
│   ├── run-kiro-default.sh
│   ├── run-kiro-team.sh
│   └── run-comparison.sh   # Runs both, collects metrics
├── metrics/
│   ├── collect.py       # Parse logs → structured data
│   └── report.py        # Generate comparison report
└── results/             # Output reports (gitignored)
```

## Scenario Format

```yaml
# scenarios/example.yaml
id: simple-bugfix
name: "Simple Bug Fix"
description: "Fix an off-by-one error in a single file"
complexity: low
expected_winner: kiro-default  # Hypothesis

task: |
  Fix the off-by-one error in src/utils.py line 42.
  The loop should use `range(n)` not `range(n+1)`.

fixture: fixtures/bugfix-repo/

acceptance:
  - file: src/utils.py
    contains: "range(n)"
  - command: "python -m pytest tests/"
    exit_code: 0

metrics_focus:
  - tokens    # Primary metric for this scenario
  - time
```

## Running Comparisons

```bash
# Run single scenario on both approaches
./runners/run-comparison.sh scenarios/simple-bugfix.yaml

# Run all scenarios
./runners/run-comparison.sh --all

# Generate report
python metrics/report.py results/ > results/comparison-report.md
```

## Expected Findings

| Scenario Type | Likely Winner | Why |
|---------------|---------------|-----|
| Simple, well-defined | kiro-default | Less orchestration overhead |
| Multi-file, coordinated | kiro-team | Better task decomposition |
| Ambiguous requirements | kiro-team | Validator catches drift |
| Large codebase navigation | kiro-team | Specialized agents |

## Adding a Scenario

1. Create `scenarios/<name>.yaml` with task + acceptance criteria
2. Add fixture files to `fixtures/<name>/` if needed
3. Run `./runners/run-comparison.sh scenarios/<name>.yaml`
4. Review results in `results/<name>/`
