#!/usr/bin/env python3
"""Rename BlendMask checkpoint keys from centerness to ctrness."""

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

import torch


def rename_keys(state):
    converted = OrderedDict()
    for key, value in state.items():
        converted[key.replace("centerness", "ctrness")] = value
    return converted


def parse_args():
    parser = argparse.ArgumentParser(description="Rename BlendMask centerness keys")
    parser.add_argument("--model", required=True, help="Input checkpoint path")
    parser.add_argument("--output", required=True, help="Output checkpoint path")
    parser.add_argument("--state-dict-key", default="model", help="Top-level state dict key if present")
    parser.add_argument("--save-model-only", action="store_true", help="Save only renamed state dict")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src = Path(args.model)
    dst = Path(args.output)
    if not src.exists():
        raise SystemExit(f"input checkpoint does not exist: {src}")
    ckpt = torch.load(str(src), map_location="cpu")
    if isinstance(ckpt, dict) and args.state_dict_key in ckpt:
        converted = rename_keys(ckpt[args.state_dict_key])
        obj = converted if args.save_model_only else {**ckpt, args.state_dict_key: converted}
    else:
        converted = rename_keys(ckpt)
        obj = converted
    dst.parent.mkdir(parents=True, exist_ok=True)
    torch.save(obj, str(dst))
    print(f"renamed {len(converted)} tensors -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
