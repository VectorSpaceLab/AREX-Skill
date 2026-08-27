#!/usr/bin/env bash
# Self-contained Align-Anything training launcher template.
# Configure with environment variables and append any extra trainer CLI overrides after "--".
# It intentionally does not source repository scripts or preserve checkout-specific paths.

set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  LAUNCHER=deepspeed TRAINER_MODULE=align_anything.trainers.text_to_text.sft \
  MODEL_NAME_OR_PATH=<model> TRAIN_DATASETS=<dataset> TRAIN_TEMPLATE=<template> OUTPUT_DIR=<out> \
  bash launch_training_template.sh [--dry-run] [--] [extra trainer args...]

Launchers:
  LAUNCHER=deepspeed  DeepSpeed module launch, recommended for most non-diffusion trainers.
  LAUNCHER=torchrun   torchrun module launch, useful for distributed smoke tests and diffusion trainers.
  LAUNCHER=accelerate Accelerate module launch, useful for diffusion trainers.
  LAUNCHER=python     Single-process module launch; only use for trainers known to initialize safely.
  LAUNCHER=slurm      Write an sbatch wrapper around the selected command. Submit only with SLURM_SUBMIT=1.

Core variables:
  TRAINER_MODULE        Required Python module, e.g. align_anything.trainers.text_to_text.dpo
  OUTPUT_DIR            Required output directory
  AA_REPO_ROOT          Optional checkout root to prepend to PYTHONPATH
  PYTHON                Optional Python executable for probes and LAUNCHER=python. Default: python
  NUM_GPUS              Default: visible CUDA device count, else 1
  MASTER_PORT           Default: auto-selected local free port
  ZERO_STAGE_FILE       Optional DeepSpeed config file name available to the package
  WANDB_API_KEY         If empty, WANDB_MODE defaults to offline

Common model variables mapped to CLI args when non-empty:
  MODEL_NAME_OR_PATH PROCESSOR_NAME_OR_PATH ACTOR_MODEL_NAME_OR_PATH
  REWARD_MODEL_NAME_OR_PATH REWARD_CRITIC_MODEL_NAME_OR_PATH
  COST_MODEL_NAME_OR_PATH COST_CRITIC_MODEL_NAME_OR_PATH REMOTE_RM_URL

Common data variables mapped to CLI args when non-empty:
  TRAIN_DATASETS TRAIN_TEMPLATE TRAIN_SPLIT TRAIN_NAME TRAIN_DATA_FILES TRAIN_SIZE TRAIN_OPTIONAL_ARGS
  EVAL_DATASETS EVAL_TEMPLATE EVAL_SPLIT EVAL_NAME EVAL_DATA_FILES EVAL_SIZE EVAL_OPTIONAL_ARGS
  PTX_DATASETS PTX_TEMPLATE PTX_SPLIT PTX_NAME PTX_DATA_FILES PTX_SIZE PTX_OPTIONAL_ARGS

Common hyperparameter variables mapped to CLI args when non-empty:
  EPOCHS LEARNING_RATE ACTOR_LR CRITIC_LR PER_DEVICE_TRAIN_BATCH_SIZE
  PER_DEVICE_PROMPT_BATCH_SIZE PER_DEVICE_EVAL_BATCH_SIZE GRADIENT_ACCUMULATION_STEPS
  MODEL_MAX_LENGTH MAX_NEW_TOKENS BF16 FP16 USE_LORA USE_BNB LOAD_IN_4BIT LOAD_IN_8BIT
  SAVE_TOTAL_LIMIT SAVE_INTERVAL EVAL_INTERVAL EVAL_STRATEGY
  FREEZE_MM_PROJ FREEZE_VISION_TOWER FREEZE_LANGUAGE_MODEL FREEZE_UNET LORA_UNET
  BETA BETA_COEFF KL_COEFF CLIP_RANGE_RATIO NUM_GENERATIONS RESOLUTION

