#!/usr/bin/env python3
"""
Evaluation scorer for kiro-team agents.

This script helps score agent responses against scenario criteria.
It's called by the @eval-agents skill during evaluation.

Usage:
    python scorer.py <scenario.yaml> <response.txt> [--verbose]
    
Output:
    JSON with score breakdown
"""

import argparse
import json
import sys
import yaml
from pathlib import Path
from datetime import datetime


def load_scenario(path: str) -> dict:
    """Load a scenario YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


def load_response(path: str) -> str:
    """Load an agent response from file."""
    with open(path) as f:
        return f.read()


def check_must_do(response: str, must_do: list[str]) -> tuple[int, list[str]]:
    """
    Check if response indicates all must_do items were done.
    Returns (points_earned, issues_found)
    
    Note: This is a heuristic check. Full evaluation requires LLM analysis.
    """
    issues = []
    score = 0
    max_per_item = 100 // len(must_do) if must_do else 0
    
    for item in must_do:
        # Simple keyword matching as a baseline
        # The LLM-based evaluation in the skill does deeper analysis
        keywords = item.lower().split()
        matches = sum(1 for kw in keywords if kw in response.lower())
        if matches >= len(keywords) * 0.5:
            score += max_per_item
        else:
            issues.append(f"May not have done: {item}")
    
    return score, issues


def check_must_not(response: str, must_not: list[str]) -> tuple[int, list[str]]:
    """
    Check if response indicates any must_not violations.
    Returns (penalty, violations_found)
    """
    violations = []
    penalty = 0
    
    violation_indicators = {
        "create or modify": ["created", "wrote", "modified", "updated"],
        "run shell": ["ran", "executed", "$ "],
        "spawn": ["spawned", "delegated", "subagent"],
        "ask": ["what would you like", "could you clarify", "which option"],
    }
    
    for item in must_not:
        item_lower = item.lower()
        for pattern, indicators in violation_indicators.items():
            if pattern in item_lower:
                for indicator in indicators:
                    if indicator in response.lower():
                        violations.append(f"Possible violation: {item}")
                        penalty += 15
                        break
    
    return min(penalty, 35), violations  # Cap at max role_adherence points


def score_response(scenario: dict, response: str, verbose: bool = False) -> dict:
    """
    Score an agent response against a scenario.
    
    Returns a score breakdown dict.
    """
    expected = scenario.get("expected", {})
    scoring_weights = scenario.get("scoring", {
        "task_completion": 40,
        "role_adherence": 35,
        "output_format": 15,
        "efficiency": 10
    })
    
    result = {
        "scenario_id": scenario.get("id", "unknown"),
        "agent": scenario.get("agent", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "breakdown": {},
        "issues": [],
        "total": 0,
        "passed": False
    }
    
    # Task completion
    must_do = expected.get("must_do", [])
    if must_do:
        completion_score, completion_issues = check_must_do(response, must_do)
        # Scale to the weight
        scaled_score = int((completion_score / 100) * scoring_weights.get("task_completion", 40))
        result["breakdown"]["task_completion"] = {
            "score": scaled_score,
            "max": scoring_weights.get("task_completion", 40),
            "issues": completion_issues
        }
        result["issues"].extend(completion_issues)
    
    # Role adherence
    must_not = expected.get("must_not", [])
    if must_not:
        penalty, violations = check_must_not(response, must_not)
        adherence_max = scoring_weights.get("role_adherence", 35)
        adherence_score = max(0, adherence_max - penalty)
        result["breakdown"]["role_adherence"] = {
            "score": adherence_score,
            "max": adherence_max,
            "violations": violations
        }
        result["issues"].extend(violations)
    
    # Output format (basic check for report structure)
    format_max = scoring_weights.get("output_format", 15)
    format_score = 0
    format_issues = []
    
    # Check for common report markers
    report_markers = ["##", "**", "Status:", "Task:", "Complete", "Report"]
    matches = sum(1 for m in report_markers if m in response)
    format_score = int((matches / len(report_markers)) * format_max)
    
    if format_score < format_max * 0.5:
        format_issues.append("Response may not follow expected report format")
    
    result["breakdown"]["output_format"] = {
        "score": format_score,
        "max": format_max,
        "issues": format_issues
    }
    
    # Efficiency (heuristic: shorter is often better for simple tasks)
    efficiency_max = scoring_weights.get("efficiency", 10)
    response_length = len(response)
    if response_length < 500:
        efficiency_score = efficiency_max
    elif response_length < 1000:
        efficiency_score = int(efficiency_max * 0.8)
    elif response_length < 2000:
        efficiency_score = int(efficiency_max * 0.6)
    else:
        efficiency_score = int(efficiency_max * 0.4)
    
    result["breakdown"]["efficiency"] = {
        "score": efficiency_score,
        "max": efficiency_max
    }
    
    # Calculate total
    result["total"] = sum(
        cat.get("score", 0) 
        for cat in result["breakdown"].values()
    )
    result["max_possible"] = sum(
        cat.get("max", 0) 
        for cat in result["breakdown"].values()
    )
    result["percentage"] = int((result["total"] / result["max_possible"]) * 100)
    result["passed"] = result["percentage"] >= 80
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Score agent evaluation responses")
    parser.add_argument("scenario", help="Path to scenario YAML file")
    parser.add_argument("response", help="Path to response text file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--output", "-o", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    try:
        scenario = load_scenario(args.scenario)
        response = load_response(args.response)
        result = score_response(scenario, response, args.verbose)
        
        output = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)
            
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
