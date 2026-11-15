#!/usr/bin/env python3
"""
Check acceptance criteria for both approaches.

Runs the acceptance checks defined in the scenario YAML
against both workspaces.
"""

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent.parent
CHECKS_DIR = EVAL_DIR / "checks"
BASE_TAG = "eval-base"


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


def _expand(command: str, workspace: Path) -> str:
    return command.replace("{workspace}", str(workspace)).replace("{checks}", str(CHECKS_DIR))


def _parse_count(proc: subprocess.CompletedProcess) -> tuple[int | None, str]:
    """Read an integer from a counting command, or explain why not.

    Commands run under bash with pipefail, so a failing step anywhere in the
    pipeline fails the check. One exception: grep exits 1 when nothing matches,
    so exit 1 with an output of "0" is read as a real zero.
    """
    out = proc.stdout.strip()
    if proc.returncode != 0 and not (proc.returncode == 1 and out == "0"):
        err = (proc.stderr.strip().splitlines() or [""])[-1]
        return None, f"Command failed with exit code {proc.returncode}: {err}"
    try:
        return int(out), ""
    except ValueError:
        return None, f"Could not parse output as int: {out!r}"


def check_command(workspace: Path, check: dict) -> dict:
    """Run a command in the workspace and check its result."""
    command = _expand(check["command"], workspace)
    result = {
        "type": "command",
        "command": command,
        "passed": False,
        "details": "",
    }

    try:
        proc = subprocess.run(
            ["bash", "-o", "pipefail", "-c", command],
            capture_output=True,
            text=True,
            timeout=check.get("timeout", 120),
            cwd=workspace,
        )
    except subprocess.TimeoutExpired:
        result["details"] = "Command timed out"
        return result
    except Exception as e:
        result["details"] = f"Error: {e}"
        return result

    if "exit_code" in check:
        if proc.returncode != check["exit_code"]:
            result["details"] = f"Exit code {proc.returncode} != expected {check['exit_code']}"
            return result
        result["details"] = f"Exit code {proc.returncode} matches expected"

    if "max_value" in check or "min_value" in check:
        value, why = _parse_count(proc)
        if value is None:
            result["details"] = why
            return result
        if "max_value" in check and value > check["max_value"]:
            result["details"] = f"Value {value} > max {check['max_value']}"
            return result
        if "min_value" in check and value < check["min_value"]:
            result["details"] = f"Value {value} < min {check['min_value']}"
            return result
        result["details"] = f"Value {value} within bounds"
        result["passed"] = True
        return result

    if "exit_code" in check:
        result["passed"] = True
        return result

    # No explicit expectation: the command must succeed.
    result["passed"] = proc.returncode == 0
    result["details"] = f"Command completed with exit code {proc.returncode}"
    return result


def prepare_workspace(fixture: Path, workspace: Path) -> None:
    """Copy a fixture into a workspace and commit it, tagged as eval-base.

    The runners and the baseline check share this so both start from the
    same state.
    """
    shutil.copytree(fixture, workspace, dirs_exist_ok=True)
    git = ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.invalid"]
    for cmd in (
        ["git", "init", "-q"],
        ["git", "add", "-A"],
        git + ["commit", "-q", "-m", "initial"],
        ["git", "tag", BASE_TAG],
    ):
        subprocess.run(cmd, cwd=workspace, check=True, capture_output=True)


def baseline_score(scenario_file: Path) -> dict:
    """Score the untouched fixture. A good scenario scores low here."""
    import yaml

    scenario = yaml.safe_load(scenario_file.read_text())
    fixture = EVAL_DIR / scenario["fixture"]
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp) / "ws"
        prepare_workspace(fixture, workspace)
        return check_acceptance(workspace, scenario.get("acceptance", []))


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
    parser.add_argument("--default-workspace", help="kiro-default workspace")
    parser.add_argument("--team-workspace", help="kiro-team workspace")
    parser.add_argument("--output", help="Output JSON file")
    parser.add_argument(
        "--prepare",
        metavar="DEST",
        help="Copy the scenario's fixture into DEST, commit it and tag it eval-base, then exit",
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Score the untouched fixture and print the result (no agent run)",
    )
    args = parser.parse_args()

    if args.prepare:
        import yaml
        scenario = yaml.safe_load(Path(args.scenario).read_text())
        fixture = EVAL_DIR / scenario["fixture"]
        if not fixture.is_dir():
            parser.error(f"fixture not found: {fixture}")
        prepare_workspace(fixture, Path(args.prepare))
        return

    if args.baseline:
        res = baseline_score(Path(args.scenario))
        print(f"Baseline (untouched fixture): {res['passed']}/{res['total']} ({res['score']:.0f}%)")
        for c in res["checks"]:
            print(f"  [{'PASS' if c['passed'] else 'fail'}] {c['description']}")
        return

    if not (args.default_workspace and args.team_workspace and args.output):
        parser.error("--default-workspace, --team-workspace and --output are required")

    import yaml
    with open(args.scenario) as f:
        scenario = yaml.safe_load(f)

    acceptance = scenario.get("acceptance", [])
    if not acceptance:
        print("No acceptance criteria defined in scenario")
        empty = {"passed": 0, "failed": 0, "total": 0, "score": 0, "checks": []}
        result = {"scenario_id": scenario["id"], "kiro_default": empty, "kiro_team": dict(empty), "quality_winner": "tie"}
    else:
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

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"Acceptance results saved to {output_path}")
    for key in ("kiro_default", "kiro_team"):
        r = result[key]
        print(f"  {key}: {r['passed']}/{r['total']} ({r['score']:.0f}%)")


if __name__ == "__main__":
    main()