VLA/action variables mapped when non-empty:
  DATA_DIR DATASET_TASK_TYPE INPUT_SENSORS MODEL_ARCHITECTURE MODEL_VERSION

Examples:
  # Dry-run text DPO.
  LAUNCHER=deepspeed TRAINER_MODULE=align_anything.trainers.text_to_text.dpo \
  MODEL_NAME_OR_PATH=meta-llama/Llama-3.1-8B-Instruct \
  TRAIN_DATASETS=PKU-Alignment/PKU-SafeRLHF-single-dimension TRAIN_TEMPLATE=PKUSafeRLHF \
  TRAIN_SPLIT=train OUTPUT_DIR=outputs/text_dpo bash launch_training_template.sh --dry-run

  # Diffusion SFT with torchrun.
  LAUNCHER=torchrun NUM_GPUS=1 TRAINER_MODULE=align_anything.trainers.text_to_image.sft_diffusion \
  MODEL_NAME_OR_PATH=runwayml/stable-diffusion-v1-5 TRAIN_DATASETS=<dataset> \
  TRAIN_TEMPLATE=DiffusionDB TRAIN_SPLIT=train OUTPUT_DIR=outputs/t2i_sft \
  bash launch_training_template.sh --dry-run -- --resolution 512
USAGE
}

DRY_RUN=0
EXTRA_TRAINER_ARGS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      EXTRA_TRAINER_ARGS+=("$@")
      break
      ;;
    *)
      EXTRA_TRAINER_ARGS+=("$1")
      shift
      ;;
  esac
done

LAUNCHER="${LAUNCHER:-deepspeed}"
TRAINER_MODULE="${TRAINER_MODULE:-}"
OUTPUT_DIR="${OUTPUT_DIR:-}"
if [[ -z "$TRAINER_MODULE" ]]; then
  echo "ERROR: TRAINER_MODULE is required." >&2
  usage >&2
  exit 2
fi
if [[ -z "$OUTPUT_DIR" ]]; then
  echo "ERROR: OUTPUT_DIR is required." >&2
  usage >&2
  exit 2
fi

if [[ -n "${AA_REPO_ROOT:-}" ]]; then
  export PYTHONPATH="${AA_REPO_ROOT}${PYTHONPATH:+:${PYTHONPATH}}"
elif [[ -d "./align_anything" ]]; then
  export PYTHONPATH="$(pwd)${PYTHONPATH:+:${PYTHONPATH}}"
fi
export LOGLEVEL="${LOGLEVEL:-WARNING}"
PYTHON_BIN="${PYTHON:-python}"
if [[ -z "${WANDB_API_KEY:-}" ]]; then
  export WANDB_MODE="${WANDB_MODE:-offline}"
fi
mkdir -p "$OUTPUT_DIR"
if [[ ! -f "${OUTPUT_DIR}/.gitignore" ]]; then
  printf '*\n' >"${OUTPUT_DIR}/.gitignore"
fi

choose_port() {
  "$PYTHON_BIN" - <<'PY'
import socket
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("127.0.0.1", 0))
    print(s.getsockname()[1])
PY
}
MASTER_PORT="${MASTER_PORT:-$(choose_port)}"
if [[ -z "${NUM_GPUS:-}" ]]; then
  if command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    NUM_GPUS="$("$PYTHON_BIN" - <<'PY'
try:
    import torch
    n = torch.cuda.device_count()
    print(n if n > 0 else 1)
except Exception:
    print(1)
PY
)"
  else
    NUM_GPUS=1
  fi
fi

TRAINER_ARGS=()
add_arg() {
  local flag="$1"
  local value="$2"
  if [[ -n "$value" ]]; then
    TRAINER_ARGS+=("--${flag}" "$value")
  fi
}

