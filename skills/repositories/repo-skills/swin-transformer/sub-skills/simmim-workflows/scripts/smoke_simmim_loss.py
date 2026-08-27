#!/usr/bin/env python3
"""Run a tiny synthetic SimMIM mask/loss smoke on CPU."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import torch


def main() -> int:
    ap = argparse.ArgumentParser(description="Run a tiny CPU SimMIM smoke check.")
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--input-size", type=int, default=32)
    ap.add_argument("--mask-patch-size", type=int, default=16)
    ap.add_argument("--mask-ratio", type=float, default=0.5)
    args = ap.parse_args()
    sys.path.insert(0, str(args.repo_root.resolve()))
    os.environ.setdefault("LOCAL_RANK", "0")
    from data.data_simmim_pt import MaskGenerator
    from models.simmim import norm_targets

    mask_gen = MaskGenerator(args.input_size, args.mask_patch_size, 4, args.mask_ratio)
    mask = torch.tensor(mask_gen(), dtype=torch.float32).unsqueeze(0)
    x = torch.randn(1, 3, args.input_size, args.input_size)
    normalized = norm_targets(x, patch_size=3)
    print(f"mask_shape={tuple(mask.shape)} mask_sum={float(mask.sum())}")
    print(f"normalized_shape={tuple(normalized.shape)}")
    print("SimMIM mask/target smoke passed; this is not a training run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
