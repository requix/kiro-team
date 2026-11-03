#!/bin/bash
# Run a scenario using kiro-default (standard kiro-cli single-agent mode)
# Usage: ./run-kiro-default.sh <scenario.yaml> <workspace> [log_dir]

set -e

SCENARIO="$1"
WORKSPACE="$2"
LOG_DIR="${3:-results/$(basename "$SCENARIO" .yaml)/kiro-default}"

if [[ -z "$SCENARIO" || -z "$WORKSPACE" ]]; then
    echo "Usage: $0 <scenario.yaml> <workspace> [log_dir]"
    exit 1
fi

mkdir -p "$LOG_DIR"

# Extract task from scenario
TASK=$(python3 -c "
import yaml
with open('$SCENARIO') as f:
    data = yaml.safe_load(f)
    print(data['task'])
")

echo "=== Running kiro-default ===" | tee "$LOG_DIR/run.log"
echo "Scenario: $SCENARIO" | tee -a "$LOG_DIR/run.log"
echo "Workspace: $WORKSPACE" | tee -a "$LOG_DIR/run.log"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_DIR/run.log"

START_TIME=$(date +%s)

# Run kiro-cli with default agent in non-interactive mode
# --trust-all-tools allows autonomous operation
# --no-interactive runs without user input
# --output-format stream-json captures structured output
cd "$WORKSPACE"
kiro-cli chat \
    --agent kiro_default \
    --trust-all-tools \
    --no-interactive \
    --output-format stream-json \
    "$TASK" \
    2>&1 | tee "$LOG_DIR/output.log"

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "Finished: $(date -Iseconds)" | tee -a "$LOG_DIR/run.log"
echo "Duration: ${DURATION}s" | tee -a "$LOG_DIR/run.log"

# Save timing
echo "$DURATION" > "$LOG_DIR/duration.txt"

echo "=== kiro-default complete ==="
echo "Logs: $LOG_DIR/"
