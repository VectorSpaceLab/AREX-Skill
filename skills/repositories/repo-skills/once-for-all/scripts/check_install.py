#!/usr/bin/env python3
"""Smoke-check the installed Once-for-All package.

Purpose: verify that the core OFA APIs import, a supernet can be built, and an
optional CUDA smoke passes when requested.

Safe by default: no training, no dataset downloads, and no public-weight fetches.
A specialized-model load may still resolve small public config files.

Examples:
  python scripts/check_install.py
  python scripts/check_install.py --device cuda --cuda-smoke
  python scripts/check_install.py --specialized-id flops@389M_top1@79.1_finetune@75
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


def _pick_device(requested: str) -> str:
    if requested == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    return requested


def _maybe_add_repo_root(repo_root: str) -> None:
    if repo_root:
        sys.path.insert(0, str(Path(repo_root).resolve()))


def _run_forward(net: torch.nn.Module, device: str, image_size: int) -> None:
    net = net.to(device)
    x = torch.zeros(1, 3, image_size, image_size, device=device)
    with torch.no_grad():
        y = net(x)
    print(f"forward_ok shape={tuple(y.shape)} device={device}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default="", help="Optional local checkout root for import fallback.")
    parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--net-id", default="ofa_resnet50")
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument(
        "--sample-subnet",
        action="store_true",
        help="Sample an active subnet before the forward smoke when supported.",
    )
    parser.add_argument(
        "--specialized-id",
        default="",
        help="Optional specialized-model id to load for an extra smoke.",
    )
    parser.add_argument(
        "--pretrained",
        action="store_true",
        help="Allow public weight/config downloads for the chosen model ids.",
    )
    parser.add_argument(
        "--cuda-smoke",
        action="store_true",
        help="If CUDA is available, allocate a tiny tensor on the first GPU.",
    )
    args = parser.parse_args()

    _maybe_add_repo_root(args.repo_root)
    device = _pick_device(args.device)

    from ofa.model_zoo import ofa_net, ofa_specialized
    from ofa.tutorial import AccuracyPredictor

    supernet = ofa_net(args.net_id, pretrained=args.pretrained)
    if args.sample_subnet and hasattr(supernet, "sample_active_subnet"):
        supernet.sample_active_subnet()
        supernet = supernet.get_active_subnet(preserve_weight=True)
        print("sampled_subnet_ok")
    _run_forward(supernet, device, args.image_size)

    predictor = AccuracyPredictor(pretrained=False, device="cpu")
    print(f"accuracy_predictor_ok model={type(predictor.model).__name__}")

    if args.specialized_id:
        specialized_net, specialized_image_size = ofa_specialized(
            args.specialized_id, pretrained=args.pretrained
        )
        _run_forward(specialized_net, device, specialized_image_size)
        print(f"specialized_ok image_size={specialized_image_size}")

    if args.cuda_smoke and torch.cuda.is_available():
        x = torch.empty(1, device="cuda")
        print(f"cuda_ok device={torch.cuda.get_device_name(0)} tensor={x.device}")

    print(f"device={device}")
    print("install_smoke_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
