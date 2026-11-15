#!/bin/bash
# Shared helpers for the comparative runners. Source this file; do not run it.

# Model ids go into file paths and agent configs, so only allow plain ids.
validate_model() {
    local model="$1"
    if [[ -n "$model" && ! "$model" =~ ^[A-Za-z0-9._-]+$ ]]; then
        echo "ERROR: invalid model id: '$model' (allowed: letters, digits, . _ -)" >&2
        return 1
    fi
}

# Print the scenario's task text. The path is passed as an argument, never
# spliced into Python source.
scenario_task() {
    python3 - "$1" <<'PY'
import sys
import yaml

with open(sys.argv[1]) as f:
    print(yaml.safe_load(f)["task"])
PY
}

# Run kiro-cli, tee its output to the log, and record timing and exit code.
# Usage: run_kiro <log_dir> <kiro-cli chat args...>
# Returns kiro-cli's exit code, not tee's.
run_kiro() {
    local log_dir="$1"
    shift
    local start end status
    start=$(date +%s)
    set +e
    kiro-cli chat "$@" 2>&1 | tee "$log_dir/output.log"
    status=${PIPESTATUS[0]}
    set -e
    end=$(date +%s)

    echo "Finished: $(date -Iseconds)" | tee -a "$log_dir/run.log"
    echo "Duration: $((end - start))s" | tee -a "$log_dir/run.log"
    echo "Exit code: $status" | tee -a "$log_dir/run.log"
    echo "$((end - start))" > "$log_dir/duration.txt"
    echo "$status" > "$log_dir/exit_code.txt"
    return "$status"
}
