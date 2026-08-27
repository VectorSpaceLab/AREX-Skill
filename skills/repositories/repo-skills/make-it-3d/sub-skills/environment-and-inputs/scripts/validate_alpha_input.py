#!/usr/bin/env python3
"""Validate a Make-It-3D reference image alpha channel."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from PIL import Image


def inspect_image(path: Path) -> Dict[str, Any]:
    img = Image.open(path)
    arr = np.array(img)
    result: Dict[str, Any] = {
        "path_name": path.name,
        "mode": img.mode,
        "size": list(img.size),
        "has_alpha": False,
        "alpha_min": None,
        "alpha_max": None,
        "foreground_fraction": None,
        "warnings": [],
    }
    if img.mode in {"RGBA", "LA"} or (arr.ndim == 3 and arr.shape[-1] == 4):
        alpha = arr[..., -1].astype(np.float32)
        result["has_alpha"] = True
        result["alpha_min"] = float(alpha.min())
        result["alpha_max"] = float(alpha.max())
        result["foreground_fraction"] = float((alpha > 0).mean())
        if result["alpha_max"] == result["alpha_min"]:
            result["warnings"].append("alpha channel is constant; foreground/background separation may be unusable")
        if result["foreground_fraction"] < 0.01:
            result["warnings"].append("foreground alpha coverage is below 1%; mask may be empty")
        if result["foreground_fraction"] > 0.98:
            result["warnings"].append("foreground alpha coverage is above 98%; background may not be transparent")
    else:
        result["warnings"].append("image has no alpha channel; Make-It-3D main.py expects BGRA/RGBA input")
    w, h = img.size
    if min(w, h) < 128:
        result["warnings"].append("image is very small; source resizes to 512x512 and may amplify artifacts")
    if abs(w - h) / max(w, h) > 0.25:
        result["warnings"].append("image is far from square; consider centering/cropping the object before training")
    return result


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check that a reference image matches Make-It-3D alpha-image assumptions")
    parser.add_argument("--image", type=Path, required=True, help="Reference image to inspect, preferably RGBA PNG")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when alpha is missing or likely unusable")
    args = parser.parse_args(argv)
    if not args.image.exists():
        raise SystemExit(f"image does not exist: {args.image}")
    result = inspect_image(args.image)
    hard_fail = (not result["has_alpha"]) or result["alpha_min"] == result["alpha_max"]
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Make-It-3D alpha input check")
        print(f"File: {args.image}")
        print(f"Mode: {result['mode']}  Size: {result['size'][0]}x{result['size'][1]}")
        print(f"Has alpha: {result['has_alpha']}")
        if result["has_alpha"]:
            print(f"Alpha min/max: {result['alpha_min']:.1f}/{result['alpha_max']:.1f}")
            print(f"Foreground fraction (alpha > 0): {result['foreground_fraction']:.4f}")
        if result["warnings"]:
            print("Warnings:")
            for warning in result["warnings"]:
                print(f"  - {warning}")
    return 1 if args.strict and hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
