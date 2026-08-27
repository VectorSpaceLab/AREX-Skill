#!/usr/bin/env python
"""No-network smoke check for Nilearn image, masking, and signal utilities."""

from __future__ import annotations

import argparse
import json
import warnings


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build tiny in-memory NIfTI images and exercise Nilearn image "
            "math, resampling, masking, clean_img, and signal.clean."
        )
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for generated data (default: 0).",
    )
    parser.add_argument(
        "--n-scans",
        type=int,
        default=12,
        help=(
            "Number of generated time points; must be at least 8 "
            "(default: 12)."
        ),
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON summary.",
    )
    return parser


def _as_list(shape_or_array) -> list[int | float | bool]:
    import numpy as np

    return np.asarray(shape_or_array).tolist()


def run_smoke(seed: int, n_scans: int) -> dict[str, object]:
    import nibabel as nib
    import numpy as np
    from nilearn import image, masking, signal

    if n_scans < 8:
        raise ValueError("--n-scans must be at least 8 for stable cleaning checks")

    rng = np.random.default_rng(seed)
    affine = np.eye(4)
    shape_3d = (5, 6, 7)

    base = rng.normal(size=(*shape_3d, n_scans)).astype("float32")
    trend = np.linspace(-1.0, 1.0, n_scans, dtype="float32")
    base[1:4, 2:5, 3:6, :] += trend
    run_img = nib.Nifti1Image(base, affine)

    checked = image.check_niimg(run_img, ensure_ndim=4)
    first_volume = image.index_img(checked, 0)
    mean_img = image.mean_img(checked)
    z_img = image.math_img(
        "(img - np.mean(img)) / np.std(img)",
        img=mean_img,
    )
    thresholded = image.threshold_img(z_img, threshold=0.0)

    target_affine = np.diag([2.0, 2.0, 2.0, 1.0])
    target_data = np.zeros((3, 3, 4), dtype="float32")
    target_img = nib.Nifti1Image(target_data, target_affine)
    resampled = image.resample_to_img(
        thresholded,
        target_img,
        interpolation="continuous",
    )

    mask_data = np.zeros(shape_3d, dtype="uint8")
    mask_data[1:4, 2:5, 3:6] = 1
    mask_img = image.new_img_like(run_img, mask_data, affine)
    signals = masking.apply_mask(checked, mask_img, ensure_finite=True)

    confounds = np.column_stack(
        [
            np.linspace(-1.0, 1.0, n_scans),
            np.sin(np.linspace(0.0, np.pi, n_scans)),
        ]
    )
    sample_mask = np.arange(n_scans)
    sample_mask = sample_mask[sample_mask != 2]

    cleaned_signals = signal.clean(
        signals,
        confounds=confounds,
        sample_mask=sample_mask,
        detrend=True,
        standardize="zscore_sample",
        filter="butterworth",
        high_pass=0.01,
        t_r=2.0,
        ensure_finite=True,
        butterworth__padlen=3,
    )
    restored_img = masking.unmask(cleaned_signals, mask_img)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cleaned_img = image.clean_img(
            checked,
            confounds=confounds,
            detrend=True,
            standardize="zscore_sample",
            high_pass=0.01,
            t_r=2.0,
            ensure_finite=True,
            mask_img=mask_img,
            clean__butterworth__padlen=3,
        )

    return {
        "ok": True,
        "input_shape": _as_list(checked.shape),
        "first_volume_shape": _as_list(first_volume.shape),
        "resampled_shape": _as_list(resampled.shape),
        "mask_voxels": int(mask_data.sum()),
        "signals_shape": _as_list(signals.shape),
        "cleaned_signals_shape": _as_list(cleaned_signals.shape),
        "restored_shape": _as_list(restored_img.shape),
        "cleaned_img_shape": _as_list(cleaned_img.shape),
        "affine_matches_mask": bool(np.allclose(checked.affine, mask_img.affine)),
        "signals_all_finite": bool(np.isfinite(signals).all()),
        "cleaned_signals_all_finite": bool(np.isfinite(cleaned_signals).all()),
        "cleaned_img_all_finite": bool(np.isfinite(cleaned_img.get_fdata()).all()),
        "warnings": [str(item.message) for item in caught],
    }


def main() -> None:
    parser = _make_parser()
    args = parser.parse_args()
    summary = run_smoke(seed=args.seed, n_scans=args.n_scans)
    print(json.dumps(summary, indent=2 if args.pretty else None, sort_keys=True))


if __name__ == "__main__":
    main()
