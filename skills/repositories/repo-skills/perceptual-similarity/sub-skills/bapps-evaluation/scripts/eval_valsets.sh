#!/usr/bin/env bash
set -euo pipefail

# Evaluate the standard BAPPS validation splits with the bundled score helper.
#
# Configure through environment variables when needed:
#   DATASET_ROOT, DATASET_MODE, DATASETS, MODEL, NET, COLORSpace, BATCH_SIZE,
#   VERSION, MODEL_PATH, USE_GPU

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATASET_ROOT="${DATASET_ROOT:-dataset}"
DATASET_MODE="${DATASET_MODE:-2afc}"
MODEL="${MODEL:-lpips}"
NET="${NET:-alex}"
COLORSPACE="${COLORSPACE:-Lab}"
BATCH_SIZE="${BATCH_SIZE:-50}"
VERSION="${VERSION:-0.1}"
MODEL_PATH="${MODEL_PATH:-}"
USE_GPU="${USE_GPU:-0}"

if [[ -n "${DATASETS:-}" ]]; then
  read -r -a DATASET_LIST <<<"${DATASETS}"
else
  if [[ "${DATASET_MODE}" == "jnd" ]]; then
    DATASET_LIST=(val/traditional val/cnn)
  else
    DATASET_LIST=(val/traditional val/cnn val/superres val/deblur val/color val/frameinterp)
  fi
fi

cmd=(python "${SCRIPT_DIR}/score_bapps.py" --dataset_mode "${DATASET_MODE}" --dataset_root "${DATASET_ROOT}" --model "${MODEL}" --net "${NET}" --colorspace "${COLORSPACE}" --batch_size "${BATCH_SIZE}" --version "${VERSION}" "$@")
if [[ -n "${MODEL_PATH}" ]]; then
  cmd+=(--model_path "${MODEL_PATH}")
fi
if [[ "${USE_GPU}" == "1" ]]; then
  cmd+=(--use_gpu)
fi
cmd+=(--datasets "${DATASET_LIST[@]}")

exec "${cmd[@]}"
