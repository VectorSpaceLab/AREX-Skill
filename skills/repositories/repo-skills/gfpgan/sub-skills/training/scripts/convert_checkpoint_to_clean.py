#!/usr/bin/env python3
"""Convert a GFPGAN bilinear/original checkpoint into clean-model key scaling.

This is a parameterized adaptation of GFPGAN's conversion utility. It expects a
checkpoint with a state dict under --param-key (default: params_ema), creates a
GFPGANv1Clean target state dict, applies the conversion mapping, and saves a new
checkpoint with params_ema.

Example:
    python scripts/convert_checkpoint_to_clean.py --ori-path source.pth --save-path clean.pth
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Dict

import torch
from gfpgan.archs.gfpganv1_clean_arch import GFPGANv1Clean


def modify_checkpoint(checkpoint_bilinear: Dict[str, torch.Tensor], checkpoint_clean: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
    for ori_k, ori_v in checkpoint_bilinear.items():
        if "stylegan_decoder" in ori_k:
            if "style_mlp" in ori_k:
                lr_mul = 0.01
                prefix, name, idx, var = ori_k.split(".")
                idx = (int(idx) * 2) - 1
                crt_k = f"{prefix}.{name}.{idx}.{var}"
                if var == "weight":
                    _, c_in = ori_v.size()
                    scale = (1 / math.sqrt(c_in)) * lr_mul
                    crt_v = ori_v * scale * 2**0.5
                else:
                    crt_v = ori_v * lr_mul * 2**0.5
                checkpoint_clean[crt_k] = crt_v
            elif "modulation" in ori_k:
                lr_mul = 1
                crt_k = ori_k
                var = ori_k.split(".")[-1]
                if var == "weight":
                    _, c_in = ori_v.size()
                    scale = (1 / math.sqrt(c_in)) * lr_mul
                    crt_v = ori_v * scale
                else:
                    crt_v = ori_v * lr_mul
                checkpoint_clean[crt_k] = crt_v
            elif "style_conv" in ori_k:
                if "activate" in ori_k:
                    split_rlt = ori_k.split(".")
                    if len(split_rlt) == 4:
                        prefix, name, _, var = split_rlt
                        crt_k = f"{prefix}.{name}.{var}"
                    elif len(split_rlt) == 5:
                        prefix, name, idx, _, var = split_rlt
                        crt_k = f"{prefix}.{name}.{idx}.{var}"
                    else:
                        continue
                    crt_v = ori_v * 2**0.5
                    c = crt_v.size(0)
                    checkpoint_clean[crt_k] = crt_v.view(1, c, 1, 1)
                elif "modulated_conv" in ori_k:
                    _, _c_out, c_in, k1, k2 = ori_v.size()
                    scale = 1 / math.sqrt(c_in * k1 * k2)
                    checkpoint_clean[ori_k] = ori_v * scale
                elif "weight" in ori_k:
                    checkpoint_clean[ori_k] = ori_v * 2**0.5
            elif "to_rgb" in ori_k:
                if "modulated_conv" in ori_k:
                    _, _c_out, c_in, k1, k2 = ori_v.size()
                    scale = 1 / math.sqrt(c_in * k1 * k2)
                    checkpoint_clean[ori_k] = ori_v * scale
                else:
                    checkpoint_clean[ori_k] = ori_v
            else:
                checkpoint_clean[ori_k] = ori_v
        elif "conv_body_first" in ori_k or "final_conv" in ori_k:
            name, _, var = ori_k.split(".")
            crt_k = f"{name}.{var}"
            if var == "weight":
                c_out, c_in, k1, k2 = ori_v.size()
                scale = 1 / math.sqrt(c_in * k1 * k2)
                checkpoint_clean[crt_k] = ori_v * scale * 2**0.5
            else:
                checkpoint_clean[crt_k] = ori_v * 2**0.5
        elif "conv_body" in ori_k:
            key = ori_k
            if "conv_body_up" in key:
                key = key.replace("conv2.weight", "conv2.1.weight")
                key = key.replace("skip.weight", "skip.1.weight")
            name1, idx1, name2, _, var = key.split(".")
            crt_k = f"{name1}.{idx1}.{name2}.{var}"
            if name2 == "skip":
                c_out, c_in, k1, k2 = ori_v.size()
                scale = 1 / math.sqrt(c_in * k1 * k2)
                checkpoint_clean[crt_k] = ori_v * scale / 2**0.5
            else:
                if var == "weight":
                    c_out, c_in, k1, k2 = ori_v.size()
                    scale = 1 / math.sqrt(c_in * k1 * k2)
                    checkpoint_clean[crt_k] = ori_v * scale
                else:
                    checkpoint_clean[crt_k] = ori_v
                if "conv1" in key:
                    checkpoint_clean[crt_k] *= 2**0.5
        elif "toRGB" in ori_k:
            if "weight" in ori_k:
                c_out, c_in, k1, k2 = ori_v.size()
                scale = 1 / math.sqrt(c_in * k1 * k2)
                checkpoint_clean[ori_k] = ori_v * scale
            else:
                checkpoint_clean[ori_k] = ori_v
        elif "final_linear" in ori_k:
            if "weight" in ori_k:
                _, c_in = ori_v.size()
                scale = 1 / math.sqrt(c_in)
                checkpoint_clean[ori_k] = ori_v * scale
            else:
                checkpoint_clean[ori_k] = ori_v
        elif "condition" in ori_k:
            if "0.weight" in ori_k:
                c_out, c_in, k1, k2 = ori_v.size()
                scale = 1 / math.sqrt(c_in * k1 * k2)
                checkpoint_clean[ori_k] = ori_v * scale * 2**0.5
            elif "0.bias" in ori_k:
                checkpoint_clean[ori_k] = ori_v * 2**0.5
            elif "2.weight" in ori_k:
                c_out, c_in, k1, k2 = ori_v.size()
                scale = 1 / math.sqrt(c_in * k1 * k2)
                checkpoint_clean[ori_k] = ori_v * scale
            elif "2.bias" in ori_k:
                checkpoint_clean[ori_k] = ori_v
    return checkpoint_clean


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert a GFPGAN bilinear/original checkpoint to clean GFPGANv1Clean format.")
    parser.add_argument("--ori-path", required=True, help="Source checkpoint path.")
    parser.add_argument("--save-path", required=True, help="Output checkpoint path.")
    parser.add_argument("--param-key", default="params_ema", help="Top-level checkpoint key containing weights; use params for non-EMA checkpoints.")
    parser.add_argument("--narrow", type=float, default=1.0, help="GFPGANv1Clean narrow value used to build target state dict.")
    parser.add_argument("--channel-multiplier", type=float, default=2.0, help="GFPGANv1Clean channel multiplier.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src = Path(args.ori_path)
    if not src.is_file():
        print(f"Source checkpoint not found: {src}", file=sys.stderr)
        return 2
    checkpoint = torch.load(str(src), map_location="cpu")
    if isinstance(checkpoint, dict) and args.param_key in checkpoint:
        ori_state = checkpoint[args.param_key]
    elif isinstance(checkpoint, dict) and all(isinstance(k, str) for k in checkpoint.keys()):
        ori_state = checkpoint
    else:
        print(f"Could not find state dict under key {args.param_key!r} in {src}", file=sys.stderr)
        return 2

    net = GFPGANv1Clean(
        512,
        num_style_feat=512,
        channel_multiplier=args.channel_multiplier,
        decoder_load_path=None,
        fix_decoder=False,
        num_mlp=8,
        input_is_latent=True,
        different_w=True,
        narrow=args.narrow,
        sft_half=True,
    )
    clean_state = modify_checkpoint(ori_state, net.state_dict())
    save_path = Path(args.save_path)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"params_ema": clean_state}, str(save_path), _use_new_zipfile_serialization=False)
    print(f"Saved clean checkpoint to {save_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
