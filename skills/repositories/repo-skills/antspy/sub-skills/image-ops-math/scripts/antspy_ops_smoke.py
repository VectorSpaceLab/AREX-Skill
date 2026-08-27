#!/usr/bin/env python3
"""Tiny ANTsPy image operations smoke check.

This script uses only in-memory images. It avoids downloads, repository-path
dependencies, registration, GPU work, credentials, and destructive writes.

Usage:
    python antspy_ops_smoke.py
    python antspy_ops_smoke.py --skip-expensive
"""

from __future__ import annotations

import argparse
import json


def _space_summary(image):
    return {
        "dimension": image.dimension,
        "shape": tuple(int(value) for value in image.shape),
        "spacing": tuple(float(value) for value in image.spacing),
        "origin": tuple(float(value) for value in image.origin),
    }


def run_smoke(skip_expensive: bool = False) -> dict:
    import ants
    import numpy as np

    base = np.zeros((12, 10), dtype="float32")
    base[3:9, 2:8] = 2.0
    base[5:7, 4:6] = 5.0
    image = ants.from_numpy(base, spacing=(1.0, 1.5), origin=(0.25, -0.5))

    mask = ants.get_mask(image, low_thresh=1.0, high_thresh=10.0, cleanup=0)
    if mask.max() == 0:
        raise RuntimeError("expected a non-empty mask")

    threshold = ants.threshold_image(image, 1.0, 10.0)
    smoothed = image.smooth_image(0.5, sigma_in_physical_coordinates=False)
    scalar_resampled = ants.resample_image(image, (6, 5), use_voxels=True, interp_type=0)

    label_array = (base > 0).astype("float32")
    label = ants.from_numpy(label_array, spacing=image.spacing, origin=image.origin, direction=image.direction)
    label_resampled = ants.resample_image_to_target(label, scalar_resampled, interp_type="nearestNeighbor")
    unique_labels = set(np.unique(label_resampled.numpy()).tolist())
    if not unique_labels.issubset({0.0, 1.0}):
        raise RuntimeError(f"nearest-neighbor label resampling produced unexpected values: {unique_labels}")

    normalized = ants.iMath(image, "Normalize")
    dilated = ants.morphology(mask, operation="dilate", radius=1, mtype="binary")
    cropped = ants.crop_image(image, mask, label=1)
    decropped = ants.decrop_image(cropped, image)
    padded, lower_pad, upper_pad = ants.pad_image(cropped, pad_width=(2, 2), return_padvals=True)

    metric = ants.image_similarity(image.clone("float"), smoothed.clone("float"), metric_type="MeanSquares")
    mutual_information = ants.image_mutual_information(image.clone("float"), smoothed.clone("float"))
    neighborhoods = ants.get_neighborhood_in_mask(image, mask, radius=1, boundary_condition="mean")
    hausdorff = ants.hausdorff_distance(mask, dilated)

    unsupported_operation_error = None
    try:
        ants.iMath(image, "DefinitelyNotAnOperation")
    except ValueError as exc:
        unsupported_operation_error = str(exc)
    if unsupported_operation_error is None:
        raise RuntimeError("expected unsupported iMath operation to raise ValueError")

    result = {
        "ants_version": getattr(ants, "__version__", "unknown"),
        "image": _space_summary(image),
        "mask_sum": float(mask.sum()),
        "threshold_sum": float(threshold.sum()),
        "smoothed_range": [float(smoothed.min()), float(smoothed.max())],
        "scalar_resampled": _space_summary(scalar_resampled),
        "label_unique_values": sorted(unique_labels),
        "normalized_range": [float(normalized.min()), float(normalized.max())],
        "dilated_sum": float(dilated.sum()),
        "cropped_shape": tuple(int(value) for value in cropped.shape),
        "decropped_shape": tuple(int(value) for value in decropped.shape),
        "padded_shape": tuple(int(value) for value in padded.shape),
        "pad_values": {"lower": lower_pad, "upper": upper_pad},
        "mean_squares": float(metric),
        "mutual_information": float(mutual_information),
        "neighborhood_shape": tuple(int(value) for value in neighborhoods.shape),
        "hausdorff_keys": sorted(str(key) for key in hausdorff.keys()) if hasattr(hausdorff, "keys") else None,
        "unsupported_iMath_error": unsupported_operation_error,
    }

    if not skip_expensive:
        corrected = ants.n4_bias_field_correction(
            image,
            mask=mask,
            shrink_factor=2,
            convergence={"iters": [1], "tol": 1e-6},
        )
        result["n4_corrected_range"] = [float(corrected.min()), float(corrected.max())]

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny in-memory ANTsPy image-ops smoke check.")
    parser.add_argument(
        "--skip-expensive",
        action="store_true",
        help="Skip the tiny bounded N4 check and run only fast operations.",
    )
    args = parser.parse_args()
    print(json.dumps(run_smoke(args.skip_expensive), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
