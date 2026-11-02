#!/usr/bin/env bash
#
# validate-agents.sh - Static validation for kiro-team agent configurations
#
# Runs L1 (syntax) and L2 (schema) validation. For L3+ semantic validation,
# use the @validate-agents skill which performs LLM-based analysis.
#
# Usage:
#   bash scripts/validate-agents.sh          # Run all static checks
#   bash scripts/validate-agents.sh --json   # Output JSON results
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
#
# Dependencies:
#   - python3 with json module (standard library)
#   - Optional: shellcheck for shell script linting
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENTS_DIR="$PROJECT_ROOT/.kiro/agents"

# Colors (disabled if not a terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    NC='\033[0m' # No Color
else
    RED=''
    GREEN=''
    YELLOW=''
    BLUE=''
    NC=''
fi

# Helper function to parse JSON using Python (more portable than jq)
# Uses command line args to pass values to Python (heredoc variable interpolation is unreliable)
json_get() {
    local file="$1"
    local key="$2"
    python3 -c '
import json, sys, os
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    keys = sys.argv[2].split(".")
    result = data
    for k in keys:
        if k and k in result:
            result = result[k]
        else:
            os._exit(1)
    if isinstance(result, (list, dict)):
        print(json.dumps(result, sort_keys=True))
    else:
        print(result)
except SystemExit:
    raise
except:
    os._exit(1)
' "$file" "$key" 2>/dev/null
}

json_valid() {
    local file="$1"
    python3 -c '
import json, sys, os
try:
    json.load(open(sys.argv[1]))
    os._exit(0)
except SystemExit:
    raise
except Exception as e:
    print(str(e))
    os._exit(1)
' "$file" 2>&1
}

json_has_key() {
    local file="$1"
    local key="$2"
    python3 -c '
import json, sys, os
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
    keys = sys.argv[2].split(".")
    result = data
    for k in keys:
        if k and k in result:
            result = result[k]
        else:
            os._exit(1)
    os._exit(0)
except SystemExit:
    raise
except:
    os._exit(1)
' "$file" "$key" 2>/dev/null
}

# Counters
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

# Results array for JSON output
declare -a RESULTS=()

# Parse arguments
JSON_OUTPUT=false
if [[ "${1:-}" == "--json" ]]; then
    JSON_OUTPUT=true
fi

log_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${GREEN}✓${NC} $1"
    fi
    RESULTS+=("{\"check\": \"$1\", \"status\": \"pass\"}")
}

log_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${RED}✗${NC} $1"
    fi
    RESULTS+=("{\"check\": \"$1\", \"status\": \"fail\", \"message\": \"$2\"}")
}

log_warn() {
    WARN_COUNT=$((WARN_COUNT + 1))
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo -e "${YELLOW}!${NC} $1"
    fi
    RESULTS+=("{\"check\": \"$1\", \"status\": \"warn\", \"message\": \"$2\"}")
}

log_section() {
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo ""
        echo -e "${BLUE}## $1${NC}"
    fi
}

