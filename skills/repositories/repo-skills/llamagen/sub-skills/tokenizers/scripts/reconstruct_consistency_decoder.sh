#!/usr/bin/env bash
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"
set -euo pipefail
set -x

exec torchrun \
  --nnodes=1 --nproc_per_node=8 --node_rank=0 \
  --master_port=12344 \
  tokenizer/consistencydecoder/reconstruction_cd_ddp.py \
  "$@"
