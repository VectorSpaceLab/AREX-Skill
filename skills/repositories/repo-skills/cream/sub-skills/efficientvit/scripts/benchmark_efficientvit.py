#!/usr/bin/env python3
"""Small configurable throughput benchmark for EfficientViT.

The original repo script runs long warmup and measurement windows. This helper
keeps the same spirit but exposes short, explicit flags so future agents can
run a bounded import / throughput sanity check.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
import sys

import torch


def load_model(model_name: str, repo_root: Path):
    classification_root = repo_root / "EfficientViT" / "classification"
    if not classification_root.exists():
        raise SystemExit(f"could not find EfficientViT classification root at {classification_root}")
    sys.path.insert(0, str(classification_root))
    from model.build import EfficientViT_M0, EfficientViT_M1, EfficientViT_M2, EfficientViT_M3, EfficientViT_M4, EfficientViT_M5

    builders = {
        "EfficientViT_M0": EfficientViT_M0,
        "EfficientViT_M1": EfficientViT_M1,
        "EfficientViT_M2": EfficientViT_M2,
        "EfficientViT_M3": EfficientViT_M3,
        "EfficientViT_M4": EfficientViT_M4,
        "EfficientViT_M5": EfficientViT_M5,
    }
    if model_name not in builders:
        raise SystemExit(f"unknown model: {model_name}")
    return builders[model_name](num_classes=1000)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark EfficientViT throughput")
    parser.add_argument("--repo-root", default=".", help="Path to the Cream checkout that contains EfficientViT/")
    parser.add_argument("--model", default="EfficientViT_M4")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"])
    parser.add_argument("--batch-size", type=int, default=64)
    parser.add_argument("--resolution", type=int, default=224)
    parser.add_argument("--warmup-seconds", type=float, default=2.0)
    parser.add_argument("--measure-seconds", type=float, default=5.0)
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but not available")

    repo_root = Path(args.repo_root).expanduser().resolve()
    device = torch.device(args.device)
    model = load_model(args.model, repo_root).to(device).eval()
    if hasattr(model, "head") and hasattr(model.head, "fuse"):
        # keep behavior close to the source benchmark, but only if the helper exists
        model = model
    inputs = torch.randn(args.batch_size, 3, args.resolution, args.resolution, device=device)

    with torch.no_grad():
        start = time.time()
        while time.time() - start < args.warmup_seconds:
            model(inputs)
        timings = []
        start = time.time()
        while time.time() - start < args.measure_seconds:
            t0 = time.time()
            model(inputs)
            if device.type == "cuda":
                torch.cuda.synchronize()
            timings.append(time.time() - t0)

    if not timings:
        raise SystemExit("no timing samples collected")
    mean = sum(timings) / len(timings)
    print(f"{args.model} on {args.device}: {args.batch_size / mean:.2f} images/s at batch size {args.batch_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
