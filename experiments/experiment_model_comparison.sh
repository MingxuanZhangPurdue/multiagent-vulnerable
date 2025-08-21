#!/bin/bash

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/run_user_tasks.py"

# declare -a SUITES=("slack" "banking" "workspace" "travel")
declare -a SUITES=("travel")

declare -a EXECUTOR_PROMPTS=(
    "experiments/prompts/prompt1.txt"
    "experiments/prompts/prompt2.txt"
    "experiments/prompts/prompt3.txt"
    "experiments/prompts/prompt4.txt"
    "experiments/prompts/prompt5.txt"
)

run_experiment() {
    local suite="$1"
    local planner_model="$2"
    local executor_model="$3"
    local prompt_file="$4"

    python "$PYTHON_SCRIPT" \
        --suite "$suite" \
        --structure "planner_executor" \
        --memory-type "shared_memory" \
        --planner-model "$planner_model" \
        --executor-model "$executor_model" \
        --executor-prompt-file "$prompt_file" \
        --log-path "results/model_comparison" 

    # python "$PYTHON_SCRIPT" \
    #     --suite "$suite" \
    #     --structure "handoffs" \
    #     --memory-type "shared_memory" \
    #     --planner-model "$planner_model" \
    #     --executor-model "$executor_model" \
    #     --executor-prompt-file "$prompt_file" \
    #     --log-path "results/model_comparison" 
}

# Function to run cross-provider experiments (different planner/executor combinations)
run_cross_provider_experiments() {
    local suite="$1"
    local -a prompts=()

    mkdir -p "results/model_comparison/planner_executor/$suite"
    mkdir -p "results/model_comparison/handoffs/$suite"


    echo "[$suite]"
    case "$suite" in
        "workspace")
            prompts=("${EXECUTOR_PROMPTS[@]:0:4}")   # prompt1–4
            ;;
        "travel")
            prompts=("${EXECUTOR_PROMPTS[4]}")  # prompt1–3 + prompt5
            ;;
        *)
            prompts=("${EXECUTOR_PROMPTS[@]}")  # 默认全跑
            ;;
    esac

    for prompt_file in "${prompts[@]}"; do
        run_experiment "$suite" "gpt-5-mini" "gpt-5-mini" "$prompt_file"
    done

    # run_experiment "$suite" "gpt-5" "gpt-5"
    # run_experiment "$suite" "gpt-5" "gpt-5-mini"
    # run_experiment "$suite" "gpt-5" "gpt-5-nano"
    # run_experiment "$suite" "gpt-5-mini" "gpt-5-mini"
    # run_experiment "$suite" "gpt-5-mini" "gpt-5-nano"
    # run_experiment "$suite" "gpt-5-nano" "gpt-5-nano"
}

for suite in "${SUITES[@]}"; do
    run_cross_provider_experiments "$suite"
done
