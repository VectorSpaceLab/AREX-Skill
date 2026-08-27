#!/usr/bin/env python3
"""Render a conservative Megatron-LM pretrain command template."""

from __future__ import annotations

import argparse


def main() -> int:
    p = argparse.ArgumentParser(description="Render a Megatron-LM torch.distributed.run template.")
    p.add_argument("--entrypoint", default="pretrain_gpt.py", help="Training entrypoint name.")
    p.add_argument("--gpus-per-node", type=int, default=8)
    p.add_argument("--nodes", type=int, default=1)
    p.add_argument("--tp", type=int, default=1)
    p.add_argument("--pp", type=int, default=1)
    p.add_argument("--cp", type=int, default=1)
    p.add_argument("--layers", type=int, default=2)
    p.add_argument("--hidden-size", type=int, default=128)
    p.add_argument("--heads", type=int, default=4)
    p.add_argument("--seq-length", type=int, default=128)
    p.add_argument("--micro-batch-size", type=int, default=1)
    p.add_argument("--global-batch-size", type=int, default=8)
    p.add_argument("--iters", type=int, default=10)
    p.add_argument("--data-path", default=None, help="Preprocessed data prefix. Omit for mock data.")
    p.add_argument("--bf16", action="store_true", default=True)
    args = p.parse_args()

    cmd = [
        "python -m torch.distributed.run",
        f"  --nproc-per-node {args.gpus_per_node}",
    ]
    if args.nodes > 1:
        cmd.extend([
            f"  --nnodes {args.nodes}",
            "  --node-rank <NODE_RANK>",
            "  --master-addr <MASTER_ADDR>",
            "  --master-port <MASTER_PORT>",
        ])
    cmd.append(f"  {args.entrypoint}")
    flags = [
        ("--tensor-model-parallel-size", args.tp),
        ("--pipeline-model-parallel-size", args.pp),
        ("--context-parallel-size", args.cp),
        ("--num-layers", args.layers),
        ("--hidden-size", args.hidden_size),
        ("--num-attention-heads", args.heads),
        ("--seq-length", args.seq_length),
        ("--micro-batch-size", args.micro_batch_size),
        ("--global-batch-size", args.global_batch_size),
        ("--train-iters", args.iters),
    ]
    for name, value in flags:
        cmd.append(f"  {name} {value}")
    if args.bf16:
        cmd.append("  --bf16")
    if args.data_path:
        cmd.extend([f"  --data-path {args.data_path}", "  --split 949,50,1"])
    else:
        cmd.append("  --mock-data")
    print(" \\\n".join(cmd))
    print("\n# Validate topology and add tokenizer/checkpoint/logging flags before real training.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
