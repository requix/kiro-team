#!/bin/bash
# Run a scenario using kiro-default (standard kiro-cli single-agent mode)
# Usage: ./run-kiro-default.sh <scenario.yaml> <workspace> [log_dir] [model]
# Exits with kiro-cli's exit code.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=SCRIPTDIR/common.sh
source "$SCRIPT_DIR/common.sh"

SCENARIO="${1:-}"
WORKSPACE="${2:-}"
if [[ -z "$SCENARIO" || -z "$WORKSPACE" ]]; then
    echo "Usage: $0 <scenario.yaml> <workspace> [log_dir] [model]"
    exit 1
fi
LOG_DIR="${3:-results/$(basename "$SCENARIO" .yaml)/kiro-default}"
MODEL="${4:-}"  # Optional model override (e.g., claude-sonnet-4)
validate_model "$MODEL"

SCENARIO="$(cd "$(dirname "$SCENARIO")" && pwd)/$(basename "$SCENARIO")"
mkdir -p "$LOG_DIR"
LOG_DIR="$(cd "$LOG_DIR" && pwd)"

TASK="$(scenario_task "$SCENARIO")"

{
    echo "=== Running kiro-default ==="
    echo "Scenario: $SCENARIO"
    echo "Workspace: $WORKSPACE"
    [[ -n "$MODEL" ]] && echo "Model: $MODEL"
    echo "Started: $(date -Iseconds)"
} | tee "$LOG_DIR/run.log"

MODEL_ARGS=()
[[ -n "$MODEL" ]] && MODEL_ARGS=(--model "$MODEL")

# --trust-all-tools allows autonomous operation
# --output-format stream-json writes ACP events as JSON Lines (implies --no-interactive)
cd "$WORKSPACE"
status=0
run_kiro "$LOG_DIR" \
    --agent kiro_default \
    "${MODEL_ARGS[@]}" \
    --trust-all-tools \
    --no-interactive \
    --output-format stream-json \
    "$TASK" || status=$?

echo "=== kiro-default complete (exit $status) ==="
echo "Logs: $LOG_DIR/"
exit "$status"
