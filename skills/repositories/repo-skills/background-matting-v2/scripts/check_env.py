#!/usr/bin/env python3
"""Check that the repo modules import and a tiny matting forward pass works.

Safe by default:
- requires an explicit --repo-root to inspect a checkout outside the current
  working directory
- never downloads checkpoints or datasets
- only performs a tiny random forward pass

Example:
    python scripts/check_env.py --repo-root /path/to/BackgroundMattingV2 --device cuda
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Check BackgroundMattingV2 import and smoke readiness")
    p.add_argument("--repo-root", required=True, help="Path to a BackgroundMattingV2 checkout")
    p.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    p.add_argument("--model-type", choices=["mattingbase", "mattingrefine"], default="mattingrefine")
    p.add_argument("--backbone", choices=["resnet101", "resnet50", "mobilenetv2"], default="mobilenetv2")
    p.add_argument("--backend", choices=["pytorch", "torchscript"], default="pytorch")
    p.add_argument("--height", type=int, default=64)
    p.add_argument("--width", type=int, default=64)
    p.add_argument("--refine-mode", choices=["full", "sampling", "thresholding"], default="sampling")
    p.add_argument("--refine-sample-pixels", type=int, default=16)
    p.add_argument("--precision", choices=["float32", "float16"], default="float32")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    if not repo_root.exists():
        print(f"repo-root does not exist: {repo_root}", file=sys.stderr)
        return 2

    sys.path.insert(0, str(repo_root))

    import torch
    from model import MattingBase, MattingRefine

    print(f"python={sys.executable}")
    print(f"torch={torch.__version__} cuda={torch.version.cuda}")
    print(f"cuda_available={torch.cuda.is_available()} device_count={torch.cuda.device_count()}")
    print(f"MattingBase={inspect.signature(MattingBase)}")
    print(f"MattingRefine={inspect.signature(MattingRefine)}")

    if args.device == "cuda" and not torch.cuda.is_available():
        print("requested CUDA but torch.cuda.is_available() is false", file=sys.stderr)
        return 3

    device = torch.device(args.device)
    dtype = torch.float16 if args.precision == "float16" else torch.float32
    if args.device == "cpu" and dtype == torch.float16:
        print("float16 is not supported on CPU for this smoke", file=sys.stderr)
        return 4

    if args.model_type == "mattingbase":
        model = MattingBase(args.backbone)
    else:
        model = MattingRefine(
            args.backbone,
            backbone_scale=0.25,
            refine_mode=args.refine_mode,
            refine_sample_pixels=args.refine_sample_pixels,
        )

    if args.backend == "torchscript":
        model = torch.jit.script(model)

    model = model.eval().to(device=device, dtype=dtype)
    src = torch.rand(1, 3, args.height, args.width, device=device, dtype=dtype)
    bgr = torch.rand(1, 3, args.height, args.width, device=device, dtype=dtype)

    with torch.no_grad():
        outputs = model(src, bgr)

    shapes = [tuple(x.shape) for x in outputs]
    print(f"output_shapes={shapes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
