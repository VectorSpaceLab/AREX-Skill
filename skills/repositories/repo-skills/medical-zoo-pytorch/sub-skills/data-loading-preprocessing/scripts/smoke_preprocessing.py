#!/usr/bin/env python3
"""Synthetic smoke checks for medical-image preprocessing helpers.

This script creates tiny temporary NIfTI fixtures and exercises the pure
preprocessing helpers without touching any real dataset.
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sys

import nibabel as nib
import numpy as np
import torch


def ensure_repo_on_path() -> None:
    try:
        import lib.medloaders.medical_image_process  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        if (parent / "lib" / "medloaders" / "medical_image_process.py").is_file():
            sys.path.insert(0, str(parent))
            return

    raise RuntimeError(
        "Could not import MedicalZooPytorch preprocessing helpers. Run from a checkout that contains the repo root, or make the package importable first."
    )


ensure_repo_on_path()

from lib.medloaders import medical_image_process as mp


def save_nifti(path: Path, data: np.ndarray, affine: np.ndarray | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    affine = np.eye(4, dtype=np.float32) if affine is None else np.asarray(affine, dtype=np.float32)
    img = nib.Nifti1Image(np.asarray(data, dtype=np.float32), affine)
    nib.save(img, str(path))
    return path


def assert_shape(name: str, actual, expected) -> None:
    if tuple(actual) != tuple(expected):
        raise AssertionError(f"{name} shape mismatch: expected {expected}, got {tuple(actual)}")


def main() -> int:
    np.random.seed(0)
    torch.manual_seed(0)

    with TemporaryDirectory(prefix="medicalzoo-preproc-") as tmpdir:
        tmp = Path(tmpdir)

        base = np.arange(6 * 5 * 4, dtype=np.float32).reshape(6, 5, 4)
        label = np.zeros_like(base, dtype=np.float32)
        label[1:5, 1:4, 1:3] = 1.0

        img_path = save_nifti(tmp / "img.nii.gz", base)
        label_path = save_nifti(
            tmp / "label.nii.gz",
            label,
            affine=np.array([
                [1.5, 0, 0, 2],
                [0, 2.0, 0, -1],
                [0, 0, 2.5, 3],
                [0, 0, 0, 1],
            ], dtype=np.float32),
        )
        canonical_path = save_nifti(
            tmp / "canonical.nii.gz",
            base.copy(),
            affine=np.eye(4, dtype=np.float32),
        )

        loaded = mp.load_medical_image(str(img_path), normalization=None, clip_intenisty=False)
        assert_shape("load_medical_image", loaded.shape, base.shape)

        label_tensor = mp.load_medical_image(str(label_path), type="label", viz3d=True)
        assert_shape("label viz", label_tensor.shape, base.shape)

        resampled = mp.load_medical_image(
            str(img_path),
            resample=(2, 2, 2),
            normalization=None,
            clip_intenisty=False,
        )
        if tuple(resampled.shape) == tuple(loaded.shape):
            raise AssertionError("resample=(2,2,2) should change the output shape")

        canonical = mp.load_medical_image(
            str(canonical_path),
            to_canonical=True,
            normalization=None,
            clip_intenisty=False,
        )
        assert_shape("canonical load", canonical.shape, base.shape)

        affine = mp.load_affine_matrix(str(img_path))
        assert_shape("affine matrix", affine.shape, (4, 4))

        transformed = mp.transform_coordinate_space(nib.load(str(img_path)), nib.load(str(label_path)))
        assert_shape("coordinate transform", transformed.shape, base.shape)
        if not np.isfinite(transformed).all():
            raise AssertionError("coordinate transform produced non-finite values")

        rescaled = mp.rescale_data_volume(base, (3, 4, 2))
        assert_shape("rescale_data_volume", rescaled.shape, (3, 4, 2))

        normalized = mp.normalize_intensity(
            torch.from_numpy(base.copy()),
            normalization="max_min",
            norm_values=(float(base.mean()), float(base.std() or 1.0), float(base.max()), float(base.min())),
        )
        assert_shape("normalize_intensity", normalized.shape, base.shape)

        cropped = mp.crop_img(torch.from_numpy(base.copy()), (3, 4, 2), (1, 0, 1))
        assert_shape("crop_img", cropped.shape, (3, 4, 2))

        transformed_intensity = mp.medical_image_transform(
            torch.from_numpy(base.copy()),
            normalization="full_volume_mean",
            norm_values=(float(base.mean()), float(base.std() or 1.0), float(base.max()), float(base.min())),
        )
        assert_shape("medical_image_transform", transformed_intensity.shape, base.shape)

        print("preprocessing smoke ok")
        print(f"loaded={tuple(loaded.shape)} resampled={tuple(resampled.shape)} cropped={tuple(cropped.shape)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
