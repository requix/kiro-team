#!/usr/bin/env python3
"""
Check acceptance criteria for both approaches.

Runs the acceptance checks defined in the scenario YAML
against both workspaces.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path


def check_file_pattern(workspace: Path, check: dict) -> dict:
    """Check if a file contains/doesn't contain a pattern."""
    file_path = workspace / check["file"]
    result = {
        "type": "file_pattern",
        "file": check["file"],
        "passed": False,
        "details": "",
    }
    
    if not file_path.exists():
        result["details"] = f"File not found: {check['file']}"
        return result
    
    content = file_path.read_text()
    
    # Check positive pattern
    if "pattern" in check:
        if re.search(check["pattern"], content):
            result["passed"] = True
            result["details"] = f"Pattern found: {check['pattern']}"
        else:
            result["details"] = f"Pattern not found: {check['pattern']}"
            return result
    
    # Check negative pattern
    if "not_pattern" in check:
        if re.search(check["not_pattern"], content):
            result["passed"] = False
            result["details"] = f"Forbidden pattern found: {check['not_pattern']}"
            return result
    
    if "pattern" not in check and "not_pattern" in check:
        result["passed"] = True
        result["details"] = f"Forbidden pattern absent: {check['not_pattern']}"
    
    return result


def check_command(workspace: Path, check: dict) -> dict:
    """Run a command and check its result."""
    command = check["command"].replace("{workspace}", str(workspace))
    result = {
        "type": "command",
        "command": command,
        "passed": False,
        "details": "",
    }
    
    try:
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=workspace,
        )
        
        # Check exit code
        if "exit_code" in check:
            if proc.returncode == check["exit_code"]:
                result["passed"] = True
                result["details"] = f"Exit code {proc.returncode} matches expected"
            else:
                result["details"] = f"Exit code {proc.returncode} != expected {check['exit_code']}"
                return result
        
        # Check output value
        output_value = proc.stdout.strip()
        if "max_value" in check:
            try:
                value = int(output_value)
                if value <= check["max_value"]:
                    result["passed"] = True
                    result["details"] = f"Value {value} <= {check['max_value']}"
                else:
                    result["details"] = f"Value {value} > max {check['max_value']}"
            except ValueError:
                result["details"] = f"Could not parse output as int: {output_value}"
        
        if "min_value" in check:
            try:
                value = int(output_value)
                if value >= check["min_value"]:
                    result["passed"] = True
                    result["details"] = f"Value {value} >= {check['min_value']}"
                else:
                    result["details"] = f"Value {value} < min {check['min_value']}"
            except ValueError:
                result["details"] = f"Could not parse output as int: {output_value}"
        
        # If no specific check, just verify it ran
        if "exit_code" not in check and "max_value" not in check and "min_value" not in check:
            result["passed"] = proc.returncode == 0
            result["details"] = f"Command completed with exit code {proc.returncode}"
        
    except subprocess.TimeoutExpired:
        result["details"] = "Command timed out"
    except Exception as e:
        result["details"] = f"Error: {e}"
    
    return result


def check_acceptance(workspace: Path, acceptance: list) -> dict:
    """Run all acceptance checks against a workspace."""
    results = {
        "passed": 0,
        "failed": 0,
        "checks": [],
    }
    
    for check in acceptance:
        if "file" in check and ("pattern" in check or "not_pattern" in check):
            result = check_file_pattern(workspace, check)
        elif "command" in check:
            result = check_command(workspace, check)
        else:
            result = {
                "type": "unknown",
                "passed": False,
                "details": f"Unknown check type: {check}",
            }
        
        result["description"] = check.get("description", "")
        results["checks"].append(result)
        
        if result["passed"]:
            results["passed"] += 1
        else:
            results["failed"] += 1
    
    results["total"] = results["passed"] + results["failed"]
    results["score"] = (
        results["passed"] / results["total"] * 100
        if results["total"] > 0 else 0
    )
    
    return results


def main():
    parser = argparse.ArgumentParser(description="Check acceptance criteria")
    parser.add_argument("--scenario", required=True, help="Scenario YAML file")
    parser.add_argument("--default-workspace", required=True, help="kiro-default workspace")
    parser.add_argument("--team-workspace", required=True, help="kiro-team workspace")
    parser.add_argument("--output", required=True, help="Output JSON file")
    args = parser.parse_args()
    
    # Load scenario
    import yaml
    with open(args.scenario) as f:
        scenario = yaml.safe_load(f)
    
    acceptance = scenario.get("acceptance", [])
    
    if not acceptance:
        print("No acceptance criteria defined in scenario")
        result = {
            "kiro_default": {"passed": 0, "failed": 0, "total": 0, "score": 0, "checks": []},
            "kiro_team": {"passed": 0, "failed": 0, "total": 0, "score": 0, "checks": []},
        }
    else:
        # Check both workspaces
        default_results = check_acceptance(Path(args.default_workspace), acceptance)
        team_results = check_acceptance(Path(args.team_workspace), acceptance)
        
        result = {
            "scenario_id": scenario["id"],
            "kiro_default": default_results,
            "kiro_team": team_results,
            "quality_winner": (
                "kiro-default" if default_results["score"] > team_results["score"]
                else "kiro-team" if team_results["score"] > default_results["score"]
                else "tie"
            ),
        }
    
    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Acceptance results saved to {output_path}")
    if acceptance:
        print(f"  kiro-default: {default_results['passed']}/{default_results['total']} ({default_results['score']:.0f}%)")
        print(f"  kiro-team:    {team_results['passed']}/{team_results['total']} ({team_results['score']:.0f}%)")


if __name__ == "__main__":
    main()
