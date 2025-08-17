#!/bin/bash

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/run_user_tasks.py"

declare -a SUITES=("workspace" "banking" "slack" "travel")

run_experiment() {
    local suite="$1"
    local planner_model="$2"
    local executor_model="$3"
    local memory_type="$4"

    python "$PYTHON_SCRIPT" \
        --suite "$suite" \
        --structure "planner_executor" \
        --memory-type "$memory_type" \
        --planner-model "$planner_model" \
        --executor-model "$executor_model" \
        --log-path "results/memory_comparison" 
}

# Function to run memory experiments with different configurations
run_memory_experiments() {
    local suite="$1"

    # Test different memory configurations with gpt-4o-mini
    run_experiment "$suite" "gpt-4o-mini" "gpt-4o-mini" "no_memory"
    run_experiment "$suite" "gpt-4o-mini" "gpt-4o-mini" "shared_memory"
    run_experiment "$suite" "gpt-4o-mini" "gpt-4o-mini" "no_executor_memory"
    
    # Test different memory configurations with gemini models
    run_experiment "$suite" "gemini-2.5-pro" "gemini-2.5-flash" "no_memory"
    run_experiment "$suite" "gemini-2.5-pro" "gemini-2.5-flash" "shared_memory"
    run_experiment "$suite" "gemini-2.5-pro" "gemini-2.5-flash" "no_executor_memory"
    
    # Test different memory configurations with claude models
    run_experiment "$suite" "claude-sonnet-4" "claude-3.7" "no_memory"
    run_experiment "$suite" "claude-sonnet-4" "claude-3.7" "shared_memory"
    run_experiment "$suite" "claude-sonnet-4" "claude-3.7" "no_executor_memory"
}

for suite in "${SUITES[@]}"; do
    run_memory_experiments "$suite"
done