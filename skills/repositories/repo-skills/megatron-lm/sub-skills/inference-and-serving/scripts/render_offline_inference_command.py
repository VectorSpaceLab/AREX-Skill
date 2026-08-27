#!/usr/bin/env python3
"""Render a Megatron offline inference command template."""

from __future__ import annotations

import argparse


def main() -> int:
    p = argparse.ArgumentParser(description="Render an offline inference torchrun command.")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--tokenizer-type", default="HuggingFaceTokenizer")
    p.add_argument("--gpus", type=int, default=1)
    p.add_argument("--tp", type=int, default=1)
    p.add_argument("--pp", type=int, default=1)
    p.add_argument("--tokens", type=int, default=64)
    p.add_argument("--prompt", default="Hello Megatron")
    p.add_argument("--coordinator", action="store_true")
    p.add_argument("--async-mode", action="store_true")
    args = p.parse_args()
    parts = [
        "python -m torch.distributed.run",
        f"  --nproc-per-node {args.gpus}",
        "  examples/inference/offline_inference.py",
        f"  --load {args.checkpoint}",
        f"  --tokenizer-type {args.tokenizer_type}",
        f"  --tensor-model-parallel-size {args.tp}",
        f"  --pipeline-model-parallel-size {args.pp}",
        f"  --num-tokens-to-generate {args.tokens}",
        f"  --prompts {args.prompt!r}",
    ]
    if args.coordinator:
        parts.append("  --use-coordinator")
    if args.async_mode:
        parts.append("  --async-mode")
    print(" \\\n".join(parts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
