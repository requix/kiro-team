#!/bin/bash
# Run a scenario on both kiro-default and kiro-team, collect metrics
# Usage: ./run-comparison.sh <scenario.yaml> [--model <model>] [--all] [--jev]
#
# Examples:
#   ./run-comparison.sh scenarios/simple-bugfix.yaml
#   ./run-comparison.sh scenarios/simple-bugfix.yaml --model claude-sonnet-4
#   ./run-comparison.sh --all --model claude-sonnet-4
#   ./run-comparison.sh --all --jev  # Enable Jev pre-check in validator
#
# Environment:
#   TYPESAFE_API_KEY - Required for --jev mode (Jev validator pre-check)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
EVAL_DIR="$(dirname "$SCRIPT_DIR")"
SCENARIOS_DIR="$EVAL_DIR/scenarios"
FIXTURES_DIR="$EVAL_DIR/fixtures"
RESULTS_DIR="$EVAL_DIR/results"

# Parse arguments
MODEL=""
RUN_ALL=false
SCENARIO=""
USE_JEV=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --jev)
            USE_JEV=true
            shift
            ;;
        *)
            SCENARIO="$1"
            shift
            ;;
    esac
done

# Check Jev requirements
if [[ "$USE_JEV" == true ]]; then
    # Try to load from .env if not in environment
    if [[ -z "$TYPESAFE_API_KEY" ]]; then
        ENV_FILE="/home/kirocrew/projects/kiro-team/.env"
        if [[ -f "$ENV_FILE" ]]; then
            export $(grep -E '^TYPESAFE_API_KEY=' "$ENV_FILE" | xargs)
        fi
    fi
    
    if [[ -z "$TYPESAFE_API_KEY" ]]; then
        echo "ERROR: --jev requires TYPESAFE_API_KEY"
        echo "Set it in /home/kirocrew/projects/kiro-team/.env or environment"
        exit 1
    fi
    echo "Jev pre-check enabled for validator"
fi

run_scenario() {
    local SCENARIO="$1"
    local SCENARIO_ID=$(basename "$SCENARIO" .yaml)
    
    # Add model suffix to results dir if model specified
    local RESULT_SUFFIX=""
    if [[ -n "$MODEL" ]]; then
        RESULT_SUFFIX="-${MODEL}"
    fi
    if [[ "$USE_JEV" == true ]]; then
        RESULT_SUFFIX="${RESULT_SUFFIX}-jev"
    fi
    local RESULT_DIR="$RESULTS_DIR/${SCENARIO_ID}${RESULT_SUFFIX}"
    
    echo "========================================"
    echo "Scenario: $SCENARIO_ID"
    [[ -n "$MODEL" ]] && echo "Model: $MODEL"
    echo "========================================"
    
    # Extract fixture path
    local FIXTURE=$(python3 -c "
import yaml
with open('$SCENARIO') as f:
    data = yaml.safe_load(f)
    print(data.get('fixture', ''))
")
    
    if [[ -z "$FIXTURE" ]]; then
        echo "ERROR: No fixture defined in $SCENARIO"
        return 1
    fi
    
    local FIXTURE_PATH="$EVAL_DIR/$FIXTURE"
    
    if [[ ! -d "$FIXTURE_PATH" ]]; then
        echo "ERROR: Fixture not found: $FIXTURE_PATH"
        echo "Create the fixture first, then rerun."
        return 1
    fi
    
    # Create isolated workspaces for each approach
    local WORKSPACE_DEFAULT=$(mktemp -d)
    local WORKSPACE_TEAM=$(mktemp -d)
    
    echo "Workspaces:"
    echo "  kiro-default: $WORKSPACE_DEFAULT"
    echo "  kiro-team:    $WORKSPACE_TEAM"
    
    # Copy fixture to both workspaces
    cp -r "$FIXTURE_PATH"/* "$WORKSPACE_DEFAULT/"
    cp -r "$FIXTURE_PATH"/* "$WORKSPACE_TEAM/"
    
    # Initialize git in both (clean slate)
    (cd "$WORKSPACE_DEFAULT" && git init && git add -A && git commit -m "initial" 2>/dev/null) || true
    (cd "$WORKSPACE_TEAM" && git init && git add -A && git commit -m "initial" 2>/dev/null) || true
    
    mkdir -p "$RESULT_DIR"
    
    # Run kiro-default
    echo ""
    echo "--- Running kiro-default ---"
    "$SCRIPT_DIR/run-kiro-default.sh" "$SCENARIO" "$WORKSPACE_DEFAULT" "$RESULT_DIR/kiro-default" "$MODEL" || true
    
    # Run kiro-team
    echo ""
    echo "--- Running kiro-team ---"
    "$SCRIPT_DIR/run-kiro-team.sh" "$SCENARIO" "$WORKSPACE_TEAM" "$RESULT_DIR/kiro-team" "$MODEL" || true
    
    # Collect metrics
    echo ""
    echo "--- Collecting metrics ---"
    python3 "$EVAL_DIR/metrics/collect.py" \
        --scenario "$SCENARIO" \
        --default-logs "$RESULT_DIR/kiro-default" \
        --team-logs "$RESULT_DIR/kiro-team" \
        --output "$RESULT_DIR/metrics.json"
    
    # Run acceptance checks
    echo ""
    echo "--- Checking acceptance criteria ---"
    python3 "$EVAL_DIR/metrics/check_acceptance.py" \
        --scenario "$SCENARIO" \
        --default-workspace "$WORKSPACE_DEFAULT" \
        --team-workspace "$WORKSPACE_TEAM" \
        --output "$RESULT_DIR/acceptance.json"
    
    # Cleanup workspaces (keep results)
    # Note: Using explicit paths with find to avoid rm -rf
    find "$WORKSPACE_DEFAULT" -type f -delete 2>/dev/null || true
    find "$WORKSPACE_DEFAULT" -type d -empty -delete 2>/dev/null || true
    find "$WORKSPACE_TEAM" -type f -delete 2>/dev/null || true
    find "$WORKSPACE_TEAM" -type d -empty -delete 2>/dev/null || true
    
    echo ""
    echo "Results: $RESULT_DIR/"
    echo "========================================"
}

if [[ "$RUN_ALL" == true ]]; then
    echo "Running all comparative scenarios..."
    [[ -n "$MODEL" ]] && echo "Using model: $MODEL"
    for scenario in "$SCENARIOS_DIR"/*.yaml; do
        run_scenario "$scenario"
        echo ""
    done
    
    # Generate combined report
    echo "Generating comparison report..."
    python3 "$EVAL_DIR/metrics/report.py" "$RESULTS_DIR" > "$RESULTS_DIR/comparison-report.md"
    echo "Report: $RESULTS_DIR/comparison-report.md"
else
    if [[ -z "$SCENARIO" ]]; then
        echo "Usage: $0 <scenario.yaml> [--model <model>]"
        echo "       $0 --all [--model <model>]"
        echo ""
        echo "Models: claude-sonnet-4, claude-opus-4, etc."
        echo ""
        echo "Available scenarios:"
        ls -1 "$SCENARIOS_DIR"/*.yaml 2>/dev/null | xargs -I{} basename {} .yaml
        exit 1
    fi
    
    run_scenario "$SCENARIO"
fi
