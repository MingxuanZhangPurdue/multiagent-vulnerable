#!/usr/bin/env bash
# run_parallel.sh
# Pallelly run attack_hooks.py， support multiple API Keys, and can choose different prompts according to different suites

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/attack_hooks.py"

CONCURRENCY=1

# Focus on Slack privacy testing
declare -a SUITES=("workspace")

declare -a PLANNER_MODELS=("gemini-2.5-flash")
declare -a EXECUTOR_MODELS=("gemini-2.5-flash")

declare -a API_KEYS=()

# Load API keys from environment variables (comma-separated). Example:
#   export GEMINI_API_KEYS="key1,key2"  # for Gemini models
#   export OPENAI_API_KEYS="key1,key2"  # for OpenAI models
IFS=',' read -r -a _GEMINI_KEYS <<< "${GEMINI_API_KEYS:-}"
IFS=',' read -r -a _OPENAI_KEYS <<< "${OPENAI_API_KEYS:-}"
for k in "${_GEMINI_KEYS[@]}"; do [[ -n "$k" ]] && API_KEYS+=("$k"); done
for k in "${_OPENAI_KEYS[@]}"; do [[ -n "$k" ]] && API_KEYS+=("$k"); done

declare -a attack_type=("prompt")

declare -a task_type=("privacy")

# Available prompt templates for harmful tasks
declare -a harmful_prompt_templates=(
    "direct_command"
    "priority_escalation"
    "stealth_injection"
)

# Enhanced privacy attack templates for better success with user tasks
# These templates are designed to work better with user tasks by creating
# more natural and contextually appropriate prompts that reduce model security awareness
declare -a privacy_prompt_templates=(
    "privacy_audit_preparation"
    "privacy_emergency_planning"
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


is_target_combo () {
  local p="$1" e="$2"
  [[ 
    ( "$p" == "gemini-2.5-flash" && "$e" == "gemini-2.5-flash" ) ||
    ( "$p" == "gpt-5-mini" && "$e" == "gpt-5-mini" ) ||
    ( "$p" == "gpt-5" && "$e" == "gpt-5-nano" ) ||
    ( "$p" == "gpt-5-mini" && "$e" == "gpt-5-nano" ) ]]
}

select_method () {
  local attack_type="$1"
  case "$attack_type" in
    "instruction")
      echo "inject"
      ;;
    "memory")
      echo "pop"
      ;;
    *)
      echo "back"
      ;;
  esac
}


run_one_experiment () {
  local suite="$1"
  local planner_model="$2"
  local executor_model="$3"
  local attack_type="$4"
  local task_type="$5"
  local prompt_template="$6"
  local api_key="$7"

  local ts
  ts="$(date +%Y%m%d-%H%M%S)"
  local results_dir="${attack_type}_${task_type}_${prompt_template}_${planner_model}_${executor_model}_${suite}_${ts}_planner_executor_on_planner_start"
  mkdir -p "$results_dir"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting: $attack_type $task_type $prompt_template $planner_model->$executor_model"

  local method
  method="$(select_method "$attack_type")"

  # Set appropriate API key based on model type
  if [[ "$planner_model" == gemini* ]]; then
    GEMINI_API_KEY="$api_key" OPENAI_API_KEY="" python "$PYTHON_SCRIPT" \
      --suite "$suite" \
      --mas_type "planner_executor" \
      --planner_model "$planner_model" \
      --executor_model "$executor_model" \
      --attack_type "$attack_type" \
      --task_type "$task_type" \
      --step "on_planner_start" \
      --method "$method" \
      --prompt_template "$prompt_template" \
      --results_dir "$results_dir" \
      > "${results_dir}/output.log" 2>&1 &
  else
    OPENAI_API_KEY="$api_key" GEMINI_API_KEY="" python "$PYTHON_SCRIPT" \
      --suite "$suite" \
      --mas_type "planner_executor" \
      --planner_model "$planner_model" \
      --executor_model "$executor_model" \
      --attack_type "$attack_type" \
      --task_type "$task_type" \
      --step "on_planner_start" \
      --method "$method" \
      --prompt_template "$prompt_template" \
      --results_dir "$results_dir" \
      > "${results_dir}/output.log" 2>&1 &
  fi
}

