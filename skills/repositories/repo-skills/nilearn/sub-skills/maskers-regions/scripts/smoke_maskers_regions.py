#!/usr/bin/env python3
"""No-network smoke check for Nilearn maskers and regions."""

from __future__ import annotations

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Create tiny synthetic NIfTI images and exercise NiftiMasker, "
            "NiftiLabelsMasker, and connected_label_regions without network."
        )
    )
    parser.add_argument(
        "--n-scans",
        type=int,
        default=5,
        help="Number of synthetic 3D volumes in the 4D image.",
    )
    parser.add_argument(
        "--shape",
        type=int,
        nargs=3,
        default=(4, 4, 4),
        metavar=("X", "Y", "Z"),
        help="Spatial shape of the synthetic image.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation for stdout; use 0 for compact JSON.",
    )
    return parser


def make_synthetic_images(shape: tuple[int, int, int], n_scans: int):
    import nibabel as nib
    import numpy as np

    affine = np.eye(4)
    spatial_size = int(np.prod(shape))
    base_grid = np.arange(spatial_size, dtype=np.float32).reshape(shape)
    data = np.stack(
        [base_grid + float(scan_index) for scan_index in range(n_scans)],
        axis=-1,
    )

    mask_data = np.ones(shape, dtype=np.int8)
    labels_data = np.zeros(shape, dtype=np.int16)
    labels_data[:2, :2, :2] = 1
    labels_data[2:, 2:, 2:] = 2
    labels_data[0, 3, 0] = 1

    return {
        "fmri_img": nib.Nifti1Image(data, affine),
        "mask_img": nib.Nifti1Image(mask_data, affine),
        "labels_img": nib.Nifti1Image(labels_data, affine),
    }


def run_smoke(shape: tuple[int, int, int], n_scans: int) -> dict[str, object]:
    import numpy as np

    from nilearn.maskers import NiftiLabelsMasker, NiftiMasker
    from nilearn.regions import connected_label_regions

    images = make_synthetic_images(shape, n_scans)

    voxel_masker = NiftiMasker(
        mask_img=images["mask_img"],
        standardize=None,
        reports=False,
    )
    voxel_signals = voxel_masker.fit_transform(images["fmri_img"])
    voxel_inverse = voxel_masker.inverse_transform(voxel_signals[:1])

    labels_masker = NiftiLabelsMasker(
        labels_img=images["labels_img"],
        background_label=0,
        mask_img=images["mask_img"],
        strategy="mean",
        standardize=None,
        reports=False,
        resampling_target=None,
    )
    label_signals = labels_masker.fit_transform(images["fmri_img"])
    label_inverse = labels_masker.inverse_transform(label_signals[:1])

    split_labels_img = connected_label_regions(
        images["labels_img"],
        connect_diag=False,
    )
    split_label_values = sorted(
        int(value)
        for value in np.unique(split_labels_img.get_fdata())
        if int(value) != 0
    )

    result = {
        "ok": True,
        "input_shape": list(shape) + [n_scans],
        "nifti_masker": {
            "signals_shape": list(voxel_signals.shape),
            "n_elements": int(voxel_masker.n_elements_),
            "inverse_shape": list(voxel_inverse.shape),
        },
        "nifti_labels_masker": {
            "signals_shape": list(label_signals.shape),
            "n_elements": int(labels_masker.n_elements_),
            "labels": [
                int(label)
                for label in labels_masker.labels_
                if int(label) != labels_masker.background_label
            ],
            "inverse_shape": list(label_inverse.shape),
        },
        "connected_label_regions": {
            "non_background_labels": split_label_values,
            "n_regions": len(split_label_values),
        },
    }

    if voxel_signals.shape != (n_scans, int(np.prod(shape))):
        raise RuntimeError(f"Unexpected NiftiMasker shape: {voxel_signals.shape}")
    if label_signals.shape != (n_scans, 2):
        raise RuntimeError(
            f"Unexpected NiftiLabelsMasker shape: {label_signals.shape}"
        )
    if len(split_label_values) < 3:
        raise RuntimeError("Expected disconnected label image to split regions")

    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.n_scans < 2:
        parser.error("--n-scans must be at least 2")
    if any(dimension < 3 for dimension in args.shape):
        parser.error("all --shape dimensions must be at least 3")

    result = run_smoke(tuple(args.shape), args.n_scans)
    indent = None if args.indent == 0 else args.indent
    print(json.dumps(result, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"ok": False, "error": str(error)}), file=sys.stderr)
        raise
