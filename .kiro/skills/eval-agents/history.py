#!/usr/bin/env python3
"""
Evaluation history management for kiro-team.

Stores results per commit, enables comparison over time.

Usage:
    python history.py record <scenario-id> <score> [--breakdown '{"cat":n}']
    python history.py show [--last N]
    python history.py report [--format md|json]
    python history.py trend <scenario-id> [--last N]
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


HISTORY_DIR = Path(__file__).parent.parent.parent / "evals" / "history"


def get_commit_hash() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except:
        return "unknown"


def get_commit_date() -> str:
    """Get current commit date."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()[:10]  # YYYY-MM-DD
    except:
        return datetime.now().strftime("%Y-%m-%d")


def get_history_file() -> Path:
    """Get path to current history file (one per day)."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now().strftime("%Y-%m-%d")
    commit = get_commit_hash()
    return HISTORY_DIR / f"{date}-{commit}.json"


def load_history(path: Path = None) -> dict:
    """Load history from file."""
    if path is None:
        path = get_history_file()
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {
        "date": datetime.now().isoformat(),
        "commit": get_commit_hash(),
        "scenarios": {}
    }


def save_history(data: dict, path: Path = None):
    """Save history to file."""
    if path is None:
        path = get_history_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def record_result(scenario_id: str, score: int, breakdown: dict = None):
    """Record a scenario result."""
    history = load_history()
    
    history["scenarios"][scenario_id] = {
        "score": score,
        "timestamp": datetime.now().isoformat(),
        "passed": score >= 80
    }
    if breakdown:
        history["scenarios"][scenario_id]["breakdown"] = breakdown
    
    save_history(history)
    print(f"Recorded: {scenario_id} = {score} ({'PASS' if score >= 80 else 'FAIL'})")
    return history


def list_history_files() -> list[Path]:
    """List all history files, newest first."""
    if not HISTORY_DIR.exists():
        return []
    files = list(HISTORY_DIR.glob("*.json"))
    # Sort by filename (date-commit format)
    return sorted(files, reverse=True)


def show_history(last_n: int = 10):
    """Show recent evaluation history."""
    files = list_history_files()[:last_n]
    
    if not files:
        print("No evaluation history found.")
        return
    
    print(f"Last {len(files)} evaluation runs:\n")
    
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        
        scenarios = data.get("scenarios", {})
        total = len(scenarios)
        passed = sum(1 for s in scenarios.values() if s.get("passed", False))
        avg = sum(s.get("score", 0) for s in scenarios.values()) / total if total else 0
        
        print(f"{f.stem}:")
        print(f"  Scenarios: {passed}/{total} passed, avg {avg:.0f}%")
        for sid, result in scenarios.items():
            status = "✅" if result.get("passed") else "❌"
            print(f"    {status} {sid}: {result.get('score', '?')}")
        print()


def generate_report(format: str = "md") -> str:
    """Generate evaluation report."""
    history = load_history()
    scenarios = history.get("scenarios", {})
    
    if not scenarios:
        return "No scenarios evaluated yet."
    
    total = len(scenarios)
    passed = sum(1 for s in scenarios.values() if s.get("passed", False))
    failed = total - passed
    avg = sum(s.get("score", 0) for s in scenarios.values()) / total if total else 0
    
    if format == "json":
        return json.dumps({
            "date": history.get("date"),
            "commit": history.get("commit"),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "average": round(avg, 1)
            },
            "scenarios": scenarios
        }, indent=2)
    
    # Markdown format
    lines = [
        "# Evaluation Report",
        "",
        f"**Date**: {history.get('date', 'unknown')[:19]}",
        f"**Commit**: {history.get('commit', 'unknown')}",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total scenarios | {total} |",
        f"| Passed | {passed} |",
        f"| Failed | {failed} |",
        f"| Average score | {avg:.0f}% |",
        "",
        "## Results",
        "",
        "| Scenario | Score | Status |",
        "|----------|-------|--------|",
    ]
    
    for sid, result in sorted(scenarios.items()):
        score = result.get("score", 0)
        status = "✅ PASS" if result.get("passed") else "❌ FAIL"
        lines.append(f"| {sid} | {score}% | {status} |")
    
    # Detailed breakdowns if available
    has_breakdown = any("breakdown" in s for s in scenarios.values())
    if has_breakdown:
        lines.extend(["", "## Detailed Breakdown", ""])
        for sid, result in sorted(scenarios.items()):
            if "breakdown" in result:
                lines.append(f"### {sid}")
                lines.append("")
                lines.append("| Category | Score | Max |")
                lines.append("|----------|-------|-----|")
                for cat, val in result["breakdown"].items():
                    if isinstance(val, dict):
                        lines.append(f"| {cat} | {val.get('score', 0)} | {val.get('max', '?')} |")
                    else:
                        lines.append(f"| {cat} | {val} | - |")
                lines.append("")
    
    return "\n".join(lines)


def show_trend(scenario_id: str, last_n: int = 10):
    """Show score trend for a scenario over time."""
    files = list_history_files()[:last_n]
    
    if not files:
        print("No history found.")
        return
    
    print(f"Trend for {scenario_id} (last {len(files)} runs):\n")
    
    scores = []
    for f in reversed(files):  # Oldest first
        with open(f) as fh:
            data = json.load(fh)
        
        if scenario_id in data.get("scenarios", {}):
            score = data["scenarios"][scenario_id].get("score", 0)
            scores.append((f.stem, score))
    
    if not scores:
        print(f"No history for scenario: {scenario_id}")
        return
    
    # Simple ASCII chart
    max_score = max(s[1] for s in scores)
    for date, score in scores:
        bar = "█" * (score // 5)
        trend = ""
        print(f"{date[:10]}: {bar} {score}%")
    
    # Calculate trend
    if len(scores) >= 2:
        first = scores[0][1]
        last = scores[-1][1]
        diff = last - first
        if diff > 5:
            print(f"\n⬆️ Improving (+{diff} points)")
        elif diff < -5:
            print(f"\n⬇️ Regressing ({diff} points)")
        else:
            print(f"\n➡️ Stable")


def main():
    parser = argparse.ArgumentParser(description="Manage evaluation history")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record a result")
    record_parser.add_argument("scenario_id", help="Scenario ID")
    record_parser.add_argument("score", type=int, help="Score (0-100)")
    record_parser.add_argument("--breakdown", help="JSON breakdown dict")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show history")
    show_parser.add_argument("--last", type=int, default=10, help="Number of runs")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--format", choices=["md", "json"], default="md")
    
    # Trend command
    trend_parser = subparsers.add_parser("trend", help="Show trend")
    trend_parser.add_argument("scenario_id", help="Scenario ID")
    trend_parser.add_argument("--last", type=int, default=10, help="Number of runs")
    
    args = parser.parse_args()
    
    if args.command == "record":
        breakdown = json.loads(args.breakdown) if args.breakdown else None
        record_result(args.scenario_id, args.score, breakdown)
    
    elif args.command == "show":
        show_history(args.last)
    
    elif args.command == "report":
        print(generate_report(args.format))
    
    elif args.command == "trend":
        show_trend(args.scenario_id, args.last)


if __name__ == "__main__":
    main()
