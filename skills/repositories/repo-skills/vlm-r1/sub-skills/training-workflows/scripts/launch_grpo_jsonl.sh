#!/usr/bin/env bash
set -euo pipefail

show_help() {
  cat <<'EOF'
Render or launch a checked VLM-R1 GRPO JSONL training command.

Default mode is dry-run: the script prints the torchrun command and does not
start training. Add --execute when the rendered command has been reviewed.

Required:
  --workdir DIR                 open-r1-multimodal package root containing src/open_r1/grpo_jsonl.py
  --model-name-or-path VALUE    model id or checkpoint path
  --data-file-paths VALUE       colon-separated JSONL files
  --image-folders VALUE         colon-separated image roots, one per JSONL file
  --output-dir DIR              training output directory
  --run-name NAME               run name

Common options:
  --task-type VALUE                         default: rec
  --custom-vlm-reward true|false            default: true
  --reward-funcs LIST                       comma or space separated; default: accuracy,format
  --reward-method LIST                      optional colon-separated accuracy sub-methods
  --zero-stage 2|3|3-offload                resolve a standard local_scripts DeepSpeed config under --workdir
  --deepspeed FILE                          explicit DeepSpeed config path; cannot be combined with --zero-stage
  --nproc-per-node N                        default: 8
  --nnodes N                                default: 1
  --node-rank N                             default: 0
  --master-addr HOST                        default: 127.0.0.1
  --master-port PORT                        default: 12349
  --per-device-train-batch-size N           default: 8
  --gradient-accumulation-steps N           default: 2
  --gradient-checkpointing true|false       default: true
  --use-vllm true|false                     default: false
  --num-train-epochs N                      default: 2
  --max-steps N                             optional
  --logging-steps N                         default: 1
  --save-steps N                            default: 100
  --save-total-limit N                      optional
  --num-generations N                       default: 8
  --max-completion-length N                 default: 2048
  --learning-rate VALUE                     optional
  --beta VALUE                              default: 0.04
  --epsilon VALUE                           optional
  --epsilon-high VALUE                      optional
  --attn-implementation VALUE               default: flash_attention_2
  --max-pixels N                            optional Qwen image bound
  --min-pixels N                            optional Qwen image bound
  --max-anyres-num N                        optional InternVL image patch bound
  --use-peft true|false                     default: false
  --lora-r N                                default: 64 when PEFT is enabled
  --lora-alpha N                            default: 128 when PEFT is enabled
  --lora-dropout VALUE                      default: 0.05 when PEFT is enabled
  --lora-task-type VALUE                    default: CAUSAL_LM when PEFT is enabled
  --freeze-vision-modules true|false        default: false
  --report-to VALUE                         default: wandb
  --no-wandb                                set WANDB_DISABLED=true and --report_to none
  --debug true|false                        default: false
  --log-dir DIR                             debug log directory; default: OUTPUT/log
  --resume-from-checkpoint true|false       default: True
  --dataset-name VALUE                      default: not_used
  --data-seed N                             default: 42
  --skip-path-checks                        skip filesystem existence checks
  --dry-run                                 print command only (default)
  --execute                                 run command after validation
  --                                        pass remaining arguments through to grpo_jsonl.py

Example dry-run for LoRA plus frozen vision and no W&B:
  launch_grpo_jsonl.sh \
    --workdir <open-r1-multimodal-package-root> \
    --model-name-or-path Qwen/Qwen2.5-VL-3B-Instruct \
    --data-file-paths data/a.jsonl:data/b.jsonl \
    --image-folders images/a:images/b \
    --output-dir outputs/rl/lora-freeze \
    --run-name lora-freeze \
    --custom-vlm-reward true \
    --zero-stage 2 \
    --use-peft true \
    --freeze-vision-modules true \
    --no-wandb \
    --skip-path-checks
EOF
}

die() { echo "error: $*" >&2; exit 2; }

lower() { printf '%s' "$1" | tr '[:upper:]' '[:lower:]'; }

normalize_bool() {
  case "$(lower "$1")" in
    true|1|yes|y) printf 'true' ;;
    false|0|no|n) printf 'false' ;;
    *) die "expected boolean true/false, got '$1'" ;;
  esac
}

count_colon_items() {
  local value="$1"
  if [[ -z "$value" ]]; then
    printf '1'
    return
  fi
  local only_colons="${value//[^:]/}"
  printf '%s' "$(( ${#only_colons} + 1 ))"
}

