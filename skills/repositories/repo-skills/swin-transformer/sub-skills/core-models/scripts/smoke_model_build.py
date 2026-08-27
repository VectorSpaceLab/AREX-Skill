#!/usr/bin/env python3
"""Build a tiny Swin model on CPU and optionally run a minimal forward pass.

Example:
  python smoke_model_build.py --repo-root /path/to/Swin-Transformer \
      --cfg configs/swin/swin_tiny_patch4_window7_224.yaml --tiny-forward
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import torch


def apply_repo_root(repo_root: Path) -> None:
    root = repo_root.resolve()
    if not root.exists():
        raise SystemExit(f"repo root does not exist: {root}")
    sys.path.insert(0, str(root))
    os.environ.setdefault("LOCAL_RANK", "0")


def parse_overrides(items: list[str]) -> list[str]:
    if len(items) % 2:
        raise SystemExit("--override must be provided as KEY VALUE pairs")
    return items


def build_config(repo_root: Path, cfg: Path, overrides: list[str]):
    cfg_path = cfg if cfg.is_absolute() else repo_root.resolve() / cfg
    from config import get_config

    class Args:
        batch_size = None
        data_path = None
        zip = False
        cache_mode = None
        pretrained = None
        resume = None
        accumulation_steps = None
        use_checkpoint = False
        disable_amp = False
        amp_opt_level = None
        output = "output"
        tag = "smoke"
        eval = False
        throughput = False
        fused_window_process = False
        fused_layernorm = False
        optim = None
        enable_amp = False
        local_rank = 0

    args = Args()
    args.cfg = str(cfg_path)
    args.opts = overrides or None
    return get_config(args)


def main() -> int:
    ap = argparse.ArgumentParser(description="Smoke-build a tiny Swin model on CPU.")
    ap.add_argument("--repo-root", type=Path, required=True, help="Checkout root to add to sys.path.")
    ap.add_argument("--cfg", type=Path, required=True, help="Config YAML to use.")
    ap.add_argument("--override", nargs="*", default=[], help="Additional KEY VALUE overrides.")
    ap.add_argument("--tiny-forward", action="store_true", help="Run one tiny CPU forward pass.")
    ap.add_argument("--input-size", type=int, default=32, help="Input image size for the tiny forward path.")
    args = ap.parse_args()

    apply_repo_root(args.repo_root)
    overrides = parse_overrides(args.override)
    cfg = build_config(args.repo_root, args.cfg, overrides)

    from models import build_model

    model = build_model(cfg)
    model.eval()
    params = sum(p.numel() for p in model.parameters())
    print(f"model={cfg.MODEL.TYPE}/{cfg.MODEL.NAME}")
    print(f"params={params}")

    if args.tiny_forward:
        with torch.no_grad():
            x = torch.randn(1, 3, args.input_size, args.input_size)
            y = model(x)
        print(f"forward_shape={tuple(y.shape)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
