#!/usr/bin/env bash
# run_parallel.sh
# Pallelly run run_user_tasks.py，support multi API Key and can choose different prompt according to different suite

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/run_user_tasks.py"

CONCURRENCY=6

declare -a SUITES=("workspace")

declare -a PLANNER_MODELS=("gpt-5-mini" "gpt-5-nano")
declare -a EXECUTOR_MODELS=("gpt-5-mini" "gpt-5-nano")

LOG_ROOT="results/prompt_test"

declare -a API_KEYS=(
  "key 1"
  "key 2"
  "key 3"
  "key 4"
  "key 5"
  "key 6"
)

declare -a EXECUTOR_PROMPTS=(
  "executor_prompts/prompt1.txt"
  "executor_prompts/prompt2.txt"
  "executor_prompts/prompt3.txt"
  "executor_prompts/prompt4.txt"
  "executor_prompts/prompt5.txt"
  "executor_prompts/prompt6.txt"
  "executor_prompts/prompt7.txt"
  "executor_prompts/prompt8.txt"
  "executor_prompts/prompt9.txt"
)

declare -a PLANNER_PROMPTS=(
  "planner_prompts/prompt1.txt"
  "planner_prompts/prompt2.txt"
  "planner_prompts/prompt3.txt"
  "planner_prompts/prompt4.txt"
  "planner_prompts/prompt5.txt"
  "planner_prompts/prompt6.txt"
  "planner_prompts/prompt7.txt"
  "planner_prompts/prompt8.txt"
  "planner_prompts/prompt9.txt"
)

basename_no_ext () {
  local p="$1"
  local base
  base="$(basename -- "$p")"
  echo "${base%.*}"
}

pick_key () {
  local idx="$1"
  local n="${#API_KEYS[@]}"
  local sel=$(( idx % n ))
  echo "${API_KEYS[$sel]}"
}


suite_executor_prompts () {
  local suite="$1"
  local -n _out_arr="$2"   

  case "$suite" in
    "workspace")
      _out_arr=("${EXECUTOR_PROMPTS[@]:0:6}")  
      ;;
    "travel")
      _out_arr=("${EXECUTOR_PROMPTS[7]}")  
      ;;
  esac
}

suite_planner_prompts () {
  local suite="$1"
  local -n _out_arr="$2"   

  # case "$suite" in
  #   "workspace")
  #     _out_arr=("${PLANNER_PROMPTS[3]}")  
  #     ;;
  #   "travel")
  #     _out_arr=("${PLANNER_PROMPTS[7]}")  
  #     ;;
  # esac
}


is_target_combo () {
  local p="$1" e="$2"
  [[ ( "$p" == "gpt-5-mini" && "$e" == "gpt-5-mini" ) ]]
    #  ( "$p" == "gpt-5-mini" && "$e" == "gpt-5-nano" ) ||
    #  ( "$p" == "gpt-5-nano" && "$e" == "gpt-5-nano" ) ]]
}


run_one_experiment () {
  local suite="$1"
  local planner_model="$2"
  local executor_model="$3"
  local executor_prompt_file="$4"
  local planner_prompt_file="$5"
  local api_key="$6"


  OPENAI_API_KEY="$api_key" python "$PYTHON_SCRIPT" \
    --suite "$suite" \
    --structure "planner_executor" \
    --memory-type "shared_memory" \
    --planner-model "$planner_model" \
    --executor-model "$executor_model" \
    --executor-prompt-file "$executor_prompt_file" \
    --planner-prompt-file "$planner_prompt_file" \
    --log-path "$LOG_ROOT" \
    >/dev/null 2>&1 &

  # OPENAI_API_KEY="$api_key" python "$PYTHON_SCRIPT" \
  #   --suite "$suite" \
  #   --structure "handoffs" \
  #   --memory-type "shared_memory" \
  #   --planner-model "$planner_model" \
  #   --executor-model "$executor_model" \
  #   --executor-prompt-file "$executor_prompt_file" \
  #   --planner-prompt-file "$planner_prompt_file" \
  #   --log-path "$LOG_ROOT" \
  #   >/dev/null 2>&1 &
}

wait_for_slot () {
  while (( $(jobs -r | wc -l) >= CONCURRENCY )); do
    if wait -n 2>/dev/null; then
      :
    else
      sleep 1
    fi
  done
}

main () {
  mkdir -p "$LOG_ROOT/planner_executor" "$LOG_ROOT/handoffs"
  local task_index=0

  for suite in "${SUITES[@]}"; do
    local exec_prompts=()
    suite_executor_prompts "$suite" exec_prompts

    local plan_prompts=()
    suite_planner_prompts "$suite" plan_prompts

    if (( ${#exec_prompts[@]} == 0 )); then
      exec_prompts=("")
    fi

    if (( ${#plan_prompts[@]} == 0 )); then
      plan_prompts=("")
    fi



    for executor_prompt_file in "${exec_prompts[@]}"; do
      for planner_prompt_file in "${plan_prompts[@]}"; do
        for p in "${PLANNER_MODELS[@]}"; do
          for e in "${EXECUTOR_MODELS[@]}"; do
            is_target_combo "$p" "$e" || continue
            local api_key
            api_key="$(pick_key "$task_index")"
            wait_for_slot
            echo "[launch] suite=$suite  plan_model=$p  exec_model=$e  \
            exec=$(basename "$executor_prompt_file")  planner=$(basename "${planner_prompt_file:-NONE}")  \
            key_index=$(( task_index % ${#API_KEYS[@]} ))"

            run_one_experiment "$suite" "$p" "$e" \
              "$executor_prompt_file" "$planner_prompt_file" "$api_key"
            ((task_index++))
          done
        done
      done
    done
  done

  wait
  echo "All experiments finished."
}

main