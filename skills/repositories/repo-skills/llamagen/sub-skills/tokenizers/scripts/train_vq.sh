#!/usr/bin/env bash
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"
set -euo pipefail
set -x

exec torchrun \
  --nnodes="${nnodes:?set nnodes}" --nproc_per_node="${nproc_per_node:?set nproc_per_node}" --node_rank="${node_rank:?set node_rank}" \
  --master_addr="${master_addr:?set master_addr}" --master_port="${master_port:?set master_port}" \
  tokenizer/tokenizer_image/vq_train.py "$@"
