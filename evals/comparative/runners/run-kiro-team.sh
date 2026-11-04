#!/bin/bash
# Run a scenario using kiro-team (multi-agent orchestration)
# Usage: ./run-kiro-team.sh <scenario.yaml> <workspace> [log_dir] [model]

set -e

SCENARIO="$1"
WORKSPACE="$2"
LOG_DIR="${3:-results/$(basename "$SCENARIO" .yaml)/kiro-team}"
MODEL="${4:-}"  # Optional model override (e.g., claude-sonnet-4, claude-opus-4)

if [[ -z "$SCENARIO" || -z "$WORKSPACE" ]]; then
    echo "Usage: $0 <scenario.yaml> <workspace> [log_dir] [model]"
    exit 1
fi

mkdir -p "$LOG_DIR"

# Copy kiro-team workspace agents to the test workspace
# This makes team-lead, builder, validator, documenter available
KIRO_TEAM_AGENTS="/home/kirocrew/projects/kiro-team/.kiro/agents"
KIRO_TEAM_SCRIPTS="/home/kirocrew/projects/kiro-team/.kiro/scripts"

if [[ -d "$KIRO_TEAM_AGENTS" ]]; then
    mkdir -p "$WORKSPACE/.kiro/agents"
    cp -r "$KIRO_TEAM_AGENTS"/* "$WORKSPACE/.kiro/agents/"
    echo "Copied kiro-team agents to workspace"
    
    # Copy scripts (includes jev_precheck.py)
    if [[ -d "$KIRO_TEAM_SCRIPTS" ]]; then
        mkdir -p "$WORKSPACE/.kiro/scripts"
        cp -r "$KIRO_TEAM_SCRIPTS"/* "$WORKSPACE/.kiro/scripts/"
        echo "Copied kiro-team scripts to workspace"
    fi
    
    # If model is specified, update agent configs to use it
    # Exception: builder-fast keeps its cheap model for complexity routing
    if [[ -n "$MODEL" ]]; then
        for agent_json in "$WORKSPACE/.kiro/agents"/*.json; do
            if [[ -f "$agent_json" ]]; then
                agent_name=$(basename "$agent_json" .json)
                # Keep builder-fast on its cheap model (Haiku) for complexity routing optimization
                if [[ "$agent_name" == "builder-fast" || "$agent_name" == "validator-fast" ]]; then
                    echo "Keeping $agent_name on cheap model for speed"
                    continue
                fi
                # Replace the model field in each agent config
                python3 -c "
import json
with open('$agent_json', 'r') as f:
    data = json.load(f)
data['model'] = '$MODEL'
with open('$agent_json', 'w') as f:
    json.dump(data, f, indent=2)
"
            fi
        done
        echo "Updated agent configs to use model: $MODEL (except fast agents)"
    fi
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
[[ -n "$MODEL" ]] && echo "Model: $MODEL" | tee -a "$LOG_DIR/run.log"
echo "Started: $(date -Iseconds)" | tee -a "$LOG_DIR/run.log"

START_TIME=$(date +%s)

# Build model flag if specified (for team-lead's own model)
MODEL_FLAG=""
if [[ -n "$MODEL" ]]; then
    MODEL_FLAG="--model $MODEL"
fi

# Run kiro-cli with team-lead agent
# Team-lead will orchestrate builder/validator/documenter as needed
# --trust-all-tools allows autonomous operation
# --no-interactive runs without user input
# --trust-workspace trusts the workspace agents
cd "$WORKSPACE"
kiro-cli chat \
    --agent team-lead \
    $MODEL_FLAG \
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