# L1: Syntax Validation
validate_json_syntax() {
    log_section "L1: JSON Syntax Validation"
    
    for config in "$AGENTS_DIR"/*.json; do
        if [[ -f "$config" ]]; then
            name=$(basename "$config")
            if error=$(json_valid "$config"); then
                log_pass "JSON valid: $name"
            else
                log_fail "JSON invalid: $name" "$error"
            fi
        fi
    done
}

validate_shell_syntax() {
    log_section "L1: Shell Script Syntax"
    
    for script in "$PROJECT_ROOT"/scripts/*.sh; do
        if [[ -f "$script" ]]; then
            name=$(basename "$script")
            # Basic bash syntax check
            if bash -n "$script" 2>/dev/null; then
                log_pass "Bash syntax valid: $name"
            else
                error=$(bash -n "$script" 2>&1 || true)
                log_fail "Bash syntax invalid: $name" "$error"
            fi
            
            # ShellCheck if available
            if command -v shellcheck &>/dev/null; then
                if shellcheck -S error "$script" 2>/dev/null; then
                    log_pass "ShellCheck passed: $name"
                else
                    log_warn "ShellCheck warnings: $name" "Run shellcheck for details"
                fi
            fi
        fi
    done
}

# L2: Schema Validation
validate_schema() {
    log_section "L2: Schema Validation"
    
    local required_fields=("name" "description" "prompt" "tools" "allowedTools" "model")
    
    for config in "$AGENTS_DIR"/*.json; do
        if [[ -f "$config" ]]; then
            name=$(basename "$config" .json)
            
            # Check required fields
            for field in "${required_fields[@]}"; do
                if json_has_key "$config" "$field"; then
                    log_pass "$name: has '$field'"
                else
                    log_fail "$name: missing '$field'" "Required field not found"
                fi
            done
            
            # Check name matches filename
            config_name=$(json_get "$config" "name")
            if [[ "$config_name" == "$name" ]]; then
                log_pass "$name: name matches filename"
            else
                log_fail "$name: name mismatch" "Config says '$config_name' but file is '$name.json'"
            fi
            
            # Check prompt file exists
            prompt_ref=$(json_get "$config" "prompt")
            if [[ "$prompt_ref" == file://./* ]]; then
                prompt_file="${prompt_ref#file://./}"
                prompt_path="$AGENTS_DIR/$prompt_file"
                if [[ -f "$prompt_path" ]]; then
                    log_pass "$name: prompt file exists ($prompt_file)"
                else
                    log_fail "$name: prompt file missing" "$prompt_path not found"
                fi
            else
                log_fail "$name: invalid prompt reference" "Should be file://./filename.md"
            fi
            
            # Check tools and allowedTools match
            tools=$(json_get "$config" "tools")
            allowed=$(json_get "$config" "allowedTools")
            if [[ "$tools" == "$allowed" ]]; then
                log_pass "$name: tools matches allowedTools"
            else
                log_warn "$name: tools/allowedTools mismatch" "tools: $tools, allowedTools: $allowed"
            fi
            
            # Check subagent has trustedAgents
            if json_get "$config" "tools" | grep -q "subagent"; then
                if json_has_key "$config" "toolsSettings.subagent.trustedAgents"; then
                    log_pass "$name: subagent has trustedAgents configured"
                else
                    log_fail "$name: subagent missing trustedAgents" "Required when tools includes subagent"
                fi
            fi
        fi
    done
}

# Check prompt file structure
validate_prompts() {
    log_section "L2: Prompt Structure"
    
    for prompt in "$AGENTS_DIR"/*-prompt.md; do
        if [[ -f "$prompt" ]]; then
            name=$(basename "$prompt" -prompt.md)
            
            # Check for Purpose section
            if grep -q "^## Purpose" "$prompt" || grep -q "^# .*Purpose" "$prompt"; then
                log_pass "$name: has Purpose section"
            else
                log_warn "$name: missing Purpose section" "Prompts should have a ## Purpose section"
            fi
            
            # Check for Instructions section
            if grep -q "^## Instructions" "$prompt" || grep -q "^## Workflow" "$prompt"; then
                log_pass "$name: has Instructions/Workflow section"
            else
                log_warn "$name: missing Instructions section" "Prompts should have a ## Instructions section"
            fi
            
            # Check for boundaries/rules
            if grep -qi "must not\|do not\|never\|## Rules" "$prompt"; then
                log_pass "$name: has boundary constraints"
            else
                log_warn "$name: missing boundary constraints" "Consider adding ## Rules or explicit restrictions"
            fi
            
            # Check file is not empty
            if [[ -s "$prompt" ]]; then
                lines=$(wc -l < "$prompt")
                if [[ $lines -ge 20 ]]; then
                    log_pass "$name: prompt has $lines lines"
                else
                    log_warn "$name: prompt only has $lines lines" "Consider adding more detail"
                fi
            else
                log_fail "$name: prompt file is empty" "Prompt file has no content"
            fi
        fi
    done
}

# Summary
print_summary() {
    if [[ "$JSON_OUTPUT" == true ]]; then
        echo "{"
        echo "  \"pass\": $PASS_COUNT,"
        echo "  \"fail\": $FAIL_COUNT,"
        echo "  \"warn\": $WARN_COUNT,"
        echo "  \"results\": ["
        printf "    %s\n" "${RESULTS[@]}" | sed '$ ! s/$/,/'
        echo "  ]"
        echo "}"
    else
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${BLUE}Validation Summary${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "  ${GREEN}Passed${NC}: $PASS_COUNT"
        echo -e "  ${RED}Failed${NC}: $FAIL_COUNT"
        echo -e "  ${YELLOW}Warnings${NC}: $WARN_COUNT"
        echo ""
        
        if [[ $FAIL_COUNT -eq 0 ]]; then
            echo -e "${GREEN}✓ All static checks passed${NC}"
            echo ""
            echo "For semantic (L3+) validation, run: @validate-agents"
        else
            echo -e "${RED}✗ Validation failed - fix errors before proceeding${NC}"
        fi
    fi
}

# Main
main() {
    if [[ "$JSON_OUTPUT" == false ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "kiro-team Agent Validation (L1-L2)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    fi
    
    validate_json_syntax
    validate_shell_syntax
    validate_schema
    validate_prompts
    print_summary
    
    if [[ $FAIL_COUNT -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
