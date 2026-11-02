# Evaluation Baselines

This directory stores known-good evaluation scores used for regression detection.

## Baseline Files

- `v1.0.0.json` — Baseline for version 1.0.0 release
- `current.json` — Current development baseline (updated periodically)

## File Format

```json
{
  "version": "1.0.0",
  "created_at": "2024-01-15T10:00:00Z",
  "commit": "abc123def",
  "scores": {
    "builder-create-file": {
      "score": 95,
      "breakdown": {
        "task_completion": 40,
        "role_adherence": 30,
        "output_format": 20,
        "efficiency": 5
      }
    },
    "validator-verify-file": { ... },
    ...
  },
  "summary": {
    "total_scenarios": 7,
    "passed": 7,
    "failed": 0,
    "average_score": 91.4
  }
}
```

## Creating a Baseline

Run a full evaluation and save results:

```bash
# Run all scenarios
@eval-agents full

# If all pass, save as baseline
@eval-agents save-baseline v1.1.0
```

## Comparing Against Baseline

```bash
@eval-agents compare v1.0.0
```

Output shows:
- ✅ Improved (score went up)
- ➡️ Stable (within ±5 points)
- ⚠️ Regression (score went down >5 points)
- ❌ Failing (below pass threshold)
