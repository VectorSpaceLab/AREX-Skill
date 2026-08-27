#!/usr/bin/env python3
"""Tiny ANTsPy learning/deeplearn helper smoke check.

This script uses only in-memory images and arrays. It avoids downloads,
repository-path dependencies, neural-network training, GPU work, credentials,
and destructive writes.

Usage:
    python antspy_deeplearn_smoke.py
    python antspy_deeplearn_smoke.py --skip-random-transform
"""

from __future__ import annotations

import argparse
import json
import random
from typing import Any


def _shape_tuple(values: Any) -> tuple[int, ...]:
    return tuple(int(value) for value in values)


def run_smoke(skip_random_transform: bool = False) -> dict:
    import ants
    import numpy as np

    np.random.seed(17)
    random.seed(17)

    base = np.arange(64, dtype="float32").reshape(8, 8) / 63.0
    image = ants.from_numpy(base, spacing=(1.0, 1.25), origin=(0.0, 0.0))
    label_array = np.zeros((8, 8), dtype="int32")
    label_array[2:6, 2:6] = 1
    label_array[3:5, 3:5] = 2
    label = ants.from_numpy(label_array.astype("float32"), spacing=image.spacing, origin=image.origin, direction=image.direction)

    patches = ants.extract_image_patches(
        image,
        patch_size=(4, 4),
        max_number_of_patches="all",
        stride_length=(4, 4),
        return_as_array=True,
    )
    if patches.shape != (4, 4, 4):
        raise RuntimeError(f"unexpected patch array shape: {patches.shape}")

    reconstructed = ants.reconstruct_image_from_patches(patches, image, stride_length=(4, 4))
    if reconstructed.shape != image.shape:
        raise RuntimeError(f"unexpected reconstructed shape: {reconstructed.shape}")

    one_hot = ants.segmentation_to_one_hot(label_array, segmentation_labels=[0, 1, 2])
    if one_hot.shape != (8, 8, 3):
        raise RuntimeError(f"unexpected one-hot shape: {one_hot.shape}")
    probability_images = ants.one_hot_to_segmentation(one_hot, label)
    if len(probability_images) != 3:
        raise RuntimeError("expected one probability image per label")

    one_hot_cf = ants.segmentation_to_one_hot(
        label_array,
        segmentation_labels=[0, 1, 2],
        channel_first_ordering=True,
    )
    if one_hot_cf.shape != (3, 8, 8):
        raise RuntimeError(f"unexpected channel-first one-hot shape: {one_hot_cf.shape}")

    cropped = ants.crop_image_center(image, (6, 6))
    padded = ants.pad_or_crop_image_to_size(cropped, (8, 8))
    factor_padded = ants.pad_image_by_factor(cropped, 4)

    warped = ants.histogram_warp_image_intensities(
        image,
        break_points=(0.25, 0.5, 0.75),
        displacements=(0.01, -0.02, 0.01),
        clamp_end_points=(True, True),
        transform_domain_size=8,
    )
    bias_log = ants.simulate_bias_field(
        image,
        number_of_points=4,
        sd_bias_field=0.1,
        number_of_fitting_levels=1,
        mesh_size=2,
    )
    biased = image * ants.from_numpy_like(np.exp(bias_log.numpy()), image)

    reference = ants.from_numpy((base * 2.0 + 0.5).astype("float32"), spacing=image.spacing, origin=image.origin, direction=image.direction)
    matched = ants.regression_match_image(image, reference, poly_order=1, truncate=True)

    mask = ants.from_numpy(np.ones((8, 8), dtype="float32"), spacing=image.spacing, origin=image.origin, direction=image.direction)
    eig_seg = ants.eig_seg(mask, [image, reference], smooth=0, cthresh=0)

    x = np.vstack([base.ravel(), (base * 2).ravel(), (base + 1).ravel(), (base[::-1]).ravel()]).astype("float64")
    init = ants.initialize_eigenanatomy(x.astype("float32"))

    result = {
        "ants_version": getattr(ants, "__version__", "unknown"),
        "image_shape": _shape_tuple(image.shape),
        "patches_shape": _shape_tuple(patches.shape),
        "reconstructed_shape": _shape_tuple(reconstructed.shape),
        "reconstruction_max_abs_error": float(np.max(np.abs(reconstructed.numpy() - image.numpy()))),
        "one_hot_shape": _shape_tuple(one_hot.shape),
        "one_hot_channel_first_shape": _shape_tuple(one_hot_cf.shape),
        "probability_image_count": len(probability_images),
        "cropped_shape": _shape_tuple(cropped.shape),
        "padded_shape": _shape_tuple(padded.shape),
        "factor_padded_shape": _shape_tuple(factor_padded.shape),
        "warped_range": [float(warped.min()), float(warped.max())],
        "bias_log_range": [float(bias_log.min()), float(bias_log.max())],
        "biased_range": [float(biased.min()), float(biased.max())],
        "matched_range": [float(matched.min()), float(matched.max())],
        "eig_seg_unique": sorted(float(value) for value in np.unique(eig_seg.numpy())),
        "initialize_eigenanatomy": {
            "initlist_count": len(init["initlist"]),
            "mask_shape": _shape_tuple(init["mask"].shape),
            "name_count": len(init["enames"]),
        },
        "crop_image_from_center_point_exported": bool(hasattr(ants, "crop_image_from_center_point")),
    }

    if not skip_random_transform:
        transformed = ants.randomly_transform_image_data(
            reference_image=image,
            input_image_list=[[image]],
            segmentation_image_list=[label],
            number_of_simulations=1,
            transform_type="affine",
            sd_affine=0.001,
            input_image_interpolator="linear",
            segmentation_image_interpolator="nearestNeighbor",
        )
        result["random_transform"] = {
            "simulation_count": len(transformed["simulated_images"]),
            "modalities_first_simulation": len(transformed["simulated_images"][0]),
            "segmentation_count": len(transformed["simulated_segmentation_images"]),
            "which_subject": [int(value) for value in transformed["which_subject"]],
            "transform_count": len(transformed["simulated_transforms"]),
        }

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a tiny in-memory ANTsPy learning/deeplearn helper smoke check."
    )
    parser.add_argument(
        "--skip-random-transform",
        action="store_true",
        help="Skip the tiny affine augmentation check and run only array/intensity helpers.",
    )
    args = parser.parse_args()
    print(json.dumps(run_smoke(args.skip_random_transform), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
