#!/usr/bin/env bash
set -euo pipefail
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../../.." && pwd)"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:$PYTHONPATH}"

exec torchrun \
  --nnodes=1 --nproc_per_node=8 --node_rank=0 \
  --master_port=12335 \
  autoregressive/train/extract_codes_c2i.py \
  "$@"
