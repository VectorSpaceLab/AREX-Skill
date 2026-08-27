#!/usr/bin/env python3
"""Run a tiny BackgroundMattingV2 forward pass without checkpoints or data.

Safe by default:
- requires an explicit --repo-root
- uses random tensors only
- does not download or write artifacts

Example:
    python sub-skills/inference-and-demo/scripts/smoke_forward.py \
      --repo-root /path/to/BackgroundMattingV2 --device cuda
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="BackgroundMattingV2 tiny forward smoke")
    p.add_argument("--repo-root", required=True)
    p.add_argument("--model-type", choices=["mattingbase", "mattingrefine"], default="mattingrefine")
    p.add_argument("--backbone", choices=["resnet101", "resnet50", "mobilenetv2"], default="mobilenetv2")
    p.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--backend", choices=["pytorch", "torchscript"], default="pytorch")
    p.add_argument("--precision", choices=["float32", "float16"], default="float32")
    p.add_argument("--height", type=int, default=64)
    p.add_argument("--width", type=int, default=64)
    p.add_argument("--refine-mode", choices=["full", "sampling", "thresholding"], default="sampling")
    p.add_argument("--refine-sample-pixels", type=int, default=16)
    p.add_argument("--refine-threshold", type=float, default=0.1)
    p.add_argument("--refine-kernel-size", type=int, default=3)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"repo-root does not exist: {repo_root}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(repo_root))

    try:
        import torch
        from model import MattingBase, MattingRefine
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"import failed: {exc}", file=sys.stderr)
        return 3

    if args.device == "cuda" and not torch.cuda.is_available():
        print("requested CUDA but torch.cuda.is_available() is false", file=sys.stderr)
        return 4
    if args.device == "cpu" and args.precision == "float16":
        print("float16 is not supported on CPU for this smoke", file=sys.stderr)
        return 5

    dtype = torch.float16 if args.precision == "float16" else torch.float32
    device = torch.device(args.device)

    try:
        if args.model_type == "mattingbase":
            model = MattingBase(args.backbone)
        else:
            model = MattingRefine(
                args.backbone,
                backbone_scale=0.25,
                refine_mode=args.refine_mode,
                refine_sample_pixels=args.refine_sample_pixels,
                refine_threshold=args.refine_threshold,
                refine_kernel_size=args.refine_kernel_size,
            )
        if args.backend == "torchscript":
            model = torch.jit.script(model)
        model = model.eval().to(device=device, dtype=dtype)
        src = torch.rand(1, 3, args.height, args.width, device=device, dtype=dtype)
        bgr = torch.rand(1, 3, args.height, args.width, device=device, dtype=dtype)
        with torch.no_grad():
            outputs = model(src, bgr)
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"forward smoke failed: {exc}", file=sys.stderr)
        return 6

    print(f"python={sys.executable}")
    print(f"torch={torch.__version__} cuda={torch.version.cuda}")
    print(f"MattingBase={inspect.signature(MattingBase)}")
    print(f"MattingRefine={inspect.signature(MattingRefine)}")
    print(f"device={device} backend={args.backend} precision={args.precision}")
    print(f"output_shapes={[tuple(x.shape) for x in outputs]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
