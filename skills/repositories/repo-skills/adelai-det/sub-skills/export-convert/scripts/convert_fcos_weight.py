#!/usr/bin/env python3
"""Convert official FCOS checkpoint keys to AdelaiDet/Detectron2-style keys."""

from __future__ import annotations

import argparse
from collections import OrderedDict
from pathlib import Path

import torch


def rename_resnet_param_names(ckpt_state_dict):
    converted_state_dict = OrderedDict()
    for key, value in ckpt_state_dict.items():
        key = key.replace("module.", "")
        key = key.replace("body", "bottom_up")
        key = key.replace(".layer1", ".res2")
        key = key.replace(".layer2", ".res3")
        key = key.replace(".layer3", ".res4")
        key = key.replace(".layer4", ".res5")
        key = key.replace("downsample.0", "shortcut")
        key = key.replace("downsample.1", "shortcut.norm")
        key = key.replace("bn1", "conv1.norm")
        key = key.replace("bn2", "conv2.norm")
        key = key.replace("bn3", "conv3.norm")
        key = key.replace("fpn_inner2", "fpn_lateral3")
        key = key.replace("fpn_inner3", "fpn_lateral4")
        key = key.replace("fpn_inner4", "fpn_lateral5")
        key = key.replace("fpn_layer2", "fpn_output3")
        key = key.replace("fpn_layer3", "fpn_output4")
        key = key.replace("fpn_layer4", "fpn_output5")
        key = key.replace("top_blocks", "top_block")
        key = key.replace("fpn.", "")
        key = key.replace("rpn", "proposal_generator")
        key = key.replace("head", "fcos_head")
        converted_state_dict[key] = value
    return converted_state_dict


def parse_args():
    parser = argparse.ArgumentParser(description="Convert official FCOS weight keys")
    parser.add_argument("--model", required=True, help="Input checkpoint path")
    parser.add_argument("--output", required=True, help="Output checkpoint path")
    parser.add_argument("--state-dict-key", default="model", help="Top-level state dict key")
    parser.add_argument("--save-model-only", action="store_true", help="Save only converted state dict")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src = Path(args.model)
    dst = Path(args.output)
    if not src.exists():
        raise SystemExit(f"input checkpoint does not exist: {src}")
    ckpt = torch.load(str(src), map_location="cpu")
    if args.state_dict_key:
        if args.state_dict_key not in ckpt:
            raise SystemExit(f"missing key {args.state_dict_key!r}; available keys: {list(ckpt)[:20]}")
        state = ckpt[args.state_dict_key]
    else:
        state = ckpt
    converted = rename_resnet_param_names(state)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if args.save_model_only or not isinstance(ckpt, dict):
        torch.save(converted, str(dst))
    else:
        ckpt[args.state_dict_key] = converted
        torch.save(ckpt, str(dst))
    print(f"converted {len(converted)} tensors -> {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
