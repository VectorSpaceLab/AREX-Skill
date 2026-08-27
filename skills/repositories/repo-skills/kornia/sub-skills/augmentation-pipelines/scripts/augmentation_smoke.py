#!/usr/bin/env python3
"""Tiny no-download Kornia augmentation smoke test.

This script exercises a deterministic image/mask augmentation pipeline, checks
that the image and mask stay synchronized, and confirms that a transform matrix
is exposed for a rigid geometric augmentation.
"""

from __future__ import annotations

import argparse
import sys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device to use. 'auto' selects CUDA when available, otherwise CPU.",
    )
    return parser.parse_args()


def _select_device(torch, requested: str):
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested, but torch.cuda.is_available() is False")
    return torch.device(requested)


def main() -> int:
    args = _parse_args()
    try:
        import torch
        import kornia.augmentation as K
    except Exception as exc:  # pragma: no cover - diagnostic path for broken runtimes
        print(f"Failed to import torch/kornia augmentation APIs: {exc}", file=sys.stderr)
        return 2

    device = _select_device(torch, args.device)

    # Tiny float image in [0, 1] with a non-square shape so H/W swaps are visible.
    image = torch.tensor(
        [[[[0.00, 0.10, 0.20, 0.30], [0.40, 0.50, 0.60, 0.70], [0.80, 0.90, 1.00, 0.95]]]],
        device=device,
        dtype=torch.float32,
    )
    mask = torch.tensor(
        [[[[0.0, 1.0, 0.0, 1.0], [1.0, 0.0, 1.0, 0.0], [0.0, 0.0, 1.0, 1.0]]]],
        device=device,
        dtype=torch.float32,
    )

    aug = K.AugmentationSequential(
        K.RandomHorizontalFlip(p=1.0),
        data_keys=["input", "mask"],
        same_on_batch=True,
        keepdim=True,
        transformation_matrix_mode="rigid",
    ).to(device)

    image_out, mask_out = aug(image, mask)

    expected_image = torch.flip(image, dims=(-1,))
    expected_mask = torch.flip(mask, dims=(-1,))

    assert image_out.shape == image.shape
    assert mask_out.shape == mask.shape
    assert aug.transform_matrix is not None
    assert aug.transform_matrix.shape == (1, 3, 3)
    torch.testing.assert_close(image_out, expected_image)
    torch.testing.assert_close(mask_out, expected_mask)

    print("augmentation-smoke-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
