#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json


def make_spatial_plan(height: int, width: int, factor: int, steps: int, conditioning_height: int | None = None, conditioning_width: int | None = None) -> dict:
    errors = []
    warnings = []
    if height <= 0 or width <= 0:
        errors.append("image dimensions must be positive")
    if factor <= 0:
        errors.append("factor must be positive")
    if steps <= 0:
        errors.append("sampler steps must be positive")
    elif steps > 50:
        warnings.append("sampler steps exceed bounded recovery recommendation")
    divisible = factor > 0 and height % factor == 0 and width % factor == 0
    if factor > 0 and not divisible:
        errors.append("image dimensions must be divisible by factor")
    latent_height = height // factor if divisible else None
    latent_width = width // factor if divisible else None
    conditioning_alignment = "not_provided"
    if conditioning_height is not None or conditioning_width is not None:
        if conditioning_height is None or conditioning_width is None:
            errors.append("conditioning height and width must be provided together")
        elif conditioning_height == height and conditioning_width == width:
            conditioning_alignment = "image_space"
        elif latent_height is not None and conditioning_height == latent_height and conditioning_width == latent_width:
            conditioning_alignment = "latent_space"
        else:
            conditioning_alignment = "mismatched"
            errors.append("conditioning shape does not align with image or latent grid")
    return {
        "ok": not errors,
        "image_shape": [height, width],
        "factor": factor,
        "latent_grid": [latent_height, latent_width] if latent_height is not None else None,
        "sampler_steps": steps,
        "conditioning_alignment": conditioning_alignment,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--height", type=int, required=True)
    parser.add_argument("--width", type=int, required=True)
    parser.add_argument("--factor", type=int, required=True)
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--conditioning-height", type=int)
    parser.add_argument("--conditioning-width", type=int)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = make_spatial_plan(args.height, args.width, args.factor, args.steps, args.conditioning_height, args.conditioning_width)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
