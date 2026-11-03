#!/bin/bash
# Run a scenario using kiro-team (multi-agent orchestration)
# Usage: ./run-kiro-team.sh <scenario.yaml> <workspace> [log_dir]

set -e

SCENARIO="$1"
WORKSPACE="$2"
LOG_DIR="${3:-results/$(basename "$SCENARIO" .yaml)/kiro-team}"

if [[ -z "$SCENARIO" || -z "$WORKSPACE" ]]; then
    echo "Usage: $0 <scenario.yaml> <workspace> [log_dir]"
    exit 1
fi

mkdir -p "$LOG_DIR"

# Copy kiro-team workspace agents to the test workspace
# This makes team-lead, builder, validator, documenter available
KIRO_TEAM_AGENTS="/home/kirocrew/projects/kiro-team/.kiro/agents"
if [[ -d "$KIRO_TEAM_AGENTS" ]]; then
    mkdir -p "$WORKSPACE/.kiro/agents"
    cp -r "$KIRO_TEAM_AGENTS"/* "$WORKSPACE/.kiro/agents/"
    echo "Copied kiro-team agents to workspace"
fi

# Extract task from scenario
TASK=$(python3 -c "
import yaml
with open('$SCENARIO') as f:
    data = yaml.safe_load(f)
    print(data['task'])
")

echo "=== Running kiro-team ===" | tee "$LOG_DIR/run.log"
echo "Scenario: $SCENARIO" | tee -a "$LOG_DIR/run.log"
echo "Workspace: $WORKSPACE" | tee -a "$LOG_DIR/run.log"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_DIR/run.log"

START_TIME=$(date +%s)

# Run kiro-cli with team-lead agent
# Team-lead will orchestrate builder/validator/documenter as needed
# --trust-all-tools allows autonomous operation
# --no-interactive runs without user input
# --trust-workspace trusts the workspace agents
cd "$WORKSPACE"
kiro-cli chat \
    --agent team-lead \
    --trust-all-tools \
    --trust-workspace \
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

echo "=== kiro-team complete ==="
echo "Logs: $LOG_DIR/"
