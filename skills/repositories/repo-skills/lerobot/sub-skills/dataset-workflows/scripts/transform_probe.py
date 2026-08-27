#!/usr/bin/env python3
"""Run a bounded synthetic image-transform contract probe without dataset I/O."""
from __future__ import annotations

import argparse
import json
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply LeRobot's configured image transforms to a synthetic CHW image and report the contract."
    )
    parser.add_argument("--height", type=int, default=32, help="Synthetic image height")
    parser.add_argument("--width", type=int, default=48, help="Synthetic image width")
    parser.add_argument("--channels", type=int, default=3, help="Synthetic image channels")
    parser.add_argument("--max-num-transforms", type=int, default=1, help="Maximum sampled transforms")
    parser.add_argument("--disable", action="store_true", help="Probe disabled-transform behavior")
    parser.add_argument("--seed", type=int, default=0, help="Torch random seed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if min(args.height, args.width, args.channels) <= 0:
        print("ERROR: dimensions must be positive", file=sys.stderr)
        return 2
    if args.max_num_transforms < 0:
        print("ERROR: --max-num-transforms cannot be negative", file=sys.stderr)
        return 2
    try:
        import torch
        from lerobot.transforms import ImageTransforms, ImageTransformsConfig
    except Exception as exc:
        print(f"IMPORT_STATUS: transform API unavailable: {type(exc).__name__}: {exc}")
        return 1

    torch.manual_seed(args.seed)
    image = torch.linspace(
        0.0,
        1.0,
        steps=args.channels * args.height * args.width,
        dtype=torch.float32,
    ).reshape(args.channels, args.height, args.width)
    config = ImageTransformsConfig(
        enable=not args.disable,
        max_num_transforms=args.max_num_transforms,
        random_order=False,
    )
    try:
        transform = ImageTransforms(config)
        output = transform(image)
    except Exception as exc:
        print(f"PROBE_STATUS: failed: {type(exc).__name__}: {exc}")
        return 1

    result = {
        "enabled": config.enable,
        "configured_max_num_transforms": config.max_num_transforms,
        "input": {"shape": list(image.shape), "dtype": str(image.dtype), "min": float(image.min()), "max": float(image.max())},
        "output": {"shape": list(output.shape), "dtype": str(output.dtype), "min": float(output.min()), "max": float(output.max())},
        "shape_preserved": tuple(output.shape) == tuple(image.shape),
        "finite": bool(torch.isfinite(output).all()),
        "range_approximately_0_1": bool(float(output.min()) >= -1e-5 and float(output.max()) <= 1.00001),
    }
    print(json.dumps(result, indent=2))
    if not result["shape_preserved"] or not result["finite"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
