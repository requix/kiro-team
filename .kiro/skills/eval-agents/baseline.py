#!/usr/bin/env python3
"""
Baseline management for kiro-team evaluations.

Usage:
    python baseline.py save <name> <results.json>
    python baseline.py compare <baseline-name> <current.json>
    python baseline.py list
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime
import subprocess


BASELINES_DIR = Path(__file__).parent.parent.parent / "evals" / "baselines"


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


def save_baseline(name: str, results_path: str):
    """Save evaluation results as a named baseline."""
    with open(results_path) as f:
        results = json.load(f)
    
    baseline = {
        "name": name,
        "created_at": datetime.now().isoformat(),
        "commit": get_commit_hash(),
        "scores": {}
    }
    
    # Handle both single result and multiple results
    if "scenario_id" in results:
        # Single result
        baseline["scores"][results["scenario_id"]] = {
            "score": results["total"],
            "percentage": results["percentage"],
            "breakdown": results["breakdown"]
        }
    elif "scenarios" in results:
        # Multiple results
        for scenario_id, data in results["scenarios"].items():
            baseline["scores"][scenario_id] = {
                "score": data.get("total", 0),
                "percentage": data.get("percentage", 0),
                "breakdown": data.get("breakdown", {})
            }
    
    # Calculate summary
    scores = [s["percentage"] for s in baseline["scores"].values()]
    baseline["summary"] = {
        "total_scenarios": len(scores),
        "average_score": sum(scores) / len(scores) if scores else 0,
        "passed": sum(1 for s in scores if s >= 80),
        "failed": sum(1 for s in scores if s < 80)
    }
    
    # Save
    BASELINES_DIR.mkdir(parents=True, exist_ok=True)
    output_path = BASELINES_DIR / f"{name}.json"
    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2)
    
    print(f"Saved baseline to {output_path}")
    return baseline


def compare_baselines(baseline_name: str, current_path: str) -> dict:
    """Compare current results against a baseline."""
    baseline_path = BASELINES_DIR / f"{baseline_name}.json"
    
    if not baseline_path.exists():
        print(f"Baseline not found: {baseline_name}", file=sys.stderr)
        print(f"Available baselines: {list_baselines()}", file=sys.stderr)
        sys.exit(1)
    
    with open(baseline_path) as f:
        baseline = json.load(f)
    
    with open(current_path) as f:
        current = json.load(f)
    
    comparison = {
        "baseline": baseline_name,
        "baseline_commit": baseline.get("commit", "unknown"),
        "current_commit": get_commit_hash(),
        "scenarios": {},
        "summary": {
            "improved": 0,
            "stable": 0,
            "regressed": 0,
            "new": 0
        }
    }
    
    # Get current scores in same format
    current_scores = {}
    if "scenario_id" in current:
        current_scores[current["scenario_id"]] = current["percentage"]
    elif "scenarios" in current:
        for sid, data in current["scenarios"].items():
            current_scores[sid] = data.get("percentage", 0)
    
    # Compare each scenario
    for scenario_id, baseline_data in baseline.get("scores", {}).items():
        baseline_score = baseline_data.get("percentage", 0)
        current_score = current_scores.get(scenario_id)
        
        if current_score is None:
            comparison["scenarios"][scenario_id] = {
                "status": "missing",
                "baseline": baseline_score,
                "current": None
            }
            continue
        
        diff = current_score - baseline_score
        
        if diff > 5:
            status = "improved"
            comparison["summary"]["improved"] += 1
        elif diff < -5:
            status = "regressed"
            comparison["summary"]["regressed"] += 1
        else:
            status = "stable"
            comparison["summary"]["stable"] += 1
        
        comparison["scenarios"][scenario_id] = {
            "status": status,
            "baseline": baseline_score,
            "current": current_score,
            "diff": diff
        }
    
    # Check for new scenarios
    for scenario_id in current_scores:
        if scenario_id not in baseline.get("scores", {}):
            comparison["scenarios"][scenario_id] = {
                "status": "new",
                "baseline": None,
                "current": current_scores[scenario_id]
            }
            comparison["summary"]["new"] += 1
    
    return comparison


def list_baselines() -> list[str]:
    """List available baselines."""
    if not BASELINES_DIR.exists():
        return []
    return [p.stem for p in BASELINES_DIR.glob("*.json") if p.stem != "README"]


def main():
    parser = argparse.ArgumentParser(description="Manage evaluation baselines")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Save command
    save_parser = subparsers.add_parser("save", help="Save a new baseline")
    save_parser.add_argument("name", help="Baseline name (e.g., v1.0.0)")
    save_parser.add_argument("results", help="Path to results JSON file")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare against baseline")
    compare_parser.add_argument("baseline", help="Baseline name to compare against")
    compare_parser.add_argument("current", help="Path to current results JSON")
    
    # List command
    subparsers.add_parser("list", help="List available baselines")
    
    args = parser.parse_args()
    
    if args.command == "save":
        result = save_baseline(args.name, args.results)
        print(json.dumps(result, indent=2))
    
    elif args.command == "compare":
        result = compare_baselines(args.baseline, args.current)
        print(json.dumps(result, indent=2))
    
    elif args.command == "list":
        baselines = list_baselines()
        if baselines:
            print("Available baselines:")
            for b in baselines:
                print(f"  - {b}")
        else:
            print("No baselines found")


if __name__ == "__main__":
    main()
