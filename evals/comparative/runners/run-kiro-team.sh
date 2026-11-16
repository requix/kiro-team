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

# Provision the workspace the way kiro-team expects to run:
# - .kiro/agents, .kiro/steering, .kiro/templates: agent configs, the
#   constraints every agent loads, and the incident template
# - scripts/worktree-*.sh: team-lead's first step creates a worktree, and its
#   last step merges it back
# - specs/<scenario>.md: team-lead executes a plan from specs/
for dir in agents steering templates; do
    if [[ -d "$REPO_ROOT/.kiro/$dir" ]]; then
        mkdir -p "$WORKSPACE/.kiro/$dir"
        cp -r "$REPO_ROOT/.kiro/$dir"/. "$WORKSPACE/.kiro/$dir/"
    fi
done
mkdir -p "$WORKSPACE/scripts" "$WORKSPACE/specs"
cp "$REPO_ROOT/scripts/worktree-create.sh" "$REPO_ROOT/scripts/worktree-merge.sh" "$WORKSPACE/scripts/"

SCENARIO_ID="$(basename "$SCENARIO" .yaml)"
PLAN="specs/$SCENARIO_ID.md"
{
    echo "# $SCENARIO_ID"
    echo ""
    scenario_task "$SCENARIO"
} > "$WORKSPACE/$PLAN"
echo ".worktrees/" >> "$WORKSPACE/.git/info/exclude"

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

# Commit the setup and move eval-base onto it, so acceptance checks and the
# saved diff show only what the agents changed.
git -C "$WORKSPACE" add -A
git -C "$WORKSPACE" -c user.name=eval -c user.email=eval@example.invalid \
    commit -q -m "kiro-team setup"
git -C "$WORKSPACE" tag -f eval-base >/dev/null
echo "Provisioned kiro-team workspace (agents, steering, scripts, $PLAN)"

# Same task text as kiro-default, delivered the way team-lead takes work: as a plan.
TASK="Execute the plan in $PLAN."

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
# --output-format stream-json writes ACP events as JSON Lines (implies --no-interactive)
cd "$WORKSPACE"
status=0
RUN_MODEL="$MODEL" run_kiro "$LOG_DIR" \
    --agent team-lead \
    ${MODEL_ARGS[@]+"${MODEL_ARGS[@]}"} \
    --trust-all-tools \
    --no-interactive \
    --output-format stream-json \
    "$TASK" || status=$?

echo "=== kiro-team complete (exit $status) ==="
echo "Logs: $LOG_DIR/"
exit "$status"
