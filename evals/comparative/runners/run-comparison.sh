#!/bin/bash
# Run a scenario on both kiro-default and kiro-team, collect metrics
# Usage: ./run-comparison.sh <scenario.yaml> [--model <model>]
#        ./run-comparison.sh --all [--model <model>]
#
# Examples:
#   ./run-comparison.sh scenarios/simple-bugfix.yaml
#   ./run-comparison.sh scenarios/simple-bugfix.yaml --model claude-sonnet-4
#   ./run-comparison.sh --all --model claude-sonnet-4
#
# A failed agent run is still scored (a crash is a real result), but its exit
# code is recorded in exit_code.txt and shows up as a warning in metrics.json
# and the report.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EVAL_DIR="$(dirname "$SCRIPT_DIR")"
SCENARIOS_DIR="$EVAL_DIR/scenarios"
RESULTS_DIR="${EVAL_RESULTS_DIR:-$EVAL_DIR/results}"
# shellcheck source=SCRIPTDIR/common.sh
source "$SCRIPT_DIR/common.sh"

MODEL=""
RUN_ALL=false
SCENARIO=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="${2:-}"
            shift 2
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        -*)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
        *)
            SCENARIO="$1"
            shift
            ;;
    esac
done

validate_model "$MODEL"

# Both arms must run the same model, or the comparison measures the model
# difference too. With no --model, use the model the team agents pin.
if [[ -z "$MODEL" ]]; then
    MODEL="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1])).get("model", ""))' \
        "$EVAL_DIR/../../.kiro/agents/team-lead.json")"
    if [[ -z "$MODEL" ]]; then
        echo "ERROR: no --model given and team-lead.json pins none" >&2
        exit 1
    fi
    validate_model "$MODEL"
    echo "No --model given; using team-lead's model for both arms: $MODEL"
fi

# Delete a workspace. find avoids a recursive force-remove.
cleanup_workspace() {
    find "$1" -type f -delete 2>/dev/null || true
    find "$1" -depth -type d -empty -delete 2>/dev/null || true
}

# Save everything the agent changed since eval-base (committed, staged,
# unstaged and new files) as changes.patch, plus a file list.
save_changes() {
    local ws="$1" out="$2"
    git -C "$ws" add -A >/dev/null 2>&1 || true
    git -C "$ws" diff --binary --cached eval-base > "$out/changes.patch" 2>/dev/null || true
    git -C "$ws" diff --cached --name-status eval-base > "$out/changed-files.txt" 2>/dev/null || true
}

run_scenario() {
    local scenario="$1"
    local scenario_id result_dir ws_default ws_team status_default=0 status_team=0
    scenario_id=$(basename "$scenario" .yaml)
    result_dir="$RESULTS_DIR/${scenario_id}${MODEL:+-$MODEL}"

    echo "========================================"
    echo "Scenario: $scenario_id"
    [[ -n "$MODEL" ]] && echo "Model: $MODEL"
    echo "========================================"

    # Isolated workspaces: fixture copied in, committed, tagged eval-base
    ws_default=$(mktemp -d)
    ws_team=$(mktemp -d)
    python3 "$EVAL_DIR/metrics/check_acceptance.py" --scenario "$scenario" --prepare "$ws_default"
    python3 "$EVAL_DIR/metrics/check_acceptance.py" --scenario "$scenario" --prepare "$ws_team"

    echo "Workspaces:"
    echo "  kiro-default: $ws_default"
    echo "  kiro-team:    $ws_team"

    mkdir -p "$result_dir"

    echo ""
    echo "--- Running kiro-default ---"
    "$SCRIPT_DIR/run-kiro-default.sh" "$scenario" "$ws_default" "$result_dir/kiro-default" "$MODEL" \
        || status_default=$?

    echo ""
    echo "--- Running kiro-team ---"
    "$SCRIPT_DIR/run-kiro-team.sh" "$scenario" "$ws_team" "$result_dir/kiro-team" "$MODEL" \
        || status_team=$?

    if [[ ! -f "$result_dir/kiro-team/exit_code.txt" ]]; then
        # The runner stopped before kiro-cli started (e.g. agents missing).
        echo "ERROR: kiro-team runner failed before the agent ran (exit $status_team)" >&2
        cleanup_workspace "$ws_default"
        cleanup_workspace "$ws_team"
        return 1
    fi
    [[ $status_default -ne 0 ]] && echo "WARNING: kiro-default exited with $status_default"
    [[ $status_team -ne 0 ]] && echo "WARNING: kiro-team exited with $status_team"

    # Keep what each agent changed: the workspaces are deleted at the end.
    save_changes "$ws_default" "$result_dir/kiro-default"
    save_changes "$ws_team" "$result_dir/kiro-team"

    echo ""
    echo "--- Collecting metrics ---"
    python3 "$EVAL_DIR/metrics/collect.py" \
        --scenario "$scenario" \
        --default-logs "$result_dir/kiro-default" \
        --team-logs "$result_dir/kiro-team" \
        --output "$result_dir/metrics.json"

    echo ""
    echo "--- Checking acceptance criteria ---"
    python3 "$EVAL_DIR/metrics/check_acceptance.py" \
        --scenario "$scenario" \
        --default-workspace "$ws_default" \
        --team-workspace "$ws_team" \
        --output "$result_dir/acceptance.json"

    cleanup_workspace "$ws_default"
    cleanup_workspace "$ws_team"

    echo ""
    echo "Results: $result_dir/"
    echo "========================================"
}

if [[ "$RUN_ALL" == true ]]; then
    echo "Running all comparative scenarios..."
    [[ -n "$MODEL" ]] && echo "Using model: $MODEL"
    for scenario in "$SCENARIOS_DIR"/*.yaml; do
        run_scenario "$scenario"
        echo ""
    done

    echo "Generating comparison report..."
    python3 "$EVAL_DIR/metrics/report.py" "$RESULTS_DIR" > "$RESULTS_DIR/comparison-report.md"
    echo "Report: $RESULTS_DIR/comparison-report.md"
else
    if [[ -z "$SCENARIO" ]]; then
        echo "Usage: $0 <scenario.yaml> [--model <model>]"
        echo "       $0 --all [--model <model>]"
        echo ""
        echo "Available scenarios:"
        for f in "$SCENARIOS_DIR"/*.yaml; do basename "$f" .yaml; done
        exit 1
    fi

    run_scenario "$SCENARIO"
fi
