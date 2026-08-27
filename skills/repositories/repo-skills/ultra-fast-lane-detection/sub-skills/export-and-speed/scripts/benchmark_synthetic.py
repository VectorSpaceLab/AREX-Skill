#!/usr/bin/env python3
"""Benchmark a tiny synthetic forward pass for the lane model.

This helper gives a configurable throughput estimate without requiring a real
camera or dataset.

Example:
    python benchmark_synthetic.py --repo-root . --device cuda --loops 100 --warmup 10
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark a synthetic lane-model forward pass.")
    parser.add_argument("--repo-root", required=True, help="Path to the Ultra-Fast-Lane-Detection checkout")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda", help="Benchmark device")
    parser.add_argument("--backbone", default="18", help="Backbone id such as 18 or 50")
    parser.add_argument("--griding-num", type=int, default=200, help="Grid count used in cls_dim")
    parser.add_argument("--cls-num-per-lane", type=int, default=18, help="Class count per lane anchor")
    parser.add_argument("--num-lanes", type=int, default=4, help="Number of lane slots")
    parser.add_argument("--warmup", type=int, default=10, help="Warmup iterations before timing")
    parser.add_argument("--loops", type=int, default=100, help="Timed iterations")
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
    cls_dim = (args.griding_num + 1, args.cls_num_per_lane, args.num_lanes)
    net = parsingNet(pretrained=False, backbone=args.backbone, cls_dim=cls_dim, use_aux=False).to(device).eval()
    x = torch.zeros((1, 3, 288, 800), device=device)

    with torch.no_grad():
        for _ in range(max(args.warmup, 0)):
            _ = net(x)

        times = []
        for _ in range(max(args.loops, 1)):
            start = time.time()
            _ = net(x)
            if device.type == "cuda":
                torch.cuda.synchronize()
            end = time.time()
            times.append(end - start)

    avg = float(np.mean(times))
    print(f"average time: {avg}")
    print(f"average fps: {1 / avg}")
    print(f"fastest time: {min(times)}")
    print(f"fastest fps: {1 / min(times)}")
    print(f"slowest time: {max(times)}")
    print(f"slowest fps: {1 / max(times)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