# Model paths and endpoints.
add_arg model_name_or_path "${MODEL_NAME_OR_PATH:-}"
add_arg processor_name_or_path "${PROCESSOR_NAME_OR_PATH:-}"
add_arg actor_model_name_or_path "${ACTOR_MODEL_NAME_OR_PATH:-}"
add_arg reward_model_name_or_path "${REWARD_MODEL_NAME_OR_PATH:-}"
add_arg reward_critic_model_name_or_path "${REWARD_CRITIC_MODEL_NAME_OR_PATH:-}"
add_arg cost_model_name_or_path "${COST_MODEL_NAME_OR_PATH:-}"
add_arg cost_critic_model_name_or_path "${COST_CRITIC_MODEL_NAME_OR_PATH:-}"
add_arg remote_rm_url "${REMOTE_RM_URL:-}"

# Dataset groups.
add_arg train_datasets "${TRAIN_DATASETS:-}"
add_arg train_template "${TRAIN_TEMPLATE:-}"
add_arg train_split "${TRAIN_SPLIT:-}"
add_arg train_name "${TRAIN_NAME:-}"
add_arg train_data_files "${TRAIN_DATA_FILES:-${TRAIN_DATA_FILE:-}}"
add_arg train_size "${TRAIN_SIZE:-}"
add_arg train_optional_args "${TRAIN_OPTIONAL_ARGS:-}"
add_arg eval_datasets "${EVAL_DATASETS:-}"
add_arg eval_template "${EVAL_TEMPLATE:-}"
add_arg eval_split "${EVAL_SPLIT:-}"
add_arg eval_name "${EVAL_NAME:-}"
add_arg eval_data_files "${EVAL_DATA_FILES:-${EVAL_DATA_FILE:-}}"
add_arg eval_size "${EVAL_SIZE:-}"
add_arg eval_optional_args "${EVAL_OPTIONAL_ARGS:-}"
add_arg ptx_datasets "${PTX_DATASETS:-}"
add_arg ptx_template "${PTX_TEMPLATE:-}"
add_arg ptx_split "${PTX_SPLIT:-}"
add_arg ptx_name "${PTX_NAME:-}"
add_arg ptx_data_files "${PTX_DATA_FILES:-${PTX_DATA_FILE:-}}"
add_arg ptx_size "${PTX_SIZE:-}"
add_arg ptx_optional_args "${PTX_OPTIONAL_ARGS:-}"

# Output/logging and common hyperparameters.
add_arg output_dir "$OUTPUT_DIR"
add_arg cache_dir "${CACHE_DIR:-}"
add_arg epochs "${EPOCHS:-}"
add_arg learning_rate "${LEARNING_RATE:-}"
add_arg actor_lr "${ACTOR_LR:-}"
add_arg critic_lr "${CRITIC_LR:-}"
add_arg per_device_train_batch_size "${PER_DEVICE_TRAIN_BATCH_SIZE:-}"
add_arg per_device_prompt_batch_size "${PER_DEVICE_PROMPT_BATCH_SIZE:-}"
add_arg per_device_eval_batch_size "${PER_DEVICE_EVAL_BATCH_SIZE:-}"
add_arg gradient_accumulation_steps "${GRADIENT_ACCUMULATION_STEPS:-}"
add_arg model_max_length "${MODEL_MAX_LENGTH:-}"
add_arg max_new_tokens "${MAX_NEW_TOKENS:-}"
add_arg bf16 "${BF16:-}"
add_arg fp16 "${FP16:-}"
add_arg use_lora "${USE_LORA:-}"
add_arg use_bnb "${USE_BNB:-}"
add_arg load_in_4bit "${LOAD_IN_4BIT:-}"
add_arg load_in_8bit "${LOAD_IN_8BIT:-}"
add_arg save_total_limit "${SAVE_TOTAL_LIMIT:-}"
add_arg save_interval "${SAVE_INTERVAL:-}"
add_arg eval_interval "${EVAL_INTERVAL:-}"
add_arg eval_strategy "${EVAL_STRATEGY:-}"
add_arg freeze_mm_proj "${FREEZE_MM_PROJ:-}"
add_arg freeze_vision_tower "${FREEZE_VISION_TOWER:-}"
add_arg freeze_language_model "${FREEZE_LANGUAGE_MODEL:-}"
add_arg freeze_unet "${FREEZE_UNET:-}"
add_arg lora_unet "${LORA_UNET:-}"
add_arg beta "${BETA:-}"
add_arg beta_coeff "${BETA_COEFF:-}"
add_arg kl_coeff "${KL_COEFF:-}"
add_arg clip_range_ratio "${CLIP_RANGE_RATIO:-}"
add_arg num_generations "${NUM_GENERATIONS:-}"
add_arg resolution "${RESOLUTION:-}"

