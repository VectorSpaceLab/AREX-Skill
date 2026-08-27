#!/usr/bin/env python3
"""Smoke-check FLA layer/model imports and tiny construction without downloads.

The CPU path verifies imports, signatures, and a tiny Transformers auto-model
construction. The CUDA path additionally runs one tiny GatedLinearAttention
forward pass. No checkpoints, tokenizers, datasets, or native tests are loaded.
"""

from __future__ import annotations

import argparse
import inspect
import os
import sys

os.environ.setdefault("TRANSFORMERS_VERBOSITY", "critical")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke-check FLA layer/model APIs without downloads.")
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cpu", help="device for optional layer forward smoke")
    parser.add_argument("--require-cuda", action="store_true", help="fail if --device cuda is requested but CUDA is unavailable")
    parser.add_argument("--build-auto-model", action="store_true", help="also build a tiny AutoModelForCausalLM.from_config instance; this may emit third-party logs")
    return parser.parse_args()


def import_or_fail(name: str):
    try:
        return __import__(name, fromlist=["*"])
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: failed to import {name}: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return None


def main() -> int:
    args = parse_args()
    torch = import_or_fail("torch")
    fla_layers = import_or_fail("fla.layers")
    fla_models = import_or_fail("fla.models")
    fla_modules = import_or_fail("fla.modules")
    if None in (torch, fla_layers, fla_models, fla_modules):
        print("HINT: install flash-linear-attention with a backend extra and required base dependencies.", file=sys.stderr)
        return 2

    from fla.layers import GatedLinearAttention
    from fla.models import GLAConfig, KDAConfig
    from fla.modules import FusedLinearCrossEntropyLoss, RMSNorm

    print("== Verified constructors ==")
    for obj in (GatedLinearAttention, GLAConfig, KDAConfig, RMSNorm, FusedLinearCrossEntropyLoss):
        target = obj.__init__ if inspect.isclass(obj) else obj
        print(f"{obj.__name__}{inspect.signature(target)}")

    if args.build_auto_model:
        try:
            from transformers import AutoModelForCausalLM
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: failed to import transformers AutoModelForCausalLM: {exc.__class__.__name__}: {exc}", file=sys.stderr)
            return 4
        config = GLAConfig(
            hidden_size=32,
            num_hidden_layers=1,
            num_heads=4,
            hidden_ratio=2,
            max_position_embeddings=64,
            vocab_size=128,
            fuse_norm=False,
            fuse_swiglu=False,
            fuse_cross_entropy=False,
        )
        model = AutoModelForCausalLM.from_config(config)
        params = sum(p.numel() for p in model.parameters())
        print(f"tiny AutoModelForCausalLM.from_config: ok ({model.__class__.__name__}, parameters={params})")

    if args.device == "cuda":
        if not torch.cuda.is_available():
            message = "CUDA requested but torch.cuda.is_available() is False"
            if args.require_cuda:
                print(f"ERROR: {message}", file=sys.stderr)
                return 3
            print(f"SKIP: {message}")
            return 0
        dtype = torch.bfloat16
        layer = GatedLinearAttention(
            mode="chunk",
            hidden_size=128,
            expand_k=1,
            expand_v=1,
            num_heads=2,
            use_short_conv=False,
            fuse_norm=True,
        ).to(device="cuda", dtype=dtype)
        x = torch.randn(1, 64, 128, device="cuda", dtype=dtype)
        y, *_ = layer(x)
        torch.cuda.synchronize()
        print(f"cuda GatedLinearAttention forward: ok (shape={tuple(y.shape)}, dtype={y.dtype})")

    print("layer/model smoke completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
