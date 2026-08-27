#!/usr/bin/env python3
"""Export Ultra-Fast-Lane-Detection to TorchScript.

This helper avoids the hardcoded checkpoint and output paths in the source
export demo.

Example:
    python export_torchscript.py --repo-root . --checkpoint ckpt.pth --output lane.pt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a lane model to TorchScript.")
    parser.add_argument("--repo-root", required=True, help="Path to the Ultra-Fast-Lane-Detection checkout")
    parser.add_argument("--checkpoint", required=True, help="Checkpoint file with a model state dict")
    parser.add_argument("--output", required=True, help="Output TorchScript path")
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cuda", help="Export device")
    parser.add_argument("--backbone", default="18", help="Backbone id such as 18 or 50")
    parser.add_argument("--griding-num", type=int, default=200, help="Grid count used in cls_dim")
    parser.add_argument("--cls-num-per-lane", type=int, default=18, help="Class count per lane anchor")
    parser.add_argument("--num-lanes", type=int, default=4, help="Number of lane slots")
    parser.add_argument("--half", action="store_true", help="Export the traced model in half precision on CUDA")
    return parser.parse_args()


def load_state_dict(checkpoint_path: Path) -> dict:
    checkpoint = torch.load(checkpoint_path, map_location="cpu")
    if isinstance(checkpoint, dict) and "model" in checkpoint:
        state_dict = checkpoint["model"]
    else:
        state_dict = checkpoint
    cleaned = {}
    for key, value in state_dict.items():
        cleaned[key[7:] if key.startswith("module.") else key] = value
    return cleaned


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).expanduser().resolve()
    sys.path.insert(0, str(repo_root))

    from model.model import parsingNet  # noqa: WPS433

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA is not available in this environment", file=sys.stderr)
        return 3
    if args.half and args.device != "cuda":
        print("--half is only supported with --device cuda", file=sys.stderr)
        return 4

    device = torch.device(args.device)
    cls_dim = (args.griding_num + 1, args.cls_num_per_lane, args.num_lanes)
    net = parsingNet(pretrained=False, backbone=args.backbone, cls_dim=cls_dim, use_aux=False).to(device)
    net.load_state_dict(load_state_dict(Path(args.checkpoint)), strict=False)
    net.eval()
    if args.half:
        net = net.half()

    example = torch.zeros(1, 3, 288, 800, device=device)
    if args.half:
        example = example.half()

    with torch.no_grad():
        traced = torch.jit.trace(net, example)
        traced(example)
        traced.save(str(Path(args.output).expanduser().resolve()))

    print(f"wrote TorchScript to {Path(args.output).expanduser().resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
