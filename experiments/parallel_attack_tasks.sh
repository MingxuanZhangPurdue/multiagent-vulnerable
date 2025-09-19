#!/usr/bin/env bash
# Parallel runner for experiments/run_attack_tasks.py (modeled after multi/experiments/parallel.sh)
set -u
set -o pipefail
set -m  # enable job control so jobs/wait -n behave predictably

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/run_attack_tasks.py"

# Global concurrency (number of jobs total)
CONCURRENCY=12

# Target dimensions (edit as needed)
declare -a SUITES=("banking")
declare -a STRUCTURES=("planner_executor")
declare -a MEMORY_TYPES=("default_memory")
declare -a ATTACK_TYPES=("privacy")

# Define specific model combinations
declare -a MODEL_COMBINATIONS=(
    "gpt-5 gpt-5-nano"
    "gpt-5 gpt-5-mini"
    "gpt-5-mini gpt-5-nano"
)

# Results root
LOG_ROOT_BASE="${LOG_ROOT_BASE:-$SCRIPT_DIR/results_attacks/privacy/gpt}"
TS=$(date +%Y%m%d_%H%M%S)
LOG_ROOT="$LOG_ROOT_BASE/$TS"
mkdir -p "$LOG_ROOT"

# API keys pool (round-robin per job index)
declare -a API_KEYS=(
  "API_KEY_1"
)

pick_key () {
  local idx="$1"; local n="${#API_KEYS[@]}"; local sel=$(( idx % n )); echo "${API_KEYS[$sel]}"
}

wait_for_slot () {
  while (( $(jobs -r | wc -l) >= CONCURRENCY )); do
    if wait -n 2>/dev/null; then :; else sleep 1; fi
  done
}

echo "Results root: $LOG_ROOT"

task_index=0
for suite in "${SUITES[@]}"; do
  for structure in "${STRUCTURES[@]}"; do
    for mem in "${MEMORY_TYPES[@]}"; do
      for attack in "${ATTACK_TYPES[@]}"; do
        for combination in "${MODEL_COMBINATIONS[@]}"; do
          read -r planner executor <<< "$combination"
          wait_for_slot
          api_key="$(pick_key "$task_index")"
          echo "[job $task_index] suite=$suite structure=$structure mem=$mem attack=$attack planner=$planner executor=$executor key_idx=$(( task_index % ${#API_KEYS[@]} ))"
          OPENAI_API_KEY="$api_key" python "$PYTHON_SCRIPT" \
            --suite "$suite" \
            --structure "$structure" \
            --memory-type "$mem" \
            --planner-model "$planner" \
            --executor-model "$executor" \
            --attack-type "$attack" \
            --log-path "$LOG_ROOT" \
            >/dev/null 2>&1 &
          ((task_index++))
          sleep $((RANDOM%2+1))
        done
      done
    done
  done
done

wait
echo "All runs completed. See: $LOG_ROOT"


