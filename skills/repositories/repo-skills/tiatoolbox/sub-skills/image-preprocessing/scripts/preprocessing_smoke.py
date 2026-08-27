#!/usr/bin/env python3
"""Tiny in-memory TIAToolbox preprocessing smoke checks.

The script avoids network access, WSI downloads, source checkout files, and
persistent writes. It exercises maskers, stain normalizer construction, patch
coordinate helpers, and sliding-window extraction on small NumPy arrays.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def make_tissue_like_image(size: int = 64) -> Any:
    """Create a tiny RGB image with a dark tissue-like square on light background."""
    import numpy as np

    image = np.full((size, size, 3), 235, dtype=np.uint8)
    image[16:48, 16:48] = np.array([120, 50, 100], dtype=np.uint8)
    image[24:40, 24:40] = np.array([90, 35, 80], dtype=np.uint8)
    return image


def run_smoke() -> dict[str, Any]:
    """Run safe preprocessing checks and return a JSON-serializable summary."""
    import numpy as np

    from tiatoolbox.tools.patchextraction import (
        PatchExtractor,
        SlidingWindowPatchExtractor,
    )
    from tiatoolbox.tools.stainaugment import StainAugmentor
    from tiatoolbox.tools.stainnorm import get_normalizer
    from tiatoolbox.tools.tissuemask import MorphologicalMasker, OtsuTissueMasker

    image = make_tissue_like_image()
    batch = image[np.newaxis, ...]

    otsu_mask = OtsuTissueMasker().fit_transform(batch)[0]
    morph_mask = MorphologicalMasker(kernel_size=3, min_region_size=4).fit_transform(
        batch,
    )[0]

    if otsu_mask.shape != image.shape[:2] or not np.any(otsu_mask):
        raise AssertionError("OtsuTissueMasker did not produce a non-empty 2D mask")
    if morph_mask.shape != image.shape[:2] or not np.any(morph_mask):
        raise AssertionError("MorphologicalMasker did not produce a non-empty 2D mask")

    normalizer = get_normalizer("reinhard")
    normalizer.fit(image)
    normalized = normalizer.transform(image)
    if normalized.shape != image.shape or normalized.dtype != np.uint8:
        raise AssertionError("Reinhard normalizer returned an unexpected image")

    custom_matrix = np.array(
        [
            [0.65, 0.70, 0.29],
            [0.07, 0.99, 0.11],
        ],
        dtype=float,
    )
    custom_normalizer = get_normalizer("custom", stain_matrix=custom_matrix)
    if custom_normalizer is None:
        raise AssertionError("Custom normalizer was not constructed")

    augmentor = StainAugmentor(method="macenko", stain_matrix=custom_matrix, p=1.0)
    if augmentor.method.lower() != "macenko":
        raise AssertionError("StainAugmentor was not constructed as expected")

    coordinates = PatchExtractor.get_coordinates(
        image_shape=(64, 64),
        patch_input_shape=(16, 16),
        stride_shape=(16, 16),
        input_within_bound=True,
    )
    if coordinates.shape != (16, 4):
        raise AssertionError(f"Unexpected coordinate grid shape: {coordinates.shape}")

    extractor = SlidingWindowPatchExtractor(
        input_img=image,
        patch_size=(16, 16),
        stride=(16, 16),
        input_mask=morph_mask,
        min_mask_ratio=0.05,
        within_bound=True,
    )
    if len(extractor) == 0:
        raise AssertionError("SlidingWindowPatchExtractor selected zero patches")

    first_patch = extractor[0]
    if first_patch.shape != (16, 16, 3):
        raise AssertionError(f"Unexpected patch shape: {first_patch.shape}")

    return {
        "ok": True,
        "otsu_positive_pixels": int(np.count_nonzero(otsu_mask)),
        "morph_positive_pixels": int(np.count_nonzero(morph_mask)),
        "normalizer": type(normalizer).__name__,
        "custom_normalizer": type(custom_normalizer).__name__,
        "stain_augmentor": type(augmentor).__name__,
        "coordinate_count": int(coordinates.shape[0]),
        "sliding_patch_count": int(len(extractor)),
        "first_patch_shape": list(first_patch.shape),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny in-memory TIAToolbox preprocessing smoke checks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the smoke-check summary as JSON.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    summary = run_smoke()
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print("TIAToolbox preprocessing smoke checks passed")
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
