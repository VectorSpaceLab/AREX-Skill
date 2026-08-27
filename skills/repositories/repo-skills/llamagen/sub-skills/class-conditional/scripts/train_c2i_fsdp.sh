#!/usr/bin/env bash
set -euo pipefail

# FSDP c2i training wrapper.
# Distributed env vars expected by torchrun:
#   nnodes, nproc_per_node, node_rank, master_addr, master_port
# Resume expects a directory with consolidated.pth, optimizer shards,
# and resume_step.txt; the saved optimizer shard count must match world size.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)"
cd "$repo_root"
export PYTHONPATH="$repo_root${PYTHONPATH:+:$PYTHONPATH}"

: "${nnodes:?set nnodes before calling this wrapper}"
: "${nproc_per_node:?set nproc_per_node before calling this wrapper}"
: "${node_rank:?set node_rank before calling this wrapper}"
: "${master_addr:?set master_addr before calling this wrapper}"
: "${master_port:?set master_port before calling this wrapper}"

exec torchrun \
  --nnodes="$nnodes" \
  --nproc_per_node="$nproc_per_node" \
  --node_rank="$node_rank" \
  --master_addr="$master_addr" \
  --master_port="$master_port" \
  autoregressive/train/train_c2i_fsdp.py "$@" --gpt-type c2i
