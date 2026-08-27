#!/usr/bin/env python3
"""Save only model weights from an AdelaiDet/Detectron2 checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch


def parse_args():
    parser = argparse.ArgumentParser(description="Strip optimizer/training state from checkpoint")
    parser.add_argument("--input", required=True, help="Input checkpoint path")
    parser.add_argument("--output", required=True, help="Output checkpoint path")
    parser.add_argument("--state-dict-key", default="model", help="Top-level model key to extract")
    parser.add_argument(
        "--wrap-model-key",
        action="store_true",
        help="Save {'model': state} instead of the bare state dict",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src = Path(args.input)
    dst = Path(args.output)
    if not src.exists():
        raise SystemExit(f"input checkpoint does not exist: {src}")
    ckpt = torch.load(str(src), map_location="cpu")
    if not isinstance(ckpt, dict) or args.state_dict_key not in ckpt:
        raise SystemExit(f"checkpoint does not contain key {args.state_dict_key!r}")
    state = ckpt[args.state_dict_key]
    dst.parent.mkdir(parents=True, exist_ok=True)
    torch.save({args.state_dict_key: state} if args.wrap_model_key else state, str(dst))
    print(f"saved model state -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
