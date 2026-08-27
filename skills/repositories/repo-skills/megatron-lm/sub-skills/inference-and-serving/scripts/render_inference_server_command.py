#!/usr/bin/env python3
"""Render a Megatron high-level inference server command template."""

from __future__ import annotations

import argparse


def main() -> int:
    p = argparse.ArgumentParser(description="Render an inference server torchrun command.")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--tokenizer-type", default="HuggingFaceTokenizer")
    p.add_argument("--gpus", type=int, default=1)
    p.add_argument("--tp", type=int, default=1)
    p.add_argument("--pp", type=int, default=1)
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--frontend-replicas", type=int, default=4)
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()
    parts = [
        "python -m torch.distributed.run",
        f"  --nproc-per-node {args.gpus}",
        "  examples/inference/launch_inference_server.py",
        f"  --load {args.checkpoint}",
        f"  --tokenizer-type {args.tokenizer_type}",
        f"  --tensor-model-parallel-size {args.tp}",
        f"  --pipeline-model-parallel-size {args.pp}",
        f"  --host {args.host}",
        f"  --port {args.port}",
        f"  --frontend-replicas {args.frontend_replicas}",
    ]
    if args.verbose:
        parts.append("  --verbose")
    print(" \\\n".join(parts))
    if args.host == "0.0.0.0":
        print("\n# Warning: this binds externally; confirm network/security policy first.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
