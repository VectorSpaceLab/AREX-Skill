#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PRETRAINED="${PRETRAINED:-${MODEL_PATH:-}}"
if [[ -z "${PRETRAINED}" ]]; then
  echo "error: set PRETRAINED or MODEL_PATH to the base checkpoint" >&2
  exit 1
fi

if [[ -z "${DATASET:-}" ]]; then
  echo "error: set DATASET to one or more tokenized dataset paths" >&2
  exit 1
fi

NPROC_PER_NODE="${NPROC_PER_NODE:-8}"
MASTER_PORT="${MASTER_PORT:-30013}"
HOSTFILE_ARG=()
if [[ -n "${HOSTFILE:-}" ]]; then
  HOSTFILE_ARG=(--hostfile "${HOSTFILE}")
fi

exec colossalai run --nproc_per_node "${NPROC_PER_NODE}" "${HOSTFILE_ARG[@]}" --master_port "${MASTER_PORT}" "${SCRIPT_DIR}/train_colossalai.py" \
  --pretrained "${PRETRAINED}" \
  --dataset ${DATASET} \
  --plugin "${PLUGIN:-zero2}" \
  --save_interval "${SAVE_INTERVAL:-400}" \
  --save_dir "${SAVE_DIR:-./output_models/llm4decompile}" \
  --tensorboard_dir "${TENSORBOARD_DIR:-./tensorboard/llm4decompile}" \
  --config_file "${CONFIG_FILE:-./configs/llm4decompile.json}" \
  --num_epochs "${NUM_EPOCHS:-2}" \
  --micro_batch_size "${MICRO_BATCH_SIZE:-8}" \
  --accumulation_steps "${ACCUMULATION_STEPS:-8}" \
  --lr "${LR:-2e-5}" \
  --mixed_precision "${MIXED_PRECISION:-bf16}" \
  --max_length "${MAX_LENGTH:-4096}" \
  --padding_mode "${PADDING_MODE:-longest}" \
  ${USE_FLASH_ATTN:+--use_flash_attn} \
  ${USE_GRAD_CHECKPOINT:+--use_grad_checkpoint} \
  ${USE_NEFT:+--use_neft} \
  ${FREEZE_NON_EMBEDS:+--freeze_non_embeds_params}
