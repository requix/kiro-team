#!/bin/bash
# Run a scenario using kiro-team (multi-agent orchestration)
# Usage: ./run-kiro-team.sh <scenario.yaml> <workspace> [log_dir] [model]
# Exits with kiro-cli's exit code. Exits 1 before running if the team agents
# are missing, so a run can never fall back to the wrong agent silently.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=SCRIPTDIR/common.sh
source "$SCRIPT_DIR/common.sh"

# The agents under test are the ones in this repo (three levels up from runners/).
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KIRO_TEAM_AGENTS="$REPO_ROOT/.kiro/agents"

SCENARIO="${1:-}"
WORKSPACE="${2:-}"
if [[ -z "$SCENARIO" || -z "$WORKSPACE" ]]; then
    echo "Usage: $0 <scenario.yaml> <workspace> [log_dir] [model]"
    exit 1
fi
LOG_DIR="${3:-results/$(basename "$SCENARIO" .yaml)/kiro-team}"
MODEL="${4:-}"  # Optional model override (e.g., claude-sonnet-4)
validate_model "$MODEL"

if [[ ! -f "$KIRO_TEAM_AGENTS/team-lead.json" ]]; then
    echo "ERROR: kiro-team agents not found at $KIRO_TEAM_AGENTS (expected team-lead.json)" >&2
    exit 1
fi

SCENARIO="$(cd "$(dirname "$SCENARIO")" && pwd)/$(basename "$SCENARIO")"
mkdir -p "$LOG_DIR"
LOG_DIR="$(cd "$LOG_DIR" && pwd)"

# Copy the team-lead, builder, validator and documenter agents into the workspace
mkdir -p "$WORKSPACE/.kiro/agents"
cp -r "$KIRO_TEAM_AGENTS"/. "$WORKSPACE/.kiro/agents/"
echo "Copied kiro-team agents to workspace"

# If a model is given, point every agent config at it. Values reach Python
# through argv, never through the source text.
if [[ -n "$MODEL" ]]; then
    for agent_json in "$WORKSPACE/.kiro/agents"/*.json; do
        python3 - "$agent_json" "$MODEL" <<'PY'
import json
import sys

path, model = sys.argv[1], sys.argv[2]
with open(path) as f:
    data = json.load(f)
data["model"] = model
with open(path, "w") as f:
    json.dump(data, f, indent=2)
PY
    done
    echo "Updated agent configs to use model: $MODEL"
fi

TASK="$(scenario_task "$SCENARIO")"

{
    echo "=== Running kiro-team ==="
    echo "Scenario: $SCENARIO"
    echo "Workspace: $WORKSPACE"
    [[ -n "$MODEL" ]] && echo "Model: $MODEL"
    echo "Started: $(date -Iseconds)"
} | tee "$LOG_DIR/run.log"

MODEL_ARGS=()
[[ -n "$MODEL" ]] && MODEL_ARGS=(--model "$MODEL")

# team-lead orchestrates builder/validator/documenter as needed
# --trust-all-tools allows autonomous operation
# --trust-workspace trusts the workspace agents
# --output-format stream-json writes ACP events as JSON Lines (implies --no-interactive)
cd "$WORKSPACE"
status=0
run_kiro "$LOG_DIR" \
    --agent team-lead \
    "${MODEL_ARGS[@]}" \
    --trust-all-tools \
    --trust-workspace \
    --no-interactive \
    --output-format stream-json \
    "$TASK" || status=$?

echo "=== kiro-team complete (exit $status) ==="
echo "Logs: $LOG_DIR/"
exit "$status"
