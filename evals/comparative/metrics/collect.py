#!/usr/bin/env python3
"""
Collect metrics from kiro-cli logs for comparison.

Extracts:
- Token usage (input/output)
- Wall-clock time
- Tool calls count
- Errors/retries
"""

import argparse
import json
import re
from pathlib import Path


def parse_kiro_log(log_dir: Path) -> dict:
    """Parse kiro-cli log files and extract metrics."""
    metrics = {
        "tokens_input": 0,
        "tokens_output": 0,
        "tokens_total": 0,
        "duration_seconds": 0,
        "tool_calls": 0,
        "errors": 0,
        "retries": 0,
    }
    
    # Read duration
    duration_file = log_dir / "duration.txt"
    if duration_file.exists():
        metrics["duration_seconds"] = int(duration_file.read_text().strip())
    
    # Parse kiro.log for token usage
    kiro_log = log_dir / "kiro.log"
    if kiro_log.exists():
        content = kiro_log.read_text()
        
        # Token patterns (adjust based on actual kiro-cli log format)
        # Example: "tokens: input=1234 output=567"
        token_matches = re.findall(
            r'tokens?[:\s]+input[=:\s]+(\d+)[,\s]+output[=:\s]+(\d+)',
            content, re.IGNORECASE
        )
        for inp, out in token_matches:
            metrics["tokens_input"] += int(inp)
            metrics["tokens_output"] += int(out)
        
        # Alternative format: "usage: 1234 input, 567 output"
        alt_matches = re.findall(
            r'usage[:\s]+(\d+)\s+input[,\s]+(\d+)\s+output',
            content, re.IGNORECASE
        )
        for inp, out in alt_matches:
            metrics["tokens_input"] += int(inp)
            metrics["tokens_output"] += int(out)
        
        # Count tool calls
        metrics["tool_calls"] = len(re.findall(r'tool[_\s]call|execute_bash|fs_write|fs_read', content, re.IGNORECASE))
        
        # Count errors
        metrics["errors"] = len(re.findall(r'error|failed|exception', content, re.IGNORECASE))
        
        # Count retries
        metrics["retries"] = len(re.findall(r'retry|retrying|attempt \d+', content, re.IGNORECASE))
    
    # Parse output.log for additional signals
    output_log = log_dir / "output.log"
    if output_log.exists():
        content = output_log.read_text()
        
        # Look for token summaries in output
        summary_match = re.search(
            r'total[:\s]+(\d+)\s+tokens?',
            content, re.IGNORECASE
        )
        if summary_match and metrics["tokens_total"] == 0:
            metrics["tokens_total"] = int(summary_match.group(1))
    
    # Calculate total if not found directly
    if metrics["tokens_total"] == 0:
        metrics["tokens_total"] = metrics["tokens_input"] + metrics["tokens_output"]
    
    return metrics


def main():
    parser = argparse.ArgumentParser(description="Collect comparison metrics")
    parser.add_argument("--scenario", required=True, help="Scenario YAML file")
    parser.add_argument("--default-logs", required=True, help="kiro-default log directory")
    parser.add_argument("--team-logs", required=True, help="kiro-team log directory")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()
    
    # Load scenario metadata
    import yaml
    with open(args.scenario) as f:
        scenario = yaml.safe_load(f)
    
    # Collect metrics from both approaches
    default_metrics = parse_kiro_log(Path(args.default_logs))
    team_metrics = parse_kiro_log(Path(args.team_logs))
    
    # Calculate comparisons
    token_diff = team_metrics["tokens_total"] - default_metrics["tokens_total"]
    token_ratio = (
        team_metrics["tokens_total"] / default_metrics["tokens_total"]
        if default_metrics["tokens_total"] > 0 else 0
    )
    
    time_diff = team_metrics["duration_seconds"] - default_metrics["duration_seconds"]
    time_ratio = (
        team_metrics["duration_seconds"] / default_metrics["duration_seconds"]
        if default_metrics["duration_seconds"] > 0 else 0
    )
    
    result = {
        "scenario": {
            "id": scenario["id"],
            "name": scenario["name"],
            "complexity": scenario.get("complexity", "unknown"),
            "expected_winner": scenario.get("expected_winner", "unknown"),
        },
        "kiro_default": default_metrics,
        "kiro_team": team_metrics,
        "comparison": {
            "token_diff": token_diff,
            "token_ratio": round(token_ratio, 2),
            "token_winner": "kiro-default" if token_diff > 0 else "kiro-team",
            "time_diff_seconds": time_diff,
            "time_ratio": round(time_ratio, 2),
            "time_winner": "kiro-default" if time_diff > 0 else "kiro-team",
        }
    }
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Metrics saved to {output_path}")
    print(f"  Tokens: kiro-default={default_metrics['tokens_total']}, kiro-team={team_metrics['tokens_total']} ({token_ratio:.1f}x)")
    print(f"  Time:   kiro-default={default_metrics['duration_seconds']}s, kiro-team={team_metrics['duration_seconds']}s ({time_ratio:.1f}x)")


if __name__ == "__main__":
    main()
