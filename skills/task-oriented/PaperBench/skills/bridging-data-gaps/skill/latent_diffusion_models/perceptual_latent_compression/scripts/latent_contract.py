#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

ALLOWED_REGULARIZATION = {"kl", "vq", "none"}


def validate_latent_contract(height: int, width: int, channels: int, factor: int, latent_channels: int, regularization: str) -> dict:
    errors = []
    warnings = []
    if height <= 0 or width <= 0:
        errors.append("height and width must be positive")
    if channels != 3:
        errors.append("LDM first-stage input contract expects RGB channels=3")
    if factor <= 0:
        errors.append("downsampling factor must be positive")
    elif factor == 1:
        warnings.append("factor=1 is pixel-space diffusion, not latent compression")
    elif factor > 16:
        warnings.append("large compression factors can discard perceptual detail")
    if latent_channels <= 0:
        errors.append("latent_channels must be positive")
    if regularization not in ALLOWED_REGULARIZATION:
        errors.append(f"unsupported regularization: {regularization}")
    if factor > 0 and (height % factor != 0 or width % factor != 0):
        errors.append("height and width must be divisible by factor")
    latent_height = height // factor if factor > 0 and height % factor == 0 else None
    latent_width = width // factor if factor > 0 and width % factor == 0 else None
    input_values = height * width * max(channels, 0)
    latent_values = (latent_height or 0) * (latent_width or 0) * max(latent_channels, 0)
    compression_ratio = input_values / latent_values if latent_values else None
    return {
        "ok": not errors,
        "input_shape": [height, width, channels],
        "factor": factor,
        "latent_shape": [latent_height, latent_width, latent_channels] if latent_height and latent_width and latent_channels > 0 else None,
        "spatial_reduction": factor * factor if factor > 0 else None,
        "compression_ratio": compression_ratio,
        "regularization": regularization,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--channels", type=int, default=3)
    parser.add_argument("--factor", type=int, required=True)
    parser.add_argument("--latent-channels", type=int, default=3)
    parser.add_argument("--regularization", default="none")
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    result = validate_latent_contract(args.height, args.width, args.channels, args.factor, args.latent_channels, args.regularization)
    text = json.dumps(result, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            handle.write(text + "\n")
    print(text)
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
