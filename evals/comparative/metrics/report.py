#!/usr/bin/env python3
"""
Generate a comparison report from all scenario results.

Outputs a markdown report summarizing:
- Per-scenario results
- Aggregate statistics
- Winner analysis
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime


def load_results(results_dir: Path) -> list:
    """Load all scenario results."""
    results = []
    
    for scenario_dir in sorted(results_dir.iterdir()):
        if not scenario_dir.is_dir():
            continue
        
        metrics_file = scenario_dir / "metrics.json"
        acceptance_file = scenario_dir / "acceptance.json"
        
        if not metrics_file.exists():
            continue
        
        with open(metrics_file) as f:
            metrics = json.load(f)
        
        acceptance = {}
        if acceptance_file.exists():
            with open(acceptance_file) as f:
                acceptance = json.load(f)
        
        results.append({
            "scenario_id": scenario_dir.name,
            "metrics": metrics,
            "acceptance": acceptance,
        })
    
    return results


WINNERS = ("kiro-default", "kiro-team", "tie", "n/a")


def fmt_pct(value) -> str:
    return f"{value:.0f}%" if isinstance(value, (int, float)) and not isinstance(value, bool) else "N/A"


def fmt_num(value, suffix: str = "") -> str:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "N/A"
    return f"{value:g}{suffix}"


def _tally(counter: dict, key) -> None:
    counter[key if key in counter else "n/a"] += 1


def generate_report(results: list) -> str:
    """Generate markdown report. Never raises on missing or partial data."""
    lines = [
        "# Comparative Evaluation Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
    ]

    total = len(results)
    credit_wins = dict.fromkeys(WINNERS, 0)
    time_wins = dict.fromkeys(WINNERS, 0)
    quality_wins = dict.fromkeys(WINNERS, 0)
    hypothesis_correct = 0
    hypothesis_scored = 0

    for r in results:
        comp = r["metrics"].get("comparison", {})
        _tally(credit_wins, comp.get("credits_winner", "n/a"))
        _tally(time_wins, comp.get("time_winner", "n/a"))
        acc = r.get("acceptance", {})
        actual = acc.get("quality_winner", "n/a")
        _tally(quality_wins, actual)
        expected = r["metrics"].get("scenario", {}).get("expected_winner", "")
        if actual != "n/a":
            hypothesis_scored += 1
            hypothesis_correct += expected == actual

    def row(name, wins):
        return f"| {name} | {wins['kiro-default']} | {wins['kiro-team']} | {wins['tie']} | {wins['n/a']} |"

    accuracy = (
        f"{hypothesis_correct}/{hypothesis_scored} ({hypothesis_correct / hypothesis_scored * 100:.0f}% correct)"
        if hypothesis_scored else "N/A (no acceptance data)"
    )
    lines.extend([
        f"**Scenarios evaluated:** {total}",
        "",
        "### Wins by Category",
        "",
        "| Category | kiro-default | kiro-team | Tie | No data |",
        "|----------|--------------|-----------|-----|---------|",
        row("Credits (fewer)", credit_wins),
        row("Time (faster)", time_wins),
        row("Quality (higher)", quality_wins),
        "",
        f"**Hypothesis accuracy:** {accuracy}",
        "",
        "---",
        "",
        "## Per-Scenario Results",
        "",
    ])

    for r in results:
        scenario = r["metrics"].get("scenario", {})
        default = r["metrics"].get("kiro_default", {})
        team = r["metrics"].get("kiro_team", {})
        comp = r["metrics"].get("comparison", {})
        acc = r.get("acceptance", {})

        lines.extend([
            f"### {scenario.get('name', r['scenario_id'])}",
            "",
            f"**Complexity:** {scenario.get('complexity', 'unknown')} | "
            f"**Expected winner:** {scenario.get('expected_winner', 'unknown')}",
            "",
            "| Metric | kiro-default | kiro-team | Winner |",
            "|--------|--------------|-----------|--------|",
            f"| Credits | {fmt_num(default.get('credits'))} | {fmt_num(team.get('credits'))} | {comp.get('credits_winner', 'n/a')} |",
            f"| Time | {fmt_num(default.get('duration_seconds'), 's')} | {fmt_num(team.get('duration_seconds'), 's')} | {comp.get('time_winner', 'n/a')} |",
            f"| Quality | {fmt_pct(acc.get('kiro_default', {}).get('score'))} | {fmt_pct(acc.get('kiro_team', {}).get('score'))} | {acc.get('quality_winner', 'n/a')} |",
            "",
        ])

        ratio = comp.get("credits_ratio")
        if isinstance(ratio, (int, float)) and ratio > 0:
            if ratio > 1.5:
                lines.append(f"⚠️ kiro-team used {ratio:.1f}x more credits")
            elif ratio < 0.75:
                lines.append(f"✅ kiro-team used {1 / ratio:.1f}x fewer credits")
        for warning in r["metrics"].get("warnings", []):
            lines.append(f"- Warning: {warning}")

        lines.append("")

    lines.extend([
        "---",
        "",
        "## Conclusions",
        "",
    ])

    def verdict(label, wins, team_text, default_text):
        if wins["kiro-team"] + wins["kiro-default"] == 0:
            return f"- **{label}:** not enough data"
        if wins["kiro-team"] > wins["kiro-default"]:
            return f"- **{label}:** {team_text}"
        if wins["kiro-default"] > wins["kiro-team"]:
            return f"- **{label}:** {default_text}"
        return f"- **{label}:** no clear winner"

    lines.append(verdict("Credits", credit_wins, "kiro-team used fewer in most scenarios",
                         "kiro-default used fewer in most scenarios"))
    lines.append(verdict("Time", time_wins, "kiro-team was faster in most scenarios",
                         "kiro-default was faster in most scenarios"))
    lines.append(verdict("Quality", quality_wins, "kiro-team scored higher in most scenarios",
                         "kiro-default scored higher in most scenarios"))

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate comparison report")
    parser.add_argument("results_dir", help="Directory containing scenario results")
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    results = load_results(results_dir)

    if not results:
        print("No results found", file=sys.stderr)
        sys.exit(1)

    report = generate_report(results)
    print(report)


if __name__ == "__main__":
    main()
