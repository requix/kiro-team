#!/usr/bin/env bash
#
# run-evals.sh - Run kiro-team agent evaluations
#
# This script orchestrates evaluation scenarios. For each scenario:
# 1. Sets up any required preconditions
# 2. Invokes the agent with the test prompt
# 3. Runs verification commands
# 4. Records the score
#
# Usage:
#   bash scripts/run-evals.sh                    # List scenarios
#   bash scripts/run-evals.sh <scenario-id>      # Run one scenario
#   bash scripts/run-evals.sh --all              # Run all scenarios
#   bash scripts/run-evals.sh --agent <name>     # Run scenarios for one agent
#
# Note: This is a helper for manual invocation. The full eval framework
# uses the @eval-agents skill which calls this plus LLM-based scoring.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
EVALS_DIR="$PROJECT_ROOT/.kiro/evals"
SCENARIOS_DIR="$EVALS_DIR/scenarios"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

list_scenarios() {
    echo "Available evaluation scenarios:"
    echo ""
    for agent_dir in "$SCENARIOS_DIR"/*/; do
        agent=$(basename "$agent_dir")
        echo -e "${BLUE}$agent:${NC}"
        for scenario in "$agent_dir"*.yaml; do
            if [[ -f "$scenario" ]]; then
                name=$(basename "$scenario" .yaml)
                # Extract description from yaml
                desc=$(grep -m1 "^# Scenario:" "$scenario" | sed 's/^# Scenario: //' || echo "")
                echo "  - $name: $desc"
            fi
        done
        echo ""
    done
}

show_scenario() {
    local scenario_id="$1"
    
    # Find the scenario file
    local found=""
    for agent_dir in "$SCENARIOS_DIR"/*/; do
        for scenario in "$agent_dir"*.yaml; do
            if [[ -f "$scenario" ]]; then
                id=$(grep -m1 "^id:" "$scenario" | awk '{print $2}' || basename "$scenario" .yaml)
                if [[ "$id" == "$scenario_id" ]] || [[ "$(basename "$scenario" .yaml)" == "$scenario_id" ]]; then
                    found="$scenario"
                    break 2
                fi
            fi
        done
    done
    
    if [[ -z "$found" ]]; then
        echo -e "${RED}Scenario not found: $scenario_id${NC}"
        echo ""
        list_scenarios
        exit 1
    fi
    
    echo -e "${BLUE}Scenario: $scenario_id${NC}"
    echo "File: $found"
    echo ""
    echo "--- Contents ---"
    cat "$found"
}

run_verification() {
    local scenario_file="$1"
    local status=0
    
    echo -e "\n${BLUE}Running verification commands...${NC}"
    
    # Extract verification commands
    local in_verify=false
    local in_commands=false
    
    while IFS= read -r line; do
        if [[ "$line" == "verification:" ]]; then
            in_verify=true
            continue
        fi
        
        if [[ "$in_verify" == true ]]; then
            if [[ "$line" == "  commands:" ]] || [[ "$line" == "  post_check:" ]]; then
                in_commands=true
                continue
            fi
            
            if [[ "$in_commands" == true ]] && [[ "$line" =~ ^\ {4}-\ \" ]]; then
                # Extract command from yaml list item
                cmd=$(echo "$line" | sed 's/^    - "//' | sed 's/"$//')
                echo -n "  Running: $cmd ... "
                if eval "$cmd" > /dev/null 2>&1; then
                    echo -e "${GREEN}✓${NC}"
                else
                    echo -e "${RED}✗${NC}"
                    status=1
                fi
            fi
            
            # Stop if we hit a new section
            if [[ "$line" =~ ^[a-z] ]] && [[ "$line" != "  "* ]]; then
                break
            fi
        fi
    done < "$scenario_file"
    
    return $status
}

# Main
case "${1:-}" in
    "")
        list_scenarios
        ;;
    --all)
        echo "Running all scenarios..."
        echo "(Note: Full evaluation requires @eval-agents skill for LLM scoring)"
        echo ""
        for agent_dir in "$SCENARIOS_DIR"/*/; do
            for scenario in "$agent_dir"*.yaml; do
                if [[ -f "$scenario" ]]; then
                    name=$(basename "$scenario" .yaml)
                    echo -e "${YELLOW}━━━ $name ━━━${NC}"
                    show_scenario "$name"
                    echo ""
                fi
            done
        done
        ;;
    --agent)
        agent="${2:-}"
        if [[ -z "$agent" ]]; then
            echo "Usage: $0 --agent <agent-name>"
            exit 1
        fi
        if [[ -d "$SCENARIOS_DIR/$agent" ]]; then
            echo "Scenarios for $agent:"
            for scenario in "$SCENARIOS_DIR/$agent"/*.yaml; do
                if [[ -f "$scenario" ]]; then
                    name=$(basename "$scenario" .yaml)
                    echo ""
                    show_scenario "$name"
                fi
            done
        else
            echo -e "${RED}No scenarios for agent: $agent${NC}"
            exit 1
        fi
        ;;
    *)
        show_scenario "$1"
        ;;
esac
