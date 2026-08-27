#!/usr/bin/env python3
"""Validate common token-to-spatial reshape layouts with synthetic tensors."""

from __future__ import annotations

import argparse

import torch

from pytorch_grad_cam.utils.reshape_transforms import swinT_reshape_transform, vit_reshape_transform


def main() -> int:
    parser = argparse.ArgumentParser(description="Check ViT/Swin reshape transform tensor layouts.")
    parser.add_argument("--kind", choices=["vit", "swin"], default="vit")
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--channels", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()

    if args.kind == "vit":
        height = args.height or 4
        width = args.width or 4
        tokens = height * width + 1
        tensor = torch.randn(args.batch_size, tokens, args.channels)
        result = vit_reshape_transform(tensor, height=height, width=width)
    else:
        height = args.height or 4
        width = args.width or 4
        tokens = height * width
        tensor = torch.randn(args.batch_size, tokens, args.channels)
        result = swinT_reshape_transform(tensor, height=height, width=width)

    expected = (args.batch_size, args.channels, height, width)
    assert tuple(result.shape) == expected, (result.shape, expected)
    print(f"OK {args.kind}: input={tuple(tensor.shape)} output={tuple(result.shape)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