wait_for_slot () {
  while (( $(jobs -rp | wc -l) >= CONCURRENCY )); do
    if wait -n 2>/dev/null; then
      :
    else
      sleep 1
    fi
  done
}

show_progress () {
  local running launched completed
  running=$(jobs -rp | wc -l)
  launched=$CURRENT_TASK_INDEX
  completed=$(( launched - running ))
  echo "[$(date '+%H:%M:%S')] Progress: $completed/$TOTAL_TASKS completed, $running running"
}

main () {
  local task_index=0
  local total_tasks=0
  
  # Make variables global for show_progress function
  CURRENT_TASK_INDEX=0
  TOTAL_TASKS=0

  # Calculate total number of tasks
  for suite in "${SUITES[@]}"; do
    for attack in "${attack_type[@]}"; do
      for task in "${task_type[@]}"; do
        # Select appropriate prompt templates based on task type
        if [[ "$task" == "harmful" ]]; then
          prompt_templates=("${harmful_prompt_templates[@]}")
        elif [[ "$task" == "privacy" ]]; then
          prompt_templates=("${privacy_prompt_templates[@]}")
        fi
        
        for prompt in "${prompt_templates[@]}"; do
          for p in "${PLANNER_MODELS[@]}"; do
            for e in "${EXECUTOR_MODELS[@]}"; do
              is_target_combo "$p" "$e" && ((total_tasks++))
            done
          done
        done
      done
    done
  done
  
  # Set global variables
  TOTAL_TASKS=$total_tasks

  echo "=========================================="
  echo "🚀 Starting parallel attack experiments"
  echo "=========================================="
  echo "📊 Total combinations: $total_tasks"
  echo "⚙️  Concurrency: $CONCURRENCY"
  echo "🔑 API Keys available: ${#API_KEYS[@]}"
  echo "📁 Results will be saved in: attack_results_* directories"
  echo "=========================================="

  for suite in "${SUITES[@]}"; do
    for attack in "${attack_type[@]}"; do
      for task in "${task_type[@]}"; do
        # Select appropriate prompt templates based on task type
        if [[ "$task" == "harmful" ]]; then
          prompt_templates=("${harmful_prompt_templates[@]}")
        elif [[ "$task" == "privacy" ]]; then
          prompt_templates=("${privacy_prompt_templates[@]}")
        fi
        
        for prompt in "${prompt_templates[@]}"; do
          for p in "${PLANNER_MODELS[@]}"; do
            for e in "${EXECUTOR_MODELS[@]}"; do
              is_target_combo "$p" "$e" || continue
              
              local api_key
              api_key="$(pick_key "$task_index")"
              
              wait_for_slot
              
              echo "[$((task_index + 1))/$total_tasks] Launching: $attack $task $prompt $p->$e (key: $(( task_index % ${#API_KEYS[@]} )))"
              
              run_one_experiment "$suite" "$p" "$e" "$attack" "$task" "$prompt" "$api_key"
              ((task_index++))
              CURRENT_TASK_INDEX=$task_index
              
              # Show progress every 5 tasks
              if (( task_index % 5 == 0 )); then
                show_progress
              fi
            done
          done
        done
      done
    done
  done

  echo "=========================================="
  echo "⏳ All tasks launched. Waiting for completion..."
  echo "=========================================="
  
  # Wait for all background jobs to complete
  wait
  
  echo "=========================================="
  echo "🎉 All experiments finished!"
  echo "=========================================="
  
  # Show summary of results
  echo "📁 Results directories created:"
  ls -la attack_results_* 2>/dev/null | head -10
  if (( $(ls -1 attack_results_* 2>/dev/null | wc -l) > 10 )); then
    echo "... and $(( $(ls -1 attack_results_* 2>/dev/null | wc -l) - 10 )) more"
  fi
}

main