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
from pathlib import Path
from datetime import datetime


def load_results(results_dir: Path) -> list:
    """Load all scenario results."""
    results = []
    
    for scenario_dir in results_dir.iterdir():
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


def generate_report(results: list) -> str:
    """Generate markdown report."""
    lines = [
        "# Comparative Evaluation Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        "",
    ]
    
    # Aggregate stats
    total = len(results)
    token_wins = {"kiro-default": 0, "kiro-team": 0, "tie": 0}
    time_wins = {"kiro-default": 0, "kiro-team": 0, "tie": 0}
    quality_wins = {"kiro-default": 0, "kiro-team": 0, "tie": 0}
    hypothesis_correct = 0
    
    for r in results:
        comp = r["metrics"].get("comparison", {})
        token_wins[comp.get("token_winner", "tie")] += 1
        time_wins[comp.get("time_winner", "tie")] += 1
        
        acc = r.get("acceptance", {})
        quality_wins[acc.get("quality_winner", "tie")] += 1
        
        expected = r["metrics"].get("scenario", {}).get("expected_winner", "")
        actual = acc.get("quality_winner", "")
        if expected == actual:
            hypothesis_correct += 1
    
    lines.extend([
        f"**Scenarios evaluated:** {total}",
        "",
        "### Wins by Category",
        "",
        "| Category | kiro-default | kiro-team | Tie |",
        "|----------|--------------|-----------|-----|",
        f"| Tokens (fewer) | {token_wins['kiro-default']} | {token_wins['kiro-team']} | {token_wins.get('tie', 0)} |",
        f"| Time (faster) | {time_wins['kiro-default']} | {time_wins['kiro-team']} | {time_wins.get('tie', 0)} |",
        f"| Quality (higher) | {quality_wins['kiro-default']} | {quality_wins['kiro-team']} | {quality_wins.get('tie', 0)} |",
        "",
        f"**Hypothesis accuracy:** {hypothesis_correct}/{total} ({hypothesis_correct/total*100:.0f}% correct)",
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
            f"| Tokens | {default.get('tokens_total', 'N/A')} | {team.get('tokens_total', 'N/A')} | {comp.get('token_winner', 'N/A')} |",
            f"| Time | {default.get('duration_seconds', 'N/A')}s | {team.get('duration_seconds', 'N/A')}s | {comp.get('time_winner', 'N/A')} |",
            f"| Quality | {acc.get('kiro_default', {}).get('score', 'N/A'):.0f}% | {acc.get('kiro_team', {}).get('score', 'N/A'):.0f}% | {acc.get('quality_winner', 'N/A')} |",
            "",
        ])
        
        # Token ratio analysis
        ratio = comp.get("token_ratio", 0)
        if ratio > 1.5:
            lines.append(f"⚠️ kiro-team used {ratio:.1f}x more tokens")
        elif ratio < 0.75:
            lines.append(f"✅ kiro-team used {1/ratio:.1f}x fewer tokens")
        
        lines.append("")
    
    # Conclusions
    lines.extend([
        "---",
        "",
        "## Conclusions",
        "",
    ])
    
    # Determine overall patterns
    if token_wins["kiro-team"] > token_wins["kiro-default"]:
        lines.append("- **Tokens:** kiro-team generally more efficient")
    else:
        lines.append("- **Tokens:** kiro-default generally more efficient (less orchestration overhead)")
    
    if quality_wins["kiro-team"] > quality_wins["kiro-default"]:
        lines.append("- **Quality:** kiro-team produces better results on complex tasks")
    else:
        lines.append("- **Quality:** kiro-default sufficient for most tasks")
    
    lines.extend([
        "",
        "### Recommendations",
        "",
        "Use **kiro-default** when:",
        "- Task is simple and well-defined",
        "- Token budget is tight",
        "- Speed is priority over thoroughness",
        "",
        "Use **kiro-team** when:",
        "- Task spans multiple files",
        "- Requirements are ambiguous",
        "- Validation/verification is critical",
        "- Task benefits from specialized agents",
    ])
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate comparison report")
    parser.add_argument("results_dir", help="Directory containing scenario results")
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    
    if not results_dir.exists():
        print(f"Results directory not found: {results_dir}")
        return
    
    results = load_results(results_dir)
    
    if not results:
        print("No results found")
        return
    
    report = generate_report(results)
    print(report)


if __name__ == "__main__":
    main()
