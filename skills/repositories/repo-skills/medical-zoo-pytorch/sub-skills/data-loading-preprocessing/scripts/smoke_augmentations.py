#!/usr/bin/env python3
"""Synthetic smoke checks for 3D augmentation operators.

The fixtures are tiny numpy volumes, so this script never reads a real dataset.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import numpy as np


def ensure_repo_on_path() -> None:
    try:
        import lib.augment3D  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    here = Path(__file__).resolve()
    for parent in (here.parent, *here.parents):
        if (parent / "lib" / "augment3D" / "__init__.py").is_file():
            sys.path.insert(0, str(parent))
            return

    raise RuntimeError(
        "Could not import MedicalZooPytorch augmentation helpers. Run from a checkout that contains the repo root, or make the package importable first."
    )


ensure_repo_on_path()

from lib.augment3D import (
    ComposeTransforms,
    ElasticTransform,
    GaussianNoise,
    RandomChoice,
    RandomCropToLabels,
    RandomFlip,
    RandomRotation,
    RandomShift,
    RandomZoom,
)
from lib.augment3D.elastic_deform import elastic_transform_3d
from lib.augment3D.random_flip import random_flip
from lib.augment3D.random_rotate import random_rotate3D
from lib.augment3D.random_shift import random_shift
from lib.augment3D.random_rescale import random_zoom


def make_fixture() -> tuple[np.ndarray, np.ndarray]:
    volume = np.zeros((16, 16, 16), dtype=np.float32)
    volume[4:12, 4:12, 4:12] = 1.0
    label = np.zeros_like(volume, dtype=np.int16)
    label[6:10, 6:10, 6:10] = 1
    return volume, label


def assert_shape(name: str, actual, expected) -> None:
    if tuple(actual) != tuple(expected):
        raise AssertionError(f"{name} shape mismatch: expected {expected}, got {tuple(actual)}")


def main() -> int:
    np.random.seed(0)
    random.seed(0)

    volume, label = make_fixture()

    flipped, flipped_label = random_flip(volume, label, axis_for_flip=1)
    assert_shape("random_flip", flipped.shape, volume.shape)
    assert_shape("random_flip label", flipped_label.shape, label.shape)

    rotated = random_rotate3D(volume, -12, 12)
    rotated_label = random_rotate3D(label.astype(np.float32), -12, 12)
    if rotated.ndim != 3 or rotated_label.ndim != 3:
        raise AssertionError("random_rotate3D should return 3D arrays")

    cropped, cropped_label = RandomCropToLabels()(volume, label)
    if cropped.ndim != 3 or cropped_label.shape != label.shape:
        raise AssertionError("RandomCropToLabels should return a cropped 3D image and the original label map")

    shifted = random_shift(volume)
    assert_shape("random_shift", shifted.shape, volume.shape)

    shifted_wrapper_img, shifted_wrapper_label = RandomShift(max_percentage=0.3)(volume.copy(), label.copy())
    assert_shape("RandomShift direct label", shifted_wrapper_label.shape, label.shape)

    zoomed = random_zoom(volume)
    assert_shape("random_zoom", zoomed.shape, volume.shape)

    zoomed_wrapper_img, zoomed_wrapper_label = RandomZoom(min_percentage=0.9, max_percentage=1.05)(volume.copy(), label.copy())
    assert_shape("RandomZoom direct label", zoomed_wrapper_label.shape, label.shape)

    elastic, elastic_label = elastic_transform_3d(volume, label)
    assert_shape("elastic_transform_3d", elastic.shape, volume.shape)
    assert_shape("elastic_transform_3d label", elastic_label.shape, label.shape)

    rot_wrapper = RandomRotation(min_angle=-5, max_angle=5)
    rot_img, rot_lab = rot_wrapper(volume.copy(), label.copy())
    if rot_img.ndim != 3 or rot_lab.ndim != 3:
        raise AssertionError("RandomRotation wrapper should return 3D arrays")

    shift_wrapper = RandomShift(max_percentage=0.3)
    shift_img, shift_lab = shift_wrapper(volume.copy(), label.copy())
    assert_shape("RandomShift wrapper", shift_img.shape, volume.shape)
    assert_shape("RandomShift wrapper label", shift_lab.shape, label.shape)

    zoom_wrapper = RandomZoom(min_percentage=0.9, max_percentage=1.05)
    zoom_img, zoom_lab = zoom_wrapper(volume.copy(), label.copy())
    assert_shape("RandomZoom wrapper", zoom_img.shape, volume.shape)
    assert_shape("RandomZoom wrapper label", zoom_lab.shape, label.shape)

    elastic_wrapper = ElasticTransform(alpha=0.5, sigma=2)
    elastic_img, elastic_lab = elastic_wrapper(volume.copy(), label.copy())
    assert_shape("ElasticTransform wrapper", elastic_img.shape, volume.shape)
    assert_shape("ElasticTransform wrapper label", elastic_lab.shape, label.shape)

    choice = RandomChoice(
        transforms=[GaussianNoise(mean=0, std=0.01), RandomFlip(), ElasticTransform(alpha=0.5, sigma=2)],
        p=1.0,
    )
    chosen_imgs, chosen_label = choice([volume.copy(), volume.copy()], label.copy())
    if len(chosen_imgs) != 2:
        raise AssertionError("RandomChoice should preserve the number of image tensors")
    assert_shape("RandomChoice label", chosen_label.shape, label.shape)

    composed = ComposeTransforms(
        transforms=[GaussianNoise(mean=0, std=0.01), RandomFlip()],
        p=1.0,
    )
    composed_imgs, composed_label = composed([volume.copy(), volume.copy()], label.copy())
    if len(composed_imgs) != 2:
        raise AssertionError("ComposeTransforms should preserve the number of image tensors")
    assert_shape("ComposeTransforms label", composed_label.shape, label.shape)

    print("augmentation smoke ok")
    print(
        "shapes:",
        {
            "flip": flipped.shape,
            "rotate": rotated.shape,
            "shift": shifted.shape,
            "zoom": zoomed.shape,
            "elastic": elastic.shape,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
