#!/usr/bin/env python3
"""Tiny CUDA smoke check for the training-side lane model.

This helper verifies that the repo's model can be constructed and run on the
selected device before a user launches a training job.

Example:
    python model_cuda_smoke.py --repo-root . --backbone 18 --griding-num 200
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny parsingNet smoke test.")
    parser.add_argument("--repo-root", required=True, help="Path to the Ultra-Fast-Lane-Detection checkout")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda", help="Device to smoke test")
    parser.add_argument("--backbone", default="18", help="Backbone id such as 18 or 50")
    parser.add_argument("--griding-num", type=int, default=200, help="Grid count used for the class dimension")
    parser.add_argument("--num-lanes", type=int, default=4, help="Number of lane slots")
    parser.add_argument("--use-aux", action="store_true", help="Enable the auxiliary segmentation head")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    from model.model import parsingNet  # noqa: WPS433

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available in this environment", file=sys.stderr)
        return 3

    device = torch.device(args.device)
    cls_num_per_lane = 18 if args.griding_num >= 200 else 56
    cls_dim = (args.griding_num + 1, cls_num_per_lane, args.num_lanes)
    net = parsingNet(pretrained=False, backbone=args.backbone, cls_dim=cls_dim, use_aux=args.use_aux).to(device).eval()

    with torch.no_grad():
        out = net(torch.zeros(1, 3, 288, 800, device=device))

    if isinstance(out, tuple):
        print("output_shapes", [tuple(item.shape) for item in out])
    else:
        print("output_shape", tuple(out.shape))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
