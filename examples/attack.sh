#!/usr/bin/env bash
# run_parallel.sh
# Pallelly run attack_hooks.py， support multiple API Keys, and can choose different prompts according to different suites

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/attack_hooks.py"

CONCURRENCY=4

# Per-suite/user task/attack task limits
MAX_USER_TASKS=1
MAX_ATTACK_TASKS=10

# Focus on Slack privacy testing
declare -a SUITES=("banking" "slack" "workspace" "travel")

declare -a PLANNER_MODELS=("gemini-2.5-flash")
declare -a EXECUTOR_MODELS=("gemini-2.5-flash")

# Load API keys from environment variables (comma-separated). Example:
#   export GEMINI_API_KEYS="key1,key2"  # for Gemini models
#   export OPENAI_API_KEYS="key1,key2"  # for OpenAI models
declare -a API_KEYS=(
  "API_KEY_1"
)

declare -a attack_type=("prompt")

declare -a task_type=("privacy")

# Available attack steps
declare -a attack_steps=("on_executor_start" "on_executor_end")

# Available prompt templates for harmful tasks
declare -a harmful_prompt_templates=(
    # "user_request_update" (GPT)
    # "authority_override" (Gemini)
    "authority_override"
)

# Enhanced privacy attack templates for better success with user tasks
# These templates are designed to work better with user tasks by creating
# more natural and contextually appropriate prompts that reduce model security awareness
declare -a privacy_prompt_templates=(
    # "data_governance" (GPT)
    # "privacy_compliance_audit" (Gemini)
    "privacy_compliance_audit"
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
  [[ \
    ( "$p" == "gpt-5-mini" && "$e" == "gpt-5-nano" ) || \
    ( "$p" == "gemini-2.5-flash" && "$e" == "gemini-2.5-flash" ) \
  ]]
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
      echo "front"
      ;;
  esac
}

local method
  method="$(select_method "$attack_type")"

run_one_experiment () {
  local suite="$1"
  local planner_model="$2"
  local executor_model="$3"
  local attack_type="$4"
  local task_type="$5"
  local prompt_template="$6"
  local step="$7"
  local api_key="$8"

  local ts
  ts="$(date +%Y%m%d-%H%M%S)"
  local results_dir="prompt/${attack_type}_${task_type}_${method}/${step}/${prompt_template}/${suite}/${planner_model}_${executor_model}__${ts}_planner_executor"
  mkdir -p "$results_dir"

  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting: $attack_type $task_type $prompt_template $step $planner_model->$executor_model"


  # Set appropriate API key based on model type
  if [[ "$planner_model" == gemini* ]]; then
    GEMINI_API_KEY="$api_key" OPENAI_API_KEY="" python "$PYTHON_SCRIPT" \
      --suite "$suite" \
      --mas_type "planner_executor" \
      --planner_model "$planner_model" \
      --executor_model "$executor_model" \
      --attack_type "$attack_type" \
      --task_type "$task_type" \
      --step "$step" \
      --method "$method" \
      --prompt_template "$prompt_template" \
      --max_user_tasks "$MAX_USER_TASKS" \
      --max_tasks "$MAX_ATTACK_TASKS" \
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
      --step "$step" \
      --method "$method" \
      --prompt_template "$prompt_template" \
      --max_user_tasks "$MAX_USER_TASKS" \
      --max_tasks "$MAX_ATTACK_TASKS" \
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
  # Validate API keys availability early
  if (( ${#API_KEYS[@]} == 0 )); then
    echo "[Error] No API keys provided. Set GEMINI_API_KEYS/OPENAI_API_KEYS or hardcode API_KEYS in this script."
    exit 1
  fi

  for suite in "${SUITES[@]}"; do
    for attack in "${attack_type[@]}"; do
      for task in "${task_type[@]}"; do
        for step in "${attack_steps[@]}"; do
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
        for step in "${attack_steps[@]}"; do
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
                
                echo "[$((task_index + 1))/$total_tasks] Launching: $attack $task $prompt $step $p->$e (key: $(( task_index % ${#API_KEYS[@]} )))"
                
                run_one_experiment "$suite" "$p" "$e" "$attack" "$task" "$prompt" "$step" "$api_key"
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