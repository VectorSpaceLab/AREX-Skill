#!/usr/bin/env bash
set -euo pipefail
set -x

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../../../.." && pwd)"
cd "${REPO_ROOT}"
export PYTHONPATH="${REPO_ROOT}${PYTHONPATH:+:$PYTHONPATH}"

exec torchrun \
  --nnodes=1 --nproc_per_node=8 --node_rank=0 \
  --master_port=12337 \
  language/extract_t5_feature.py \
  --data-path /path/to/laion_coco50M \
  --t5-path /path/to/laion_coco50M_flan_t5_xl \
  --caption-key blip \
  "$@"
