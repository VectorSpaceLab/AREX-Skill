#!/usr/bin/env python3
"""Safely concatenate a head and two wrist images into a T-shaped view."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import cv2
import numpy as np


def resize_and_concatenate_frames(
    head_img: np.ndarray,
    left_img: np.ndarray,
    right_img: np.ndarray,
) -> np.ndarray:
    """Return ``head`` above half-sized left/right wrist images.

    The result has height ``head_height + head_height // 2`` and width
    ``head_width``. All images must be non-empty HWC arrays with the same
    channel count; wrist inputs are resized to the head half-size.
    """
    if any(not isinstance(x, np.ndarray) or x.ndim != 3 for x in (head_img, left_img, right_img)):
        raise ValueError("head, left, and right images must be non-empty HWC arrays")
    if any(x.shape[2] != head_img.shape[2] for x in (left_img, right_img)):
        raise ValueError("all camera images must have the same channel count")
    h, w, _ = head_img.shape
    if h < 2 or w < 2 or any(x.shape[0] < 1 or x.shape[1] < 1 for x in (left_img, right_img)):
        raise ValueError("camera images must have positive dimensions and head must be at least 2x2")
    wrist_size = (w // 2, h // 2)
    left = cv2.resize(left_img, wrist_size, interpolation=cv2.INTER_AREA)
    right = cv2.resize(right_img, wrist_size, interpolation=cv2.INTER_AREA)
    return np.vstack((head_img, np.hstack((left, right))))


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--head", required=True, help="head image path")
    p.add_argument("--left", required=True, help="left wrist image path")
    p.add_argument("--right", required=True, help="right wrist image path")
    p.add_argument("--output", required=True, help="output image path")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = _parser().parse_args(argv)
    images = [cv2.imread(str(Path(p)), cv2.IMREAD_UNCHANGED) for p in (args.head, args.left, args.right)]
    if any(image is None for image in images):
        raise FileNotFoundError("one or more input images could not be read")
    result = resize_and_concatenate_frames(*images)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), result):
        raise OSError(f"failed to write {output}")
    print(f"wrote {output} with shape {result.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
