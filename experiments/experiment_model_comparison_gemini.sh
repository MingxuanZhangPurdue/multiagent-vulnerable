#!/bin/bash

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/run_user_tasks.py"

declare -a SUITES=("slack" "banking" "workspace" "travel")

run_experiment() {
    local suite="$1"
    local planner_model="$2"
    local executor_model="$3"

    python "$PYTHON_SCRIPT" \
        --suite "$suite" \
        --structure "planner_executor" \
        --memory-type "shared_memory" \
        --planner-model "$planner_model" \
        --executor-model "$executor_model" \
        --log-path "results/model_comparison" 

    python "$PYTHON_SCRIPT" \
        --suite "$suite" \
        --structure "handoffs" \
        --memory-type "shared_memory" \
        --planner-model "$planner_model" \
        --executor-model "$executor_model" \
        --log-path "results/model_comparison" 
}

# Function to run cross-provider experiments (different planner/executor combinations)
run_cross_provider_experiments() {
    local suite="$1"

    mkdir -p "results/model_comparison/planner_executor/$suite"
    mkdir -p "results/model_comparison/handoffs/$suite"

    run_experiment "$suite" "gemini-2.5-pro" "gemini-2.5-pro"
    run_experiment "$suite" "gemini-2.5-pro" "gemini-2.5-flash"
    run_experiment "$suite" "gemini-2.5-pro" "gemini-2.0-flash"
    run_experiment "$suite" "gemini-2.5-flash" "gemini-2.5-flash"
    run_experiment "$suite" "gemini-2.5-flash" "gemini-2.0-flash"
    run_experiment "$suite" "gemini-2.0-flash" "gemini-2.0-flash"

}

for suite in "${SUITES[@]}"; do
    run_cross_provider_experiments "$suite"
done
