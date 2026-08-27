#!/usr/bin/env python3
"""Validate AnyDoor inference inputs before running a generation command."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if image is None:
        raise ValueError(f"could not read image: {path}")
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    return image


def load_mask_from_path(path: Path) -> np.ndarray:
    mask = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    if mask is None:
        raise ValueError(f"could not read mask: {path}")
    if mask.ndim == 3:
        mask = mask[:, :, 0]
    return (mask > 128).astype(np.uint8)


def mask_from_image_alpha(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] < 4:
        raise ValueError("reference image has no alpha channel")
    return (image[:, :, 3] > 128).astype(np.uint8)


def bbox_from_mask(mask: np.ndarray) -> tuple[int, int, int, int]:
    if mask.sum() == 0:
        raise ValueError("mask is empty")
    rows = np.any(mask > 0, axis=1)
    cols = np.any(mask > 0, axis=0)
    y_idx = np.where(rows)[0]
    x_idx = np.where(cols)[0]
    return int(y_idx[0]), int(y_idx[-1]), int(x_idx[0]), int(x_idx[-1])


def validate_pair(image: np.ndarray, mask: np.ndarray, label: str) -> list[str]:
    notes: list[str] = []
    if image.shape[:2] != mask.shape[:2]:
        raise ValueError(f"{label} image/mask size mismatch: {image.shape[:2]} vs {mask.shape[:2]}")
    if mask.sum() == 0:
        raise ValueError(f"{label} mask is empty")
    unique = set(np.unique(mask).tolist())
    if not unique.issubset({0, 1}):
        notes.append(f"{label} mask was thresholded to binary")
    notes.append(f"{label} bbox={bbox_from_mask(mask)}")
    return notes


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    report: dict[str, Any] = {"status": "ok", "notes": [], "shapes": {}}

    ref_image = load_image(args.reference_image)
    if args.reference_mask is not None:
        ref_mask = load_mask_from_path(args.reference_mask)
    else:
        ref_mask = mask_from_image_alpha(ref_image)
        ref_image = ref_image[:, :, :3]
        report["notes"].append("reference mask derived from alpha channel")

    tgt_image = load_image(args.target_image)
    if args.target_mask is None:
        raise ValueError("target mask is required")
    tgt_mask = load_mask_from_path(args.target_mask)

    report["shapes"]["reference_image"] = list(ref_image.shape)
    report["shapes"]["reference_mask"] = list(ref_mask.shape)
    report["shapes"]["target_image"] = list(tgt_image.shape)
    report["shapes"]["target_mask"] = list(tgt_mask.shape)

    report["notes"].extend(validate_pair(ref_image[:, :, :3], ref_mask, "reference"))
    report["notes"].extend(validate_pair(tgt_image[:, :, :3], tgt_mask, "target"))

    if ref_mask.sum() < args.min_pixels:
        raise ValueError(f"reference mask too small: {int(ref_mask.sum())} pixels < {args.min_pixels}")
    if tgt_mask.sum() < args.min_pixels:
        raise ValueError(f"target mask too small: {int(tgt_mask.sum())} pixels < {args.min_pixels}")

    report["ref_bbox"] = list(bbox_from_mask(ref_mask))
    report["target_bbox"] = list(bbox_from_mask(tgt_mask))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AnyDoor inference image and mask inputs.")
    parser.add_argument("--reference-image", type=Path, required=True, help="Reference object image path.")
    parser.add_argument("--reference-mask", type=Path, help="Reference binary mask path.")
    parser.add_argument("--target-image", type=Path, required=True, help="Target/background image path.")
    parser.add_argument("--target-mask", type=Path, required=True, help="Target binary mask path.")
    parser.add_argument("--min-pixels", type=int, default=16, help="Minimum mask area in pixels.")
    parser.add_argument("--json", action="store_true", help="Emit JSON report.")
    args = parser.parse_args()

    report = build_report(args)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("AnyDoor input validation OK")
        print(f"reference bbox: {report['ref_bbox']}")
        print(f"target bbox: {report['target_bbox']}")
        for note in report["notes"]:
            print(f"note: {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