reject_empty_colon_items() {
  local name="$1"
  local value="$2"
  [[ -z "$value" ]] && return 0
  if [[ "$value" == :* || "$value" == *: || "$value" == *::* ]]; then
    die "$name contains an empty item: '$value'"
  fi
}

path_exists_anywhere() {
  local candidate="$1"
  local workdir="$2"
  [[ -z "$candidate" ]] && return 0
  if [[ "$candidate" = /* ]]; then
    [[ -e "$candidate" ]]
  else
    [[ -e "$candidate" || -e "$workdir/$candidate" ]]
  fi
}

split_colon_and_check_paths() {
  local name="$1"
  local value="$2"
  local workdir="$3"
  [[ -z "$value" ]] && return 0
  local old_ifs="$IFS"
  IFS=':' read -r -a items <<< "$value"
  IFS="$old_ifs"
  local item
  for item in "${items[@]}"; do
    if ! path_exists_anywhere "$item" "$workdir"; then
      die "$name item does not exist: $item (use --skip-path-checks for command previews)"
    fi
  done
}

print_command() {
  printf '%q ' "$@"
  printf '\n'
}

WORKDIR=""
SCRIPT="src/open_r1/grpo_jsonl.py"
MODEL_NAME_OR_PATH=""
DATA_FILE_PATHS=""
IMAGE_FOLDERS=""
OUTPUT_DIR=""
RUN_NAME=""
TASK_TYPE="rec"
CUSTOM_VLM_REWARD="true"
REWARD_FUNCS="accuracy,format"
REWARD_METHOD=""
ZERO_STAGE=""
DEEPSPEED=""
NPROC_PER_NODE=8
NNODES=1
NODE_RANK=0
MASTER_ADDR="127.0.0.1"
MASTER_PORT=12349
PER_DEVICE_TRAIN_BATCH_SIZE=8
GRADIENT_ACCUMULATION_STEPS=2
GRADIENT_CHECKPOINTING="true"
USE_VLLM="false"
NUM_TRAIN_EPOCHS=2
MAX_STEPS=""
LOGGING_STEPS=1
SAVE_STEPS=100
SAVE_TOTAL_LIMIT=""
NUM_GENERATIONS=8
MAX_COMPLETION_LENGTH=2048
LEARNING_RATE=""
BETA="0.04"
EPSILON=""
EPSILON_HIGH=""
ATTN_IMPLEMENTATION="flash_attention_2"
MAX_PIXELS=""
MIN_PIXELS=""
MAX_ANYRES_NUM=""
USE_PEFT="false"
LORA_R=64
LORA_ALPHA=128
LORA_DROPOUT="0.05"
LORA_TASK_TYPE="CAUSAL_LM"
FREEZE_VISION_MODULES="false"
REPORT_TO="wandb"
NO_WANDB="false"
DEBUG_MODE_VALUE="false"
LOG_DIR=""
RESUME_FROM_CHECKPOINT="True"
DATASET_NAME="not_used"
DATA_SEED=42
SKIP_PATH_CHECKS="false"
DRY_RUN="true"
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) show_help; exit 0 ;;
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --script) SCRIPT="${2:-}"; shift 2 ;;
    --model-name-or-path|--model) MODEL_NAME_OR_PATH="${2:-}"; shift 2 ;;
    --data-file-paths) DATA_FILE_PATHS="${2:-}"; shift 2 ;;
    --image-folders) IMAGE_FOLDERS="${2:-}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:-}"; shift 2 ;;
    --run-name) RUN_NAME="${2:-}"; shift 2 ;;
    --task-type) TASK_TYPE="${2:-}"; shift 2 ;;
    --custom-vlm-reward|--is-reward-customized-from-vlm-module) CUSTOM_VLM_REWARD="$(normalize_bool "${2:-}")"; shift 2 ;;
    --reward-funcs) REWARD_FUNCS="${2:-}"; shift 2 ;;
    --reward-method) REWARD_METHOD="${2:-}"; shift 2 ;;
    --zero-stage) ZERO_STAGE="${2:-}"; shift 2 ;;
    --deepspeed) DEEPSPEED="${2:-}"; shift 2 ;;
    --nproc-per-node) NPROC_PER_NODE="${2:-}"; shift 2 ;;
    --nnodes) NNODES="${2:-}"; shift 2 ;;
    --node-rank) NODE_RANK="${2:-}"; shift 2 ;;
    --master-addr) MASTER_ADDR="${2:-}"; shift 2 ;;
    --master-port) MASTER_PORT="${2:-}"; shift 2 ;;
    --per-device-train-batch-size) PER_DEVICE_TRAIN_BATCH_SIZE="${2:-}"; shift 2 ;;
    --gradient-accumulation-steps) GRADIENT_ACCUMULATION_STEPS="${2:-}"; shift 2 ;;
    --gradient-checkpointing) GRADIENT_CHECKPOINTING="$(normalize_bool "${2:-}")"; shift 2 ;;
    --use-vllm) USE_VLLM="$(normalize_bool "${2:-}")"; shift 2 ;;
    --num-train-epochs) NUM_TRAIN_EPOCHS="${2:-}"; shift 2 ;;
    --max-steps) MAX_STEPS="${2:-}"; shift 2 ;;
    --logging-steps) LOGGING_STEPS="${2:-}"; shift 2 ;;
    --save-steps) SAVE_STEPS="${2:-}"; shift 2 ;;
    --save-total-limit) SAVE_TOTAL_LIMIT="${2:-}"; shift 2 ;;
    --num-generations) NUM_GENERATIONS="${2:-}"; shift 2 ;;
    --max-completion-length) MAX_COMPLETION_LENGTH="${2:-}"; shift 2 ;;
    --learning-rate) LEARNING_RATE="${2:-}"; shift 2 ;;
    --beta) BETA="${2:-}"; shift 2 ;;
    --epsilon) EPSILON="${2:-}"; shift 2 ;;
    --epsilon-high) EPSILON_HIGH="${2:-}"; shift 2 ;;
    --attn-implementation) ATTN_IMPLEMENTATION="${2:-}"; shift 2 ;;
    --max-pixels) MAX_PIXELS="${2:-}"; shift 2 ;;
    --min-pixels) MIN_PIXELS="${2:-}"; shift 2 ;;
    --max-anyres-num) MAX_ANYRES_NUM="${2:-}"; shift 2 ;;
    --use-peft) USE_PEFT="$(normalize_bool "${2:-}")"; shift 2 ;;
    --lora-r) LORA_R="${2:-}"; shift 2 ;;
    --lora-alpha) LORA_ALPHA="${2:-}"; shift 2 ;;
    --lora-dropout) LORA_DROPOUT="${2:-}"; shift 2 ;;
    --lora-task-type) LORA_TASK_TYPE="${2:-}"; shift 2 ;;
    --freeze-vision-modules) FREEZE_VISION_MODULES="$(normalize_bool "${2:-}")"; shift 2 ;;
    --report-to) REPORT_TO="${2:-}"; shift 2 ;;
    --no-wandb) NO_WANDB="true"; REPORT_TO="none"; shift ;;
    --debug) DEBUG_MODE_VALUE="$(normalize_bool "${2:-}")"; shift 2 ;;
    --log-dir) LOG_DIR="${2:-}"; shift 2 ;;
    --resume-from-checkpoint) RESUME_FROM_CHECKPOINT="${2:-}"; shift 2 ;;
    --dataset-name) DATASET_NAME="${2:-}"; shift 2 ;;
    --data-seed) DATA_SEED="${2:-}"; shift 2 ;;
    --skip-path-checks) SKIP_PATH_CHECKS="true"; shift ;;
    --dry-run|--print-only) DRY_RUN="true"; shift ;;
    --execute) DRY_RUN="false"; shift ;;
    --) shift; EXTRA_ARGS+=("$@"); break ;;
    *) die "unknown option: $1" ;;
  esac
done

[[ -n "$WORKDIR" ]] || die "--workdir is required"
[[ -n "$MODEL_NAME_OR_PATH" ]] || die "--model-name-or-path is required"
[[ -n "$DATA_FILE_PATHS" ]] || die "--data-file-paths is required"
[[ -n "$OUTPUT_DIR" ]] || die "--output-dir is required"
[[ -n "$RUN_NAME" ]] || die "--run-name is required"
[[ -n "$SCRIPT" ]] || die "--script cannot be empty"

for numeric in NPROC_PER_NODE NNODES NODE_RANK MASTER_PORT PER_DEVICE_TRAIN_BATCH_SIZE GRADIENT_ACCUMULATION_STEPS LOGGING_STEPS SAVE_STEPS NUM_GENERATIONS; do
  value="${!numeric}"
  [[ "$value" =~ ^[0-9]+$ ]] || die "$numeric must be a non-negative integer, got '$value'"
done
(( NPROC_PER_NODE > 0 )) || die "--nproc-per-node must be greater than zero"
(( NNODES > 0 )) || die "--nnodes must be greater than zero"
(( NODE_RANK >= 0 && NODE_RANK < NNODES )) || die "--node-rank must be between 0 and nnodes-1"
(( MASTER_PORT > 0 && MASTER_PORT < 65536 )) || die "--master-port must be between 1 and 65535"
(( PER_DEVICE_TRAIN_BATCH_SIZE > 0 )) || die "--per-device-train-batch-size must be greater than zero"
(( NUM_GENERATIONS >= 2 )) || die "--num-generations must be at least 2"

reject_empty_colon_items "data_file_paths" "$DATA_FILE_PATHS"
reject_empty_colon_items "image_folders" "$IMAGE_FOLDERS"
reject_empty_colon_items "reward_method" "$REWARD_METHOD"

data_count="$(count_colon_items "$DATA_FILE_PATHS")"
image_count="$(count_colon_items "$IMAGE_FOLDERS")"
[[ "$data_count" == "$image_count" ]] || die "data_file_paths count ($data_count) must match image_folders count ($image_count)"
if [[ -n "$REWARD_METHOD" ]]; then
  reward_method_count="$(count_colon_items "$REWARD_METHOD")"
  [[ "$reward_method_count" == "$data_count" ]] || die "reward_method count ($reward_method_count) must match data_file_paths count ($data_count)"
fi

global_batch=$(( NPROC_PER_NODE * NNODES * PER_DEVICE_TRAIN_BATCH_SIZE ))
if (( global_batch % NUM_GENERATIONS != 0 )); then
  die "global batch ($NPROC_PER_NODE * $NNODES * $PER_DEVICE_TRAIN_BATCH_SIZE = $global_batch) must be divisible by num_generations ($NUM_GENERATIONS)"
fi

if [[ -n "$ZERO_STAGE" && -n "$DEEPSPEED" ]]; then
  die "use either --zero-stage or --deepspeed, not both"
fi
if [[ -n "$ZERO_STAGE" ]]; then
  case "$ZERO_STAGE" in
    2) DEEPSPEED="local_scripts/zero2.json" ;;
    3) DEEPSPEED="local_scripts/zero3.json" ;;
    3-offload|zero3-offload) DEEPSPEED="local_scripts/zero3_offload.json" ;;
    *) die "--zero-stage must be 2, 3, or 3-offload" ;;
  esac
fi

if [[ "$SKIP_PATH_CHECKS" != "true" ]]; then
  [[ -d "$WORKDIR" ]] || die "workdir does not exist: $WORKDIR"
  path_exists_anywhere "$SCRIPT" "$WORKDIR" || die "training script does not exist under workdir: $SCRIPT"
  split_colon_and_check_paths "data_file_paths" "$DATA_FILE_PATHS" "$WORKDIR"
  split_colon_and_check_paths "image_folders" "$IMAGE_FOLDERS" "$WORKDIR"
  if [[ -n "$DEEPSPEED" ]]; then
    path_exists_anywhere "$DEEPSPEED" "$WORKDIR" || die "DeepSpeed config does not exist: $DEEPSPEED"
  fi
fi

if [[ -z "$LOG_DIR" ]]; then
  LOG_DIR="$OUTPUT_DIR/log"
fi

reward_funcs_expanded="${REWARD_FUNCS//,/ }"
read -r -a reward_func_items <<< "$reward_funcs_expanded"
(( ${#reward_func_items[@]} > 0 )) || die "--reward-funcs must contain at least one reward function"

cmd=(
  torchrun
  --nproc_per_node="$NPROC_PER_NODE"
  --nnodes="$NNODES"
  --node_rank="$NODE_RANK"
  --master_addr="$MASTER_ADDR"
  --master_port="$MASTER_PORT"
  "$SCRIPT"
  --use_vllm "$USE_VLLM"
  --output_dir "$OUTPUT_DIR"
  --resume_from_checkpoint "$RESUME_FROM_CHECKPOINT"
  --model_name_or_path "$MODEL_NAME_OR_PATH"
  --data_file_paths "$DATA_FILE_PATHS"
  --image_folders "$IMAGE_FOLDERS"
  --is_reward_customized_from_vlm_module "$CUSTOM_VLM_REWARD"
)

if [[ -n "$REWARD_METHOD" ]]; then
  cmd+=(--reward_method "$REWARD_METHOD")
fi

cmd+=(
  --task_type "$TASK_TYPE"
  --per_device_train_batch_size "$PER_DEVICE_TRAIN_BATCH_SIZE"
  --gradient_accumulation_steps "$GRADIENT_ACCUMULATION_STEPS"
  --gradient_checkpointing "$GRADIENT_CHECKPOINTING"
  --logging_steps "$LOGGING_STEPS"
  --num_train_epochs "$NUM_TRAIN_EPOCHS"
)

if [[ -n "$MAX_STEPS" ]]; then
  cmd+=(--max_steps "$MAX_STEPS")
fi

cmd+=(
  --bf16
  --attn_implementation "$ATTN_IMPLEMENTATION"
  --run_name "$RUN_NAME"
  --data_seed "$DATA_SEED"
  --save_steps "$SAVE_STEPS"
)

if [[ -n "$SAVE_TOTAL_LIMIT" ]]; then
  cmd+=(--save_total_limit "$SAVE_TOTAL_LIMIT")
fi

cmd+=(
  --num_generations "$NUM_GENERATIONS"
  --max_completion_length "$MAX_COMPLETION_LENGTH"
  --reward_funcs "${reward_func_items[@]}"
  --beta "$BETA"
)

if [[ -n "$LEARNING_RATE" ]]; then
  cmd+=(--learning_rate "$LEARNING_RATE")
fi
if [[ -n "$EPSILON" ]]; then
  cmd+=(--epsilon "$EPSILON")
fi
if [[ -n "$EPSILON_HIGH" ]]; then
  cmd+=(--epsilon_high "$EPSILON_HIGH")
fi
if [[ -n "$MAX_PIXELS" ]]; then
  cmd+=(--max_pixels "$MAX_PIXELS")
fi
if [[ -n "$MIN_PIXELS" ]]; then
  cmd+=(--min_pixels "$MIN_PIXELS")
fi
if [[ -n "$MAX_ANYRES_NUM" ]]; then
  cmd+=(--max_anyres_num "$MAX_ANYRES_NUM")
fi

cmd+=(--report_to "$REPORT_TO" --dataset-name "$DATASET_NAME")

if [[ -n "$DEEPSPEED" ]]; then
  cmd+=(--deepspeed "$DEEPSPEED")
fi

if [[ "$USE_PEFT" == "true" ]]; then
  cmd+=(
    --use_peft true
    --lora_r "$LORA_R"
    --lora_alpha "$LORA_ALPHA"
    --lora_dropout "$LORA_DROPOUT"
    --lora_task_type "$LORA_TASK_TYPE"
  )
fi

if [[ "$FREEZE_VISION_MODULES" == "true" ]]; then
  cmd+=(--freeze_vision_modules true)
fi

cmd+=("${EXTRA_ARGS[@]}")

if [[ "$DRY_RUN" == "true" ]]; then
  echo "# dry-run: command not executed"
  printf 'cd '; printf '%q' "$WORKDIR"; printf ' && '
  env_prefix=()
  if [[ "$DEBUG_MODE_VALUE" == "true" ]]; then
    env_prefix+=("DEBUG_MODE=true" "LOG_PATH=$LOG_DIR/${RUN_NAME}.debug.TIMESTAMP.txt")
  else
    env_prefix+=("DEBUG_MODE=false")
  fi
  if [[ "$NO_WANDB" == "true" ]]; then
    env_prefix+=("WANDB_DISABLED=true")
  fi
  if (( ${#env_prefix[@]} > 0 )); then
    printf '%q ' "${env_prefix[@]}"
  fi
  print_command "${cmd[@]}"
  echo "# global_batch=$global_batch; num_generations=$NUM_GENERATIONS"
  exit 0
fi

[[ -x "$(command -v torchrun)" ]] || die "torchrun is not on PATH"
if [[ "$DEBUG_MODE_VALUE" == "true" ]]; then
  mkdir -p "$LOG_DIR"
  export DEBUG_MODE=true
  export LOG_PATH="$LOG_DIR/${RUN_NAME}.debug.$(date +%Y%m%d-%H%M%S).txt"
else
  export DEBUG_MODE=false
fi
if [[ "$NO_WANDB" == "true" ]]; then
  export WANDB_DISABLED=true
fi

cd "$WORKDIR"
echo "Launching VLM-R1 GRPO training: $RUN_NAME"
echo "global_batch=$global_batch num_generations=$NUM_GENERATIONS"
exec "${cmd[@]}"