# VLA/action and model architecture leaves.
add_arg data_dir "${DATA_DIR:-}"
add_arg dataset_task_type "${DATASET_TASK_TYPE:-}"
add_arg input_sensors "${INPUT_SENSORS:-}"
add_arg model_architecture "${MODEL_ARCHITECTURE:-}"
add_arg model_version "${MODEL_VERSION:-}"

if [[ ${#EXTRA_TRAINER_ARGS[@]} -gt 0 ]]; then
  TRAINER_ARGS+=("${EXTRA_TRAINER_ARGS[@]}")
fi

COMMAND=()
case "$LAUNCHER" in
  deepspeed)
    COMMAND=(deepspeed)
    if [[ -n "${NUM_GPUS:-}" ]]; then
      COMMAND+=(--num_gpus "$NUM_GPUS")
    fi
    COMMAND+=(--master_port "$MASTER_PORT")
    if [[ -n "${EXTRA_LAUNCH_ARGS:-}" ]]; then
      # shellcheck disable=SC2206
      EXTRA_LAUNCH_ARRAY=(${EXTRA_LAUNCH_ARGS})
      COMMAND+=("${EXTRA_LAUNCH_ARRAY[@]}")
    fi
    COMMAND+=(--module "$TRAINER_MODULE" "${TRAINER_ARGS[@]}")
    ;;
  torchrun)
    COMMAND=(torchrun --nproc_per_node "$NUM_GPUS" --master_port "$MASTER_PORT")
    if [[ -n "${EXTRA_LAUNCH_ARGS:-}" ]]; then
      # shellcheck disable=SC2206
      EXTRA_LAUNCH_ARRAY=(${EXTRA_LAUNCH_ARGS})
      COMMAND+=("${EXTRA_LAUNCH_ARRAY[@]}")
    fi
    COMMAND+=(-m "$TRAINER_MODULE" "${TRAINER_ARGS[@]}")
    ;;
  accelerate)
    COMMAND=(accelerate launch --num_processes "$NUM_GPUS")
    if [[ -n "${EXTRA_LAUNCH_ARGS:-}" ]]; then
      # shellcheck disable=SC2206
      EXTRA_LAUNCH_ARRAY=(${EXTRA_LAUNCH_ARGS})
      COMMAND+=("${EXTRA_LAUNCH_ARRAY[@]}")
    fi
    COMMAND+=(-m "$TRAINER_MODULE" "${TRAINER_ARGS[@]}")
    ;;
  python)
    COMMAND=("$PYTHON_BIN" -m "$TRAINER_MODULE" "${TRAINER_ARGS[@]}")
    ;;
  slurm)
    INNER_LAUNCHER="${INNER_LAUNCHER:-deepspeed}"
    export LAUNCHER="$INNER_LAUNCHER"
    export SLURM_SUBMIT="${SLURM_SUBMIT:-0}"
    export SLURM_JOB_NAME="${SLURM_JOB_NAME:-align-anything-train}"
    export SLURM_PARTITION="${SLURM_PARTITION:-}"
    export SLURM_ACCOUNT="${SLURM_ACCOUNT:-}"
    export SLURM_NODES="${SLURM_NODES:-1}"
    export SLURM_GPUS="${SLURM_GPUS:-$NUM_GPUS}"
    export SLURM_TIME="${SLURM_TIME:-}"
    export SLURM_CPUS_PER_TASK="${SLURM_CPUS_PER_TASK:-}"
    export SLURM_BATCH_FILE="${SLURM_BATCH_FILE:-${OUTPUT_DIR}/align_anything_train.sbatch}"
    export LAUNCHER="$INNER_LAUNCHER"
    INNER_TMP="$(mktemp "${OUTPUT_DIR%/}/align_anything_inner_command.XXXXXX")"
    "$0" --dry-run "${EXTRA_TRAINER_ARGS[@]}" >"$INNER_TMP"
    INNER_COMMAND="$(sed -n 's/^DRY-RUN: //p' "$INNER_TMP" | tail -n 1)"
    rm -f "$INNER_TMP"
    {
      printf '#!/usr/bin/env bash\n'
      printf '#SBATCH --job-name=%s\n' "$SLURM_JOB_NAME"
      printf '#SBATCH --output=%s/slurm-%%j.log\n' "$OUTPUT_DIR"
      printf '#SBATCH --error=%s/slurm-%%j.log\n' "$OUTPUT_DIR"
      [[ -n "$SLURM_PARTITION" ]] && printf '#SBATCH --partition=%s\n' "$SLURM_PARTITION"
      [[ -n "$SLURM_ACCOUNT" ]] && printf '#SBATCH --account=%s\n' "$SLURM_ACCOUNT"
      printf '#SBATCH --nodes=%s\n' "$SLURM_NODES"
      printf '#SBATCH --gres=gpu:%s\n' "$SLURM_GPUS"
      [[ -n "$SLURM_TIME" ]] && printf '#SBATCH --time=%s\n' "$SLURM_TIME"
      [[ -n "$SLURM_CPUS_PER_TASK" ]] && printf '#SBATCH --cpus-per-task=%s\n' "$SLURM_CPUS_PER_TASK"
      printf '\nset -euo pipefail\n'
      if [[ -n "${AA_REPO_ROOT:-}" ]]; then
        printf 'export PYTHONPATH=%q${PYTHONPATH:+:${PYTHONPATH}}\n' "$AA_REPO_ROOT"
      fi
      printf 'export MASTER_PORT=%q\n' "$MASTER_PORT"
      printf 'export WANDB_MODE=%q\n' "${WANDB_MODE:-offline}"
      [[ -n "${ZERO_STAGE_FILE:-}" ]] && printf 'export ZERO_STAGE_FILE=%q\n' "$ZERO_STAGE_FILE"
      printf '%s\n' "$INNER_COMMAND"
    } >"$SLURM_BATCH_FILE"
    echo "Wrote Slurm batch file: $SLURM_BATCH_FILE"
    if [[ "$SLURM_SUBMIT" == "1" ]]; then
      sbatch "$SLURM_BATCH_FILE"
    else
      echo "Review it, then submit with: sbatch $SLURM_BATCH_FILE"
    fi
    exit 0
    ;;
  *)
    echo "ERROR: unsupported LAUNCHER=$LAUNCHER" >&2
    exit 2
    ;;
esac

printf 'Launcher: %s\n' "$LAUNCHER"
printf 'Trainer:  %s\n' "$TRAINER_MODULE"
printf 'Output:   %s\n' "$OUTPUT_DIR"
printf 'Port:     %s\n' "$MASTER_PORT"
printf 'GPUs:     %s\n' "$NUM_GPUS"
if [[ -n "${ZERO_STAGE_FILE:-}" ]]; then
  printf 'DeepSpeed ZERO_STAGE_FILE: %s\n' "$ZERO_STAGE_FILE"
fi
printf -v QUOTED_COMMAND '%q ' "${COMMAND[@]}"
if [[ "$DRY_RUN" == "1" ]]; then
  printf 'DRY-RUN: %s\n' "$QUOTED_COMMAND"
else
  printf 'Running: %s\n' "$QUOTED_COMMAND"
  "${COMMAND[@]}"
fi
