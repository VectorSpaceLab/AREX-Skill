#!/usr/bin/env python3
"""Quick smoke check for Ultra-Fast-Lane-Detection.

This helper verifies that the repo can be imported from a given checkout, that
config loading works, and that an optional CUDA forward pass succeeds.

Example:
    python check_environment.py --repo-root . --device cuda
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test the Ultra-Fast-Lane-Detection environment.")
    parser.add_argument("--repo-root", required=True, help="Path to the Ultra-Fast-Lane-Detection checkout")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda", help="Device to probe")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    from utils.config import Config  # noqa: WPS433
    from model.model import parsingNet  # noqa: WPS433

    culane_cfg = Config.fromfile(repo_root / "configs" / "culane.py")
    tusimple_cfg = Config.fromfile(repo_root / "configs" / "tusimple.py")
    print("culane_dataset", culane_cfg.dataset)
    print("tusimple_dataset", tusimple_cfg.dataset)

    if args.device == "cuda":
        if not torch.cuda.is_available():
            print("CUDA is not available in this environment")
            return 3
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")

    cls_dim = (101, 56, 4)
    net = parsingNet(pretrained=False, backbone="18", cls_dim=cls_dim, use_aux=False).to(device).eval()
    with torch.no_grad():
        out = net(torch.zeros(1, 3, 288, 800, device=device))
    print("output_shape", tuple(out.shape))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
