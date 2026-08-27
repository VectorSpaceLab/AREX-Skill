#!/usr/bin/env python
"""Smoke checks for the TorchIO data-model sub-skill.

Uses only synthetic tensors and temporary files. No repository data is needed.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import torch
import torchio as tio


def assert_close_tuple(
    actual: tuple[float, ...],
    expected: tuple[float, ...],
    *,
    tolerance: float = 1e-5,
) -> None:
    assert len(actual) == len(expected)
    for actual_value, expected_value in zip(actual, expected, strict=True):
        assert abs(actual_value - expected_value) <= tolerance


def build_subject(shape: tuple[int, int, int]) -> tio.Subject:
    spatial_i, spatial_j, spatial_k = shape
    affine = tio.AffineMatrix.from_spacing(
        spacing=(0.8, 0.9, 2.5),
        origin=(10.0, 20.0, -30.0),
    )

    scalar_tensor = torch.linspace(
        0,
        1,
        steps=spatial_i * spatial_j * spatial_k,
        dtype=torch.float32,
    ).reshape(1, spatial_i, spatial_j, spatial_k)
    label_tensor = torch.zeros(1, spatial_i, spatial_j, spatial_k, dtype=torch.int16)
    label_tensor[:, 2:6, 3:8, 1:5] = 2

    landmarks = tio.Points(
        torch.tensor([[1.0, 2.0, 3.0], [5.0, 6.0, 7.0]]),
        axes="IJK",
        affine=affine,
        metadata={"kind": "synthetic"},
    )
    boxes = tio.BoundingBoxes(
        torch.tensor([[2, 3, 1, 6, 8, 5]], dtype=torch.float32),
        format=tio.BoundingBoxFormat.IJKIJK,
        labels=torch.tensor([2]),
        affine=affine,
        metadata={"source": "synthetic"},
    )

    scalar = tio.ScalarImage(
        scalar_tensor,
        affine=affine,
        sequence="synthetic-t1",
        points={"fiducials": landmarks},
    )
    label = tio.LabelMap(
        label_tensor,
        affine=affine,
        bounding_boxes={"lesion": boxes},
    )

    return tio.Subject(
        t1=scalar,
        seg=label,
        landmarks=landmarks,
        lesion_boxes=boxes,
        participant_id="synthetic-001",
    )


def run_checks(shape: tuple[int, int, int], save_roundtrip: bool) -> None:
    subject = build_subject(shape)

    assert isinstance(subject.t1, tio.ScalarImage)
    assert isinstance(subject.seg, tio.LabelMap)
    assert isinstance(tio.Study(t1=subject.t1), tio.Subject)
    assert subject.t1.is_loaded
    assert subject.seg.is_loaded
    assert subject.shape == (1, *shape)
    assert subject.spatial_shape == shape
    assert_close_tuple(subject.spacing, (0.8, 0.9, 2.5))
    assert subject.t1.orientation == ("R", "A", "S")
    assert subject.t1.metadata["sequence"] == "synthetic-t1"
    assert subject.metadata["participant_id"] == "synthetic-001"

    world = subject.landmarks.to_world()
    assert world.shape == (2, 3)
    ras = subject.landmarks.to_axes("RAS")
    assert ras.axes == "RAS"

    center_size = subject.lesion_boxes.to_format(tio.BoundingBoxFormat.IJKWHD)
    assert center_size.data.shape == (1, 6)
    assert center_size.labels is not None
    assert int(center_size.labels[0]) == 2

    all_points = subject.all_points()
    all_boxes = subject.all_bounding_boxes()
    assert "landmarks" in all_points
    assert ("t1", "fiducials") in all_points
    assert "lesion_boxes" in all_boxes
    assert ("seg", "lesion") in all_boxes

    channel_last = torch.zeros(shape[0], shape[1], shape[2], 2)
    multi = tio.ScalarImage(channel_last, channels_last=True)
    assert multi.shape == (2, *shape)

    try:
        tio.ScalarImage(torch.zeros(*shape))
    except ValueError as error:
        assert "4D" in str(error)
    else:
        raise AssertionError("3D tensor construction should fail")

    try:
        tio.AffineMatrix(torch.eye(3))
    except ValueError as error:
        assert "4" in str(error)
    else:
        raise AssertionError("3x3 affine construction should fail")

    if save_roundtrip:
        with tempfile.TemporaryDirectory() as tmpdir:
            image_path = Path(tmpdir) / "image.nii.gz"
            label_path = Path(tmpdir) / "label.nii.gz"
            subject.t1.save(image_path)
            subject.seg.save(label_path)
            loaded_image = tio.ScalarImage(image_path)
            loaded_label = tio.LabelMap(label_path)
            assert loaded_image.shape == subject.t1.shape
            assert loaded_label.shape == subject.seg.shape
            assert_close_tuple(loaded_image.spacing, subject.t1.spacing)
            assert_close_tuple(loaded_label.spacing, subject.seg.spacing)
            assert not loaded_image.is_loaded
            loaded_image.load()
            assert loaded_image.is_loaded


def parse_shape(text: str) -> tuple[int, int, int]:
    parts = text.lower().replace("x", ",").split(",")
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("shape must have three dimensions, e.g. 16,18,10")
    try:
        shape = tuple(int(part) for part in parts)
    except ValueError as error:
        raise argparse.ArgumentTypeError("shape dimensions must be integers") from error
    if any(dimension < 8 for dimension in shape):
        raise argparse.ArgumentTypeError("all dimensions must be at least 8 for the synthetic checks")
    return shape  # type: ignore[return-value]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run synthetic TorchIO data-model smoke assertions.",
    )
    parser.add_argument(
        "--shape",
        type=parse_shape,
        default=parse_shape("16,18,10"),
        help="Spatial shape as I,J,K or IxJxK; each dimension must be at least 8.",
    )
    parser.add_argument(
        "--skip-save",
        action="store_true",
        help="Skip temporary NIfTI save/load round-trip checks.",
    )
    args = parser.parse_args()
    run_checks(args.shape, save_roundtrip=not args.skip_save)
    print("TorchIO data-model smoke checks passed")


if __name__ == "__main__":
    main()
