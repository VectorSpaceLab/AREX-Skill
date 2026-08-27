#!/usr/bin/env python3
"""Safe wrapper around FCOS high-level inference.

By default this script performs a dry run and prints the intended API path. Use
--run to construct the model and execute detection. It never opens a GUI window.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load_image_bgr(path: str):
    suffix = Path(path).suffix.lower()
    if suffix == ".npy":
        arr = np.load(path)
        if arr.ndim != 3 or arr.shape[2] != 3:
            raise ValueError(f"expected HxWx3 array in {path}, got {arr.shape}")
        return arr
    try:
        import cv2  # type: ignore
    except Exception as exc:
        raise RuntimeError("OpenCV is required for non-.npy image inputs; run prepare_image_for_fcos.py first or install opencv-python") from exc
    arr = cv2.imread(path, cv2.IMREAD_COLOR)
    if arr is None:
        raise ValueError(f"could not read image: {path}")
    return arr


def main() -> int:
    parser = argparse.ArgumentParser(description="Construct or run a headless FCOS image inference command")
    parser.add_argument("input_image", help="Local image path or prepared .npy BGR array")
    parser.add_argument("--model-name", default="fcos_syncbn_bs32_c128_MNV2_FPN_1x", help="High-level FCOS model_name")
    parser.add_argument("--nms-thresh", type=float, default=0.6, help="FCOS NMS threshold")
    parser.add_argument("--min-confidence", type=float, default=None, help="Optional uniform detection threshold")
    parser.add_argument("--cpu-only", action="store_true", help="Force CPU device")
    parser.add_argument("--run", action="store_true", help="Actually import FCOS, load weights, and run detection")
    parser.add_argument("--dry-run", action="store_true", help="Print plan only; default when --run is absent")
    args = parser.parse_args()

    plan = {
        "input_image": args.input_image,
        "model_name": args.model_name,
        "nms_thresh": args.nms_thresh,
        "min_confidence": args.min_confidence,
        "cpu_only": args.cpu_only,
        "will_run": bool(args.run),
        "notes": ["No GUI window will be opened", "Model construction may download pretrained weights if not cached"],
    }
    if not args.run:
        print(json.dumps(plan, indent=2, sort_keys=True))
        return 0

    try:
        from fcos import FCOS  # type: ignore
    except Exception as exc:
        raise SystemExit(f"Failed to import fcos.FCOS: {type(exc).__name__}: {exc}")

    image = load_image_bgr(args.input_image)
    detector = FCOS(model_name=args.model_name, nms_thresh=args.nms_thresh, cpu_only=args.cpu_only)
    detections = detector.detect(image, min_confidence=args.min_confidence)
    print(json.dumps(detections, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
