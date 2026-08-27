#!/usr/bin/env python3
"""Run a tiny RobustVideoMatting MattingNetwork forward pass.

The script adapts the repository's CUDA-only speed test into a safe smoke test.
It never downloads weights and never runs a long benchmark. Pass --repo-root if
``from model import MattingNetwork`` is not already importable.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"--repo-root does not exist: {root}")
    sys.path.insert(0, str(root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test RobustVideoMatting's MattingNetwork on synthetic tensors.")
    parser.add_argument("--repo-root", help="Optional local RobustVideoMatting checkout to add to sys.path.")
    parser.add_argument("--variant", default="mobilenetv3", choices=["mobilenetv3", "resnet50"], help="Model variant.")
    parser.add_argument("--device", default="cpu", choices=["cpu", "cuda", "auto"], help="Device to use.")
    parser.add_argument("--height", type=int, default=32, help="Synthetic input height.")
    parser.add_argument("--width", type=int, default=32, help="Synthetic input width.")
    parser.add_argument("--time-steps", type=int, default=1, help="Use a 5D [B,T,C,H,W] input when >1.")
    parser.add_argument("--downsample-ratio", type=float, default=0.5, help="Forward downsample_ratio in (0, 1].")
    parser.add_argument("--segmentation-pass", action="store_true", help="Run segmentation_pass=True and report logits instead of fgr/pha.")
    args = parser.parse_args()

    if not (0 < args.downsample_ratio <= 1):
        raise SystemExit("--downsample-ratio must be > 0 and <= 1")
    if args.height < 8 or args.width < 8:
        raise SystemExit("--height and --width should be at least 8 for a meaningful smoke test")
    if args.time_steps < 1:
        raise SystemExit("--time-steps must be >= 1")

    _add_repo_root(args.repo_root)

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("Missing dependency: install PyTorch before running this smoke test.") from exc
    try:
        from model import MattingNetwork
    except ImportError as exc:
        raise SystemExit("Could not import `model.MattingNetwork`; pass --repo-root pointing at a RobustVideoMatting checkout.") from exc

    if args.device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = args.device
    if device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA requested but PyTorch reports no CUDA device. Use --device cpu or install a CUDA-capable torch build.")

    model = MattingNetwork(args.variant).eval().to(device)
    with torch.no_grad():
        if args.time_steps == 1:
            src = torch.rand(1, 3, args.height, args.width, device=device)
        else:
            src = torch.rand(1, args.time_steps, 3, args.height, args.width, device=device)
        outputs = model(src, None, None, None, None, args.downsample_ratio, segmentation_pass=args.segmentation_pass)

    if args.segmentation_pass:
        seg, *rec = outputs
        payload = {
            "mode": "segmentation_pass",
            "variant": args.variant,
            "device": device,
            "input_shape": list(src.shape),
            "seg_shape": list(seg.shape),
            "rec_shapes": [list(r.shape) for r in rec],
        }
    else:
        fgr, pha, *rec = outputs
        payload = {
            "mode": "matting",
            "variant": args.variant,
            "device": device,
            "input_shape": list(src.shape),
            "fgr_shape": list(fgr.shape),
            "pha_shape": list(pha.shape),
            "rec_shapes": [list(r.shape) for r in rec],
            "fgr_minmax": [float(fgr.min().item()), float(fgr.max().item())],
            "pha_minmax": [float(pha.min().item()), float(pha.max().item())],
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
