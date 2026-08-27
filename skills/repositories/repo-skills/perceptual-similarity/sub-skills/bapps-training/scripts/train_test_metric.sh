#!/usr/bin/env bash
set -euo pipefail

# Smoke-friendly training + evaluation wrapper.
#
# Positional arguments:
#   $1 = trial name (default: smoke)
#   $2 = backbone net (default: alex)
#
# Environment overrides:
#   DATASET_ROOT, TRAIN_DATASETS, VAL_DATASETS, MODEL, VERSION, BATCH_SIZE,
#   EPOCHS, MAX_STEPS, CHECKPOINTS_DIR, USE_GPU, FROM_SCRATCH, TRAIN_TRUNK,
#   LR, BETA1

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRIAL="${1:-smoke}"
NET="${2:-alex}"
if [[ $# -ge 2 ]]; then
  shift 2
elif [[ $# -ge 1 ]]; then
  shift 1
fi

DATASET_ROOT="${DATASET_ROOT:-dataset}"
TRAIN_DATASETS="${TRAIN_DATASETS:-train/traditional train/cnn train/mix}"
VAL_DATASETS="${VAL_DATASETS:-val/traditional val/cnn val/superres val/deblur val/color val/frameinterp}"
MODEL="${MODEL:-lpips}"
VERSION="${VERSION:-0.1}"
BATCH_SIZE="${BATCH_SIZE:-1}"
EPOCHS="${EPOCHS:-1}"
MAX_STEPS="${MAX_STEPS:-1}"
CHECKPOINTS_DIR="${CHECKPOINTS_DIR:-checkpoints}"
USE_GPU="${USE_GPU:-0}"
FROM_SCRATCH="${FROM_SCRATCH:-0}"
TRAIN_TRUNK="${TRAIN_TRUNK:-0}"
LR="${LR:-0.0001}"
BETA1="${BETA1:-0.5}"

read -r -a TRAIN_SPLITS <<<"${TRAIN_DATASETS}"
read -r -a VAL_SPLITS <<<"${VAL_DATASETS}"

TRAIN_ARGS=(
  python "${SCRIPT_DIR}/train_bapps.py"
  --dataset_root "${DATASET_ROOT}"
  --datasets "${TRAIN_SPLITS[@]}"
  --model "${MODEL}"
  --net "${NET}"
  --version "${VERSION}"
  --batch_size "${BATCH_SIZE}"
  --epochs "${EPOCHS}"
  --max_steps "${MAX_STEPS}"
  --checkpoints_dir "${CHECKPOINTS_DIR}"
  --name "${NET}_${TRIAL}"
  --lr "${LR}"
  --beta1 "${BETA1}"
  "$@"
)
if [[ "${USE_GPU}" == "1" ]]; then
  TRAIN_ARGS+=(--use_gpu)
fi
if [[ "${FROM_SCRATCH}" == "1" ]]; then
  TRAIN_ARGS+=(--from_scratch)
fi
if [[ "${TRAIN_TRUNK}" == "1" ]]; then
  TRAIN_ARGS+=(--train_trunk)
fi

"${TRAIN_ARGS[@]}"

MODEL_PATH="${CHECKPOINTS_DIR}/${NET}_${TRIAL}/latest_net_.pth"
SCORE_ARGS=(
  python "${SCRIPT_DIR}/../../bapps-evaluation/scripts/score_bapps.py"
  --dataset_mode 2afc
  --dataset_root "${DATASET_ROOT}"
  --datasets "${VAL_SPLITS[@]}"
  --model "${MODEL}"
  --net "${NET}"
  --version "${VERSION}"
  --batch_size "${BATCH_SIZE}"
  --model_path "${MODEL_PATH}"
)
if [[ "${USE_GPU}" == "1" ]]; then
  SCORE_ARGS+=(--use_gpu)
fi
if [[ "${FROM_SCRATCH}" == "1" ]]; then
  SCORE_ARGS+=(--from_scratch)
fi
if [[ "${TRAIN_TRUNK}" == "1" ]]; then
  SCORE_ARGS+=(--train_trunk)
fi

"${SCORE_ARGS[@]}"
