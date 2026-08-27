#!/usr/bin/env bash
# Parameterized training launcher for Ultra-Fast-Lane-Detection.
#
# Purpose: provide a safer, editable replacement for the repo's hardcoded
# launch_training.sh snippet.
#
# Example:
#   CUDA_VISIBLE_DEVICES=0,1 NGPUS=2 CONFIG=configs/culane.py \
#     DATA_ROOT=<CULANE_ROOT> LOG_PATH=<LOG_DIR_OUTSIDE_REPO> ./launch_training_template.sh

set -euo pipefail

: "${CONFIG:?set CONFIG to a config file such as configs/culane.py}"
: "${DATA_ROOT:?set DATA_ROOT to the dataset root}"
: "${LOG_PATH:?set LOG_PATH to an output directory outside the repo}"
: "${NGPUS:=1}"
: "${CUDA_VISIBLE_DEVICES:=0}"
: "${OMP_NUM_THREADS:=1}"

export CUDA_VISIBLE_DEVICES
export OMP_NUM_THREADS

if [[ ! -f "${CONFIG}" ]]; then
  echo "missing config: ${CONFIG}" >&2
  exit 2
fi

python -m torch.distributed.launch --nproc_per_node="${NGPUS}" train.py "${CONFIG}" \
  --data_root "${DATA_ROOT}" \
  --log_path "${LOG_PATH}"
