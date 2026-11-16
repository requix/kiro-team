"""Tests for the comparative eval harness: scoring, metrics, report, runners.

Run from the repo root: python -m pytest evals/comparative/tests -q
Needs pyyaml and pytest. No kiro-cli or network: a fake kiro-cli stands in.
"""

import json
import os
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
import yaml

EVAL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EVAL_DIR / "metrics"))

import check_acceptance  # noqa: E402
import collect  # noqa: E402
import report  # noqa: E402

SCENARIOS = sorted((EVAL_DIR / "scenarios").glob("*.yaml"))


def load(name: str) -> dict:
    return yaml.safe_load((EVAL_DIR / "scenarios" / f"{name}.yaml").read_text())


def workspace_for(name: str, tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    check_acceptance.prepare_workspace(EVAL_DIR / load(name)["fixture"], ws)
    return ws


def score(name: str, ws: Path) -> dict:
    return check_acceptance.check_acceptance(ws, load(name)["acceptance"])


def by_description(result: dict) -> dict:
    return {c["description"]: c["passed"] for c in result["checks"]}


# --- Baseline: doing nothing must not score well -----------------------------


# Checks allowed to pass on an untouched fixture: the fixture's own tests are
# green, and doing nothing changes nothing. Every other check must fail.
BASELINE_MAY_PASS = {"Tests pass", "All tests pass", "No unrelated changes"}


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda p: p.stem)
def test_untouched_fixture_scores_low(scenario):
    result = check_acceptance.baseline_score(scenario)
    passed = {c["description"] for c in result["checks"] if c["passed"]}
    assert passed <= BASELINE_MAY_PASS, f"{scenario.stem}: unexpected passes {passed - BASELINE_MAY_PASS}"
    assert result["score"] <= 34, f"{scenario.stem} baseline {result['score']:.0f}%: {passed}"


# --- Reference solutions: correct work must score 100% -----------------------

GOOD_CACHE = '''

import threading as _threading
import time as _time


class TimedCache:
    def __init__(self, fetcher, ttl=60):
        self._fetcher = fetcher
        self._ttl = ttl
        self._lock = _threading.Lock()
        self._value = None
        self._expires = 0.0

    def get(self):
        with self._lock:
            now = _time.monotonic()
            if now >= self._expires:
                self._value = self._fetcher()
                self._expires = now + self._ttl
            return self._value
'''

NAIVE_CACHE = GOOD_CACHE.replace(
    """        with self._lock:
            now = _time.monotonic()
            if now >= self._expires:
                self._value = self._fetcher()
                self._expires = now + self._ttl
            return self._value""",
    """        now = _time.monotonic()
        if now >= self._expires:
            self._value = self._fetcher()
            self._expires = now + self._ttl
        return self._value""",
)

CACHE_TESTS = '''

from src.processor import TimedCache


def test_timed_cache_caches(counter_fetcher):
    cache = TimedCache(counter_fetcher, ttl=60)
    assert cache.get() == cache.get()


def test_timed_cache_thread_smoke(counter_fetcher):
    import threading
    cache = TimedCache(counter_fetcher, ttl=60)
    threads = [threading.Thread(target=cache.get) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
'''


def test_correct_cache_scores_full(tmp_path):
    ws = workspace_for("validation-trap", tmp_path)
    with open(ws / "src/processor.py", "a") as f:
        f.write(GOOD_CACHE)
    with open(ws / "tests/test_processor.py", "a") as f:
        f.write(CACHE_TESTS)
    result = score("validation-trap", ws)
    assert result["score"] == 100, result["checks"]


def test_naive_cache_fails_thread_safety(tmp_path):
    ws = workspace_for("validation-trap", tmp_path)
    with open(ws / "src/processor.py", "a") as f:
        f.write(NAIVE_CACHE)
    checks = by_description(score("validation-trap", ws))
    assert checks["Caches within the TTL"] is True
    assert checks["One fetch for 20 concurrent gets"] is False


GOOD_PAGINATE = '''


def paginate(items, page=1, page_size=10):
    if page < 1 or page_size < 1:
        raise ValueError("page and page_size must be >= 1")
    page_size = min(page_size, 100)
    total = len(items)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    return {
        "items": items[start:start + page_size],
        "total_count": total,
        "total_pages": total_pages,
        "current_page": page,
        "has_next": page < total_pages,
        "has_prev": 1 < page <= max(total_pages, 1),
    }
'''

