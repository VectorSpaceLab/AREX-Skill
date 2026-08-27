#!/usr/bin/env python3
"""Validate a bounded image/segmentation NumPy case without importing MDT."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def load_array(path: Path, key: str | None = None) -> np.ndarray:
    if path.suffix == ".npy":
        return np.load(path, allow_pickle=False)
    if path.suffix == ".npz":
        with np.load(path, allow_pickle=False) as z:
            if key:
                if key not in z.files:
                    raise ValueError(f"missing key {key!r}; available keys: {z.files}")
                return z[key]
            if len(z.files) != 1:
                raise ValueError("an .npz with multiple arrays requires --image-key/--seg-key")
            return z[z.files[0]]
    raise ValueError("array path must end in .npy or .npz")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image", type=Path, required=True)
    p.add_argument("--segmentation", type=Path, required=True)
    p.add_argument("--image-key")
    p.add_argument("--seg-key")
    p.add_argument("--metadata", type=Path)
    p.add_argument("--max-voxels", type=int, default=4_000_000)
    args = p.parse_args()
    image = load_array(args.image, args.image_key)
    seg = load_array(args.segmentation, args.seg_key)
    errors: list[str] = []
    if image.size > args.max_voxels or seg.size > args.max_voxels:
        errors.append("array exceeds max voxel bound")
    if image.shape != seg.shape:
        errors.append(f"shape mismatch: image={image.shape}, segmentation={seg.shape}")
    if image.ndim not in (2, 3, 4):
        errors.append(f"expected 2D/3D or channel-first array, got ndim={image.ndim}")
    if not np.isfinite(image).all():
        errors.append("image contains NaN or infinite values")
    if not np.issubdtype(seg.dtype, np.integer):
        errors.append(f"segmentation must be integer-valued, got {seg.dtype}")
    elif np.min(seg, initial=0) < 0:
        errors.append("segmentation contains negative labels")
    metadata = None
    if args.metadata:
        metadata = json.loads(args.metadata.read_text())
        if not isinstance(metadata, dict):
            errors.append("metadata JSON must be an object")
        else:
            spacing = metadata.get("spacing")
            if spacing is not None and (not isinstance(spacing, list) or len(spacing) not in (2, 3) or not all(isinstance(x, (int, float)) and np.isfinite(x) and x > 0 for x in spacing)):
                errors.append("spacing must contain 2 or 3 positive finite numbers")
            class_target = metadata.get("class_target")
            if class_target is not None and (not isinstance(class_target, list) or not all(isinstance(x, (int, float)) and np.isfinite(x) for x in class_target)):
                errors.append("class_target must be a finite JSON list")
            fg_slices = metadata.get("fg_slices")
            if fg_slices is not None:
                z_size = seg.shape[-1]
                if not isinstance(fg_slices, list) or not all(isinstance(x, int) and 0 <= x < z_size for x in fg_slices):
                    errors.append(f"fg_slices must contain integer indices in [0, {z_size})")
    result = {"valid": not errors, "image_shape": list(image.shape), "image_dtype": str(image.dtype), "segmentation_dtype": str(seg.dtype), "errors": errors}
    if metadata is not None:
        result["metadata_keys"] = sorted(metadata)
    print(json.dumps(result, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
