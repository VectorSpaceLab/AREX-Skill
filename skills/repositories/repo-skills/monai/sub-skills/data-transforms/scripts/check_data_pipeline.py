#!/usr/bin/env python3
"""Validate a tiny MONAI dictionary transform and data pipeline.

The script is intentionally dependency-light: it uses NumPy arrays by default
and only uses MONAI public APIs. Optionally pass --image-npy/--label-npy to load
small local arrays without requiring medical image reader extras.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a tiny MONAI data/transform pipeline.")
    parser.add_argument("--image-npy", type=Path, default=None, help="Optional .npy image array to use instead of synthetic data.")
    parser.add_argument("--label-npy", type=Path, default=None, help="Optional .npy label array to use instead of synthetic data.")
    parser.add_argument("--spatial-size", type=int, nargs="+", default=[8, 8, 8], help="Synthetic spatial size, usually three integers.")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size for the MONAI DataLoader check.")
    parser.add_argument("--num-workers", type=int, default=0, help="Number of DataLoader workers for the check.")
    parser.add_argument("--json", action="store_true", help="Print a JSON summary instead of human-readable text.")
    return parser.parse_args()


def load_or_create_arrays(args: argparse.Namespace) -> tuple[Any, Any]:
    import numpy as np

    if args.image_npy is not None:
        image = np.load(args.image_npy)
    else:
        spatial_size = tuple(args.spatial_size)
        if len(spatial_size) not in (2, 3):
            raise ValueError("--spatial-size must contain two or three integers")
        image = np.linspace(0.0, 1.0, int(np.prod(spatial_size)), dtype=np.float32).reshape(spatial_size)

    if args.label_npy is not None:
        label = np.load(args.label_npy)
    else:
        label = np.zeros_like(image, dtype=np.int16)
        center = tuple(slice(max(0, dim // 4), max(1, (3 * dim) // 4)) for dim in image.shape)
        label[center] = 1

    if image.shape != label.shape:
        raise ValueError(f"image and label must have matching shape, got {image.shape} and {label.shape}")
    if image.ndim not in (2, 3):
        raise ValueError(f"expected 2D or 3D arrays without channel dimension, got shape {image.shape}")
    return image.astype(np.float32, copy=False), label.astype(np.int16, copy=False)


def build_pipeline() -> Any:
    from monai.transforms import Compose, EnsureChannelFirstd, EnsureTyped, ScaleIntensityd

    return Compose(
        [
            EnsureChannelFirstd(keys=("image", "label"), channel_dim="no_channel"),
            ScaleIntensityd(keys="image"),
            EnsureTyped(keys=("image", "label"), track_meta=True),
        ]
    )


def main() -> int:
    args = parse_args()

    from monai.data import DataLoader, Dataset, MetaTensor, decollate_batch

    image, label = load_or_create_arrays(args)
    item = {"image": image, "label": label, "case_id": "tiny_case"}
    transforms = build_pipeline()
    dataset = Dataset([item], transform=transforms)

    sample = dataset[0]
    if not isinstance(sample["image"], MetaTensor):
        raise AssertionError("expected image to be a MetaTensor after EnsureTyped(track_meta=True)")
    if not isinstance(sample["label"], MetaTensor):
        raise AssertionError("expected label to be a MetaTensor after EnsureTyped(track_meta=True)")
    expected_shape = (1, *image.shape)
    if tuple(sample["image"].shape) != expected_shape:
        raise AssertionError(f"expected channel-first image shape {expected_shape}, got {tuple(sample['image'].shape)}")
    if tuple(sample["label"].shape) != expected_shape:
        raise AssertionError(f"expected channel-first label shape {expected_shape}, got {tuple(sample['label'].shape)}")

    loader = DataLoader(dataset, batch_size=args.batch_size, num_workers=args.num_workers)
    batch = next(iter(loader))
    if tuple(batch["image"].shape)[1:] != expected_shape:
        raise AssertionError(f"unexpected batch image shape {tuple(batch['image'].shape)}")
    cases = decollate_batch(batch)
    if not cases or "image" not in cases[0]:
        raise AssertionError("decollate_batch did not return per-case dictionaries")

    summary = {
        "ok": True,
        "input_shape": list(image.shape),
        "sample_image_shape": list(sample["image"].shape),
        "sample_label_shape": list(sample["label"].shape),
        "batch_image_shape": list(batch["image"].shape),
        "image_type": type(sample["image"]).__name__,
        "label_type": type(sample["label"]).__name__,
        "decollated_cases": len(cases),
        "metadata_keys": sorted(str(key) for key in sample["image"].meta.keys()),
    }

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("MONAI data pipeline check passed")
        print(f"sample image shape: {tuple(sample['image'].shape)} ({type(sample['image']).__name__})")
        print(f"batch image shape: {tuple(batch['image'].shape)}")
        print(f"decollated cases: {len(cases)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