PAGINATE_TESTS = '''


def test_paginate_first_page():
    from src.api import paginate
    assert len(paginate(get_items(), 1, 10)["items"]) == 10
'''


def test_correct_paginate_scores_full(tmp_path):
    ws = workspace_for("validator-feedback", tmp_path)
    with open(ws / "src/api.py", "a") as f:
        f.write(GOOD_PAGINATE)
    with open(ws / "tests/test_api.py", "a") as f:
        f.write(PAGINATE_TESTS)
    result = score("validator-feedback", ws)
    assert result["score"] == 100, result["checks"]


def test_off_by_one_paginate_fails(tmp_path):
    ws = workspace_for("validator-feedback", tmp_path)
    with open(ws / "src/api.py", "a") as f:
        f.write(GOOD_PAGINATE.replace('"has_next": page < total_pages', '"has_next": page <= total_pages'))
    checks = by_description(score("validator-feedback", ws))
    assert checks["Returns pagination metadata"] is True
    assert checks["Page bounds and has_next/has_prev"] is False


def _git(ws: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=ws, check=True, capture_output=True,
    )


def test_refactor_with_kept_test_names_scores_full(tmp_path):
    ws = workspace_for("multi-file-refactor", tmp_path)
    for path in list((ws / "src").rglob("*.py")) + list((ws / "tests").rglob("*.py")):
        text = path.read_text()
        # Rename the function, but leave test function names such as
        # test_get_user_data_existing alone: the task does not ask for that.
        import re
        new = re.sub(r"\bget_user_data\b", "fetch_user_profile", text)
        path.write_text(new)
    _git(ws, "commit", "-qam", "refactor: rename get_user_data to fetch_user_profile")
    result = score("multi-file-refactor", ws)
    assert result["score"] == 100, result["checks"]


def test_refactor_with_wrong_commit_message_fails_commit_check(tmp_path):
    ws = workspace_for("multi-file-refactor", tmp_path)
    _git(ws, "commit", "-q", "--allow-empty", "-m", "refactor: something else")
    checks = by_description(score("multi-file-refactor", ws))
    assert checks["Commit with the requested message"] is False


def test_bugfix_scores_full_and_scope_creep_fails(tmp_path):
    ws = workspace_for("simple-bugfix", tmp_path)
    counter = ws / "src/counter.py"
    counter.write_text(counter.read_text().replace("return len(items) + 1", "return len(items)"))
    assert score("simple-bugfix", ws)["score"] == 100
    (ws / "src/extra.py").write_text("x = 1\n")
    _git(ws, "add", "-A")
    checks = by_description(score("simple-bugfix", ws))
    assert checks["No unrelated changes"] is False


# --- Command checks fail when the command itself fails -----------------------


def test_count_check_fails_when_pipeline_errors(tmp_path):
    check = {"command": "git diff --stat HEAD~1 | wc -l", "max_value": 3}
    (tmp_path / "f").write_text("x")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "only commit")
    result = check_acceptance.check_command(tmp_path, check)
    assert result["passed"] is False
    assert "exit code" in result["details"]


def test_count_check_accepts_grep_no_match(tmp_path):
    (tmp_path / "f.txt").write_text("nothing here\n")
    check = {"command": "grep -c 'needle' f.txt", "max_value": 0}
    assert check_acceptance.check_command(tmp_path, check)["passed"] is True


# --- Metrics -----------------------------------------------------------------


def _write_run(log_dir: Path, lines: list, duration=10, exit_code=0) -> Path:
    log_dir.mkdir(parents=True)
    (log_dir / "output.log").write_text("\n".join(json.dumps(x) if isinstance(x, dict) else x for x in lines))
    if duration is not None:
        (log_dir / "duration.txt").write_text(f"{duration}\n")
    if exit_code is not None:
        (log_dir / "exit_code.txt").write_text(f"{exit_code}\n")
    return log_dir


SCENARIO_META = {"id": "s", "name": "S"}


def test_credits_and_tool_calls_parsed(tmp_path):
    run = _write_run(tmp_path / "a", [
        {"method": "_kiro.dev/metadata", "params": {"meteringUsage": [{"unit": "credit", "value": 0.5}]}},
        {"method": "_kiro.dev/metadata", "params": {"meteringUsage": [{"unit": "credit", "value": 0.25}]}},
        {"params": {"update": {"sessionUpdate": "tool_call", "toolCallId": "a"}}},
        {"params": {"update": {"sessionUpdate": "tool_call", "toolCallId": "b"}}},
        "not json",
    ])
    m = collect.parse_run(run)
    assert m["credits"] == 0.75
    assert m["tool_calls"] == 2
    assert m["tokens_total"] is None
    assert m["exit_code"] == 0


