#!/usr/bin/env python3
"""
Collect metrics from runner logs for comparison.

The runners call `kiro-cli chat --output-format stream-json`, which writes the
run's ACP events to output.log as JSON Lines. This module reads that file:

- Cost: kiro-cli bills in credits, reported as `meteringUsage` entries with
  `unit == "credit"`. Credits are the cost signal.
- Tokens: read from `inputTokens` / `outputTokens` when a backend reports
  them. kiro-cli usually does not, so tokens are often absent.
- Tool calls: `tool_call` session updates.
- Wall-clock time: duration.txt, written by the runner.
- Exit status: exit_code.txt, written by the runner.

A metric with no data is recorded as null, never as 0, so a missing log can
never look like a cheap run. A comparison with missing data on either side
reports "n/a"; equal values report "tie".
"""

import argparse
import json
from pathlib import Path


def _walk(node):
    """Yield every dict nested anywhere in a parsed JSON value."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


def _number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if value >= 0 else None


def _read_int(path: Path) -> int | None:
    try:
        return int(path.read_text().strip())
    except (OSError, ValueError):
        return None


def parse_stream_log(output_log: Path) -> dict:
    """Read credits, tokens and tool calls from a stream-json log."""
    found = {"credits": None, "tokens_input": None, "tokens_output": None, "tool_calls": 0, "events": 0}
    if not output_log.exists():
        return found

    seen_tool_calls = set()
    for line in output_log.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        found["events"] += 1
        for node in _walk(event):
            metering = node.get("meteringUsage")
            if isinstance(metering, list):
                for entry in metering:
                    if isinstance(entry, dict) and entry.get("unit") == "credit":
                        value = _number(entry.get("value"))
                        if value is not None:
                            found["credits"] = (found["credits"] or 0.0) + value
            for key, field in (("inputTokens", "tokens_input"), ("outputTokens", "tokens_output")):
                value = _number(node.get(key))
                if value is not None:
                    found[field] = (found[field] or 0) + int(value)
            if node.get("sessionUpdate") == "tool_call":
                seen_tool_calls.add(node.get("toolCallId") or id(node))
    found["tool_calls"] = len(seen_tool_calls)
    return found


def parse_run(log_dir: Path) -> dict:
    """Collect every metric for one runner's log directory."""
    stream = parse_stream_log(log_dir / "output.log")
    tokens_total = None
    if stream["tokens_input"] is not None or stream["tokens_output"] is not None:
        tokens_total = (stream["tokens_input"] or 0) + (stream["tokens_output"] or 0)
    return {
        "exit_code": _read_int(log_dir / "exit_code.txt"),
        "duration_seconds": _read_int(log_dir / "duration.txt"),
        "credits": round(stream["credits"], 4) if stream["credits"] is not None else None,
        "tokens_input": stream["tokens_input"],
        "tokens_output": stream["tokens_output"],
        "tokens_total": tokens_total,
        "tool_calls": stream["tool_calls"],
        "log_events": stream["events"],
    }


def compare(default_value, team_value) -> dict:
    """Compare a lower-is-better metric. Missing data never picks a winner."""
    if default_value is None or team_value is None:
        return {"diff": None, "ratio": None, "winner": "n/a"}
    diff = team_value - default_value
    ratio = team_value / default_value if default_value > 0 else None
    if diff == 0:
        winner = "tie"
    else:
        winner = "kiro-default" if diff > 0 else "kiro-team"
    return {"diff": diff, "ratio": round(ratio, 2) if ratio is not None else None, "winner": winner}


def build_result(scenario: dict, default_metrics: dict, team_metrics: dict) -> dict:
    comparison = {}
    for name, key in (("credits", "credits"), ("tokens", "tokens_total"), ("time", "duration_seconds")):
        c = compare(default_metrics[key], team_metrics[key])
        comparison[f"{name}_diff"] = c["diff"]
        comparison[f"{name}_ratio"] = c["ratio"]
        comparison[f"{name}_winner"] = c["winner"]
    warnings = []
    for label, m in (("kiro-default", default_metrics), ("kiro-team", team_metrics)):
        if m["exit_code"] not in (0, None):
            warnings.append(f"{label} exited with code {m['exit_code']}")
        if m["log_events"] == 0:
            warnings.append(f"{label} output.log has no stream-json events")
        if m["credits"] is None and m["tokens_total"] is None:
            warnings.append(f"{label} has no cost data (credits or tokens)")
    return {
        "scenario": {
            "id": scenario["id"],
            "name": scenario["name"],
            "complexity": scenario.get("complexity", "unknown"),
            "expected_winner": scenario.get("expected_winner", "unknown"),
        },
        "kiro_default": default_metrics,
        "kiro_team": team_metrics,
        "comparison": comparison,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="Collect comparison metrics")
    parser.add_argument("--scenario", required=True, help="Scenario YAML file")
    parser.add_argument("--default-logs", required=True, help="kiro-default log directory")
    parser.add_argument("--team-logs", required=True, help="kiro-team log directory")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()

    import yaml
    with open(args.scenario) as f:
        scenario = yaml.safe_load(f)

    result = build_result(
        scenario,
        parse_run(Path(args.default_logs)),
        parse_run(Path(args.team_logs)),
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    d, t, c = result["kiro_default"], result["kiro_team"], result["comparison"]
    print(f"Metrics saved to {output_path}")
    print(f"  Credits: kiro-default={d['credits']}, kiro-team={t['credits']} (winner: {c['credits_winner']})")
    print(f"  Time:    kiro-default={d['duration_seconds']}s, kiro-team={t['duration_seconds']}s (winner: {c['time_winner']})")
    for w in result["warnings"]:
        print(f"  WARNING: {w}")


if __name__ == "__main__":
    main()