def test_missing_logs_are_null_and_never_win(tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    m = collect.parse_run(empty)
    assert m["credits"] is None and m["tokens_total"] is None and m["duration_seconds"] is None
    result = collect.build_result(SCENARIO_META, m, dict(m))
    assert result["comparison"]["credits_winner"] == "n/a"
    assert result["comparison"]["tokens_winner"] == "n/a"
    assert result["comparison"]["time_winner"] == "n/a"
    assert any("no cost data" in w for w in result["warnings"])


def test_equal_values_tie(tmp_path):
    line = {"params": {"meteringUsage": [{"unit": "credit", "value": 1}]}}
    a = collect.parse_run(_write_run(tmp_path / "a", [line], duration=5))
    b = collect.parse_run(_write_run(tmp_path / "b", [line], duration=5))
    comp = collect.build_result(SCENARIO_META, a, b)["comparison"]
    assert comp["credits_winner"] == "tie"
    assert comp["time_winner"] == "tie"


def test_nonzero_exit_is_a_warning(tmp_path):
    a = collect.parse_run(_write_run(tmp_path / "a", [], exit_code=0))
    b = collect.parse_run(_write_run(tmp_path / "b", [], exit_code=3))
    warnings = collect.build_result(SCENARIO_META, a, b)["warnings"]
    assert "kiro-team exited with code 3" in warnings


# --- Report ------------------------------------------------------------------


def test_report_handles_zero_ratio_and_missing_acceptance(tmp_path):
    scenario_dir = tmp_path / "s"
    scenario_dir.mkdir()
    (scenario_dir / "metrics.json").write_text(json.dumps({
        "scenario": {"id": "s", "name": "S"},
        "kiro_default": {"credits": 0, "duration_seconds": None},
        "kiro_team": {"credits": 0, "duration_seconds": 3},
        "comparison": {"credits_ratio": 0, "credits_winner": "tie", "time_winner": "n/a"},
    }))
    text = report.generate_report(report.load_results(tmp_path))
    assert "| Quality | N/A | N/A | n/a |" in text
    assert "not enough data" in text


def test_report_exits_nonzero_without_results(tmp_path):
    proc = subprocess.run(
        [sys.executable, str(EVAL_DIR / "metrics/report.py"), str(tmp_path)],
        capture_output=True, text=True,
    )
    assert proc.returncode == 1


# --- Runners (fake kiro-cli) -------------------------------------------------


def _fake_kiro(bin_dir: Path, exit_code: int) -> None:
    """A kiro-cli stand-in. Like the real one (2.27), it exits 2 on a flag
    `kiro-cli chat` does not know. Otherwise it records its args and workspace
    listing in $FAKE_KIRO_SEEN/<agent>.txt, then prints one credit event."""
    bin_dir.mkdir()
    script = bin_dir / "kiro-cli"
    script.write_text(textwrap.dedent(f"""\
        #!/bin/bash
        agent=""
        prev=""
        for a in "$@"; do
            case "$a" in
                --agent|--model|--output-format|--trust-all-tools|--no-interactive) ;;
                --*) echo "error: unexpected argument '$a' found" >&2; exit 2 ;;
            esac
            [[ "$prev" == "--agent" ]] && agent="$a"
            prev="$a"
        done
        {{ printf '%s\\n' "$@"; echo "---"; find . -path ./.git -prune -o -type f -print | sort; }} \\
            > "$FAKE_KIRO_SEEN/$agent.txt"
        echo '{{"params":{{"meteringUsage":[{{"unit":"credit","value":0.5}}]}}}}'
        exit {exit_code}
        """))
    script.chmod(script.stat().st_mode | stat.S_IEXEC)


def _run_comparison(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PATH"] = f"{tmp_path / 'bin'}{os.pathsep}{env['PATH']}"
    env["EVAL_RESULTS_DIR"] = str(tmp_path / "results")
    env["FAKE_KIRO_SEEN"] = str(tmp_path / "seen")
    (tmp_path / "seen").mkdir(exist_ok=True)
    return subprocess.run(
        ["bash", str(EVAL_DIR / "runners/run-comparison.sh"), *args],
        capture_output=True, text=True, env=env, timeout=300,
    )


def test_runner_records_kiro_failure(tmp_path):
    _fake_kiro(tmp_path / "bin", exit_code=3)
    proc = _run_comparison(tmp_path, str(EVAL_DIR / "scenarios/simple-bugfix.yaml"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result_dir = next((tmp_path / "results").glob("simple-bugfix*"))
    assert (result_dir / "kiro-team/exit_code.txt").read_text().strip() == "3"
    metrics = json.loads((result_dir / "metrics.json").read_text())
    assert "kiro-team exited with code 3" in metrics["warnings"]
    assert metrics["kiro_team"]["credits"] == 0.5


def test_runner_rejects_unsafe_model(tmp_path):
    _fake_kiro(tmp_path / "bin", exit_code=0)
    proc = _run_comparison(tmp_path, "--model", "../evil", str(EVAL_DIR / "scenarios/simple-bugfix.yaml"))
    assert proc.returncode != 0
    assert "invalid model id" in proc.stderr
    assert not (tmp_path / "results").exists()


def test_team_workspace_is_provisioned(tmp_path):
    _fake_kiro(tmp_path / "bin", exit_code=0)
    proc = _run_comparison(tmp_path, str(EVAL_DIR / "scenarios/simple-bugfix.yaml"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    seen = (tmp_path / "seen/team-lead.txt").read_text()
    for path in (
        "./.kiro/agents/team-lead.json",
        "./.kiro/steering/agent-constraints.md",
        "./scripts/worktree-create.sh",
        "./scripts/worktree-merge.sh",
        "./specs/simple-bugfix.md",
    ):
        assert path in seen, f"{path} missing from the team workspace"
    assert "Execute the plan in specs/simple-bugfix.md." in seen
    # The default arm gets the plain task and no team setup.
    default_seen = (tmp_path / "seen/kiro_default.txt").read_text()
    assert "Fix the off-by-one error" in default_seen
    assert "./scripts/worktree-create.sh" not in default_seen


def test_both_arms_get_the_same_model_by_default(tmp_path):
    _fake_kiro(tmp_path / "bin", exit_code=0)
    proc = _run_comparison(tmp_path, str(EVAL_DIR / "scenarios/simple-bugfix.yaml"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    team_model = json.loads((EVAL_DIR.parent.parent / ".kiro/agents/team-lead.json").read_text())["model"]
    result_dir = tmp_path / f"results/simple-bugfix-{team_model}"
    metrics = json.loads((result_dir / "metrics.json").read_text())
    assert metrics["kiro_default"]["model"] == team_model
    assert metrics["kiro_team"]["model"] == team_model
    assert not any("different models" in w for w in metrics["warnings"])
    for arm in ("kiro-default", "kiro-team"):
        assert f"--model\n{team_model}" in (tmp_path / "seen" / (
            "kiro_default.txt" if arm == "kiro-default" else "team-lead.txt")).read_text()


def test_changes_are_saved_and_no_change_warns(tmp_path):
    _fake_kiro(tmp_path / "bin", exit_code=0)
    proc = _run_comparison(tmp_path, str(EVAL_DIR / "scenarios/simple-bugfix.yaml"))
    assert proc.returncode == 0, proc.stdout + proc.stderr
    result_dir = next((tmp_path / "results").glob("simple-bugfix*"))
    for arm in ("kiro-default", "kiro-team"):
        assert (result_dir / arm / "changes.patch").exists()
        assert (result_dir / arm / "changed-files.txt").read_text() == ""
    warnings = json.loads((result_dir / "metrics.json").read_text())["warnings"]
    assert "kiro-team changed no files (did the agent halt?)" in warnings


def test_hypothesis_judged_on_its_metric(tmp_path):
    scenario_dir = tmp_path / "simple"
    scenario_dir.mkdir()
    (scenario_dir / "metrics.json").write_text(json.dumps({
        "scenario": {"id": "s", "name": "S", "expected_winner": "kiro-default", "hypothesis_metric": "time"},
        "kiro_default": {}, "kiro_team": {},
        "comparison": {"time_winner": "kiro-default", "credits_winner": "n/a"},
    }))
    (scenario_dir / "acceptance.json").write_text(json.dumps({
        "kiro_default": {"score": 100}, "kiro_team": {"score": 100}, "quality_winner": "tie",
    }))
    text = report.generate_report(report.load_results(tmp_path))
    assert "**Hypothesis accuracy:** 1/1 (100% correct)" in text
