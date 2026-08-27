#!/usr/bin/env python3
"""Deterministic NumPy-only geometry checks for the geometry-and-evaluation route.

This helper intentionally does not import the legacy detector, Torch, spconv, or
Numba. Run from any working directory with:
  python geometry_smoke.py --help
  python geometry_smoke.py
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable

import numpy as np


EPS = 1e-6


def _require_boxes(value: np.ndarray, name: str, width: int = 7) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.ndim != 2 or array.shape[1] != width:
        raise ValueError(f"{name} must have shape [N,{width}], got {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains non-finite values")
    if np.any(array[:, 3:6] <= 0):
        raise ValueError(f"{name} dimensions must be positive")
    return array


def corners_nd(dims: np.ndarray, origin: float | tuple[float, ...] = 0.5) -> np.ndarray:
    dims = np.asarray(dims, dtype=np.float64)
    if dims.ndim != 2 or dims.shape[1] not in (2, 3):
        raise ValueError(f"dims must have shape [N,2] or [N,3], got {dims.shape}")
    if np.any(dims <= 0):
        raise ValueError("dims must be positive")
    ndim = dims.shape[1]
    norm = np.stack(np.unravel_index(np.arange(2**ndim), [2] * ndim), axis=1)
    if ndim == 2:
        norm = norm[[0, 1, 3, 2]]
    else:
        norm = norm[[0, 1, 3, 2, 4, 5, 7, 6]]
    norm = norm - np.asarray(origin, dtype=np.float64)
    return dims[:, None, :] * norm[None, :, :]


def rotation_3d_z(points: np.ndarray, angles: np.ndarray) -> np.ndarray:
    points = np.asarray(points, dtype=np.float64)
    angles = np.asarray(angles, dtype=np.float64)
    sin = np.sin(angles)
    cos = np.cos(angles)
    matrix_t = np.stack(
        [[cos, -sin, np.zeros_like(cos)],
         [sin, cos, np.zeros_like(cos)],
         [np.zeros_like(cos), np.zeros_like(cos), np.ones_like(cos)]],
        axis=0,
    )
    return np.einsum("aij,jka->aik", points, matrix_t)


def lidar_corners(boxes: np.ndarray) -> np.ndarray:
    boxes = _require_boxes(boxes, "boxes")
    corners = corners_nd(boxes[:, 3:6], origin=(0.5, 0.5, 0.5))
    return rotation_3d_z(corners, boxes[:, 6]) + boxes[:, None, :3]


def second_box_encode(boxes: np.ndarray, anchors: np.ndarray) -> np.ndarray:
    boxes = _require_boxes(boxes, "boxes")
    anchors = _require_boxes(anchors, "anchors")
    if boxes.shape != anchors.shape:
        raise ValueError(f"boxes and anchors must have equal shapes, got {boxes.shape} and {anchors.shape}")
    diagonal = np.sqrt(anchors[:, 4:5] ** 2 + anchors[:, 3:4] ** 2)
    return np.concatenate(
        [
            (boxes[:, 0:1] - anchors[:, 0:1]) / diagonal,
            (boxes[:, 1:2] - anchors[:, 1:2]) / diagonal,
            (boxes[:, 2:3] - anchors[:, 2:3]) / anchors[:, 5:6],
            np.log(boxes[:, 3:4] / anchors[:, 3:4]),
            np.log(boxes[:, 4:5] / anchors[:, 4:5]),
            np.log(boxes[:, 5:6] / anchors[:, 5:6]),
            boxes[:, 6:7] - anchors[:, 6:7],
        ],
        axis=1,
    )


def second_box_decode(encodings: np.ndarray, anchors: np.ndarray) -> np.ndarray:
    anchors = _require_boxes(anchors, "anchors")
    encodings = np.asarray(encodings, dtype=np.float64)
    if encodings.ndim != 2 or encodings.shape != (anchors.shape[0], 7):
        raise ValueError(
            f"encodings must have shape [{anchors.shape[0]},7], got {encodings.shape}"
        )
    diagonal = np.sqrt(anchors[:, 4:5] ** 2 + anchors[:, 3:4] ** 2)
    return np.concatenate(
        [
            encodings[:, 0:1] * diagonal + anchors[:, 0:1],
            encodings[:, 1:2] * diagonal + anchors[:, 1:2],
            encodings[:, 2:3] * anchors[:, 5:6] + anchors[:, 2:3],
            np.exp(encodings[:, 3:4]) * anchors[:, 3:4],
            np.exp(encodings[:, 4:5]) * anchors[:, 4:5],
            np.exp(encodings[:, 5:6]) * anchors[:, 5:6],
            encodings[:, 6:7] + anchors[:, 6:7],
        ],
        axis=1,
    )


def limit_period(value: np.ndarray | float, offset: float = 0.5, period: float = np.pi) -> np.ndarray:
    value = np.asarray(value, dtype=np.float64)
    return value - np.floor(value / period + offset) * period


def _check(name: str, function: Callable[[], None], quiet: bool) -> None:
    try:
        function()
    except Exception as exc:  # pragma: no cover - user-facing diagnostic
        print(f"[FAIL] {name}: {exc}", file=sys.stderr)
        raise
    if not quiet:
        print(f"[PASS] {name}")


def check_corners() -> None:
    box = np.array([[1.0, 2.0, 3.0, 2.0, 4.0, 2.0, np.pi / 2]])
    corners = lidar_corners(box)
    assert corners.shape == (1, 8, 3)
    np.testing.assert_allclose(corners.min(axis=1)[0], [1.0 - 2.0, 2.0 - 1.0, 2.0], atol=EPS)
    np.testing.assert_allclose(corners.max(axis=1)[0], [1.0 + 2.0, 2.0 + 1.0, 4.0], atol=EPS)


def check_round_trip() -> None:
    anchors = np.array([[4.0, -2.0, 1.5, 2.0, 4.0, 1.6, -2.9]])
    boxes = np.array([[4.7, -1.4, 1.8, 2.4, 3.2, 1.9, 2.8]])
    encoded = second_box_encode(boxes, anchors)
    decoded = second_box_decode(encoded, anchors)
    np.testing.assert_allclose(decoded[:, :6], boxes[:, :6], atol=EPS)
    angle_error = limit_period(decoded[:, 6] - boxes[:, 6], period=2 * np.pi)
    np.testing.assert_allclose(angle_error, 0.0, atol=EPS)
    # A dimension-order swap must change the geometric extents, not be silently accepted.
    swapped = boxes[:, [0, 1, 2, 4, 3, 5, 6]]
    assert not np.allclose(lidar_corners(swapped), lidar_corners(boxes), atol=1e-3)


def check_period() -> None:
    values = np.array([-3 * np.pi, -np.pi, -0.1, 0.1, np.pi, 3 * np.pi])
    wrapped = limit_period(values, period=2 * np.pi)
    assert np.all(wrapped >= -np.pi - EPS)
    assert np.all(wrapped < np.pi + EPS)
    np.testing.assert_allclose(limit_period(np.array([0.0, np.pi]), period=np.pi), [0.0, 0.0], atol=EPS)


def check_malformed_shapes() -> None:
    valid = np.ones((1, 7), dtype=np.float64)
    for bad in (np.ones((7,), dtype=np.float64), np.ones((1, 6), dtype=np.float64)):
        try:
            second_box_encode(bad, valid)
        except ValueError:
            continue
        raise AssertionError(f"malformed shape {bad.shape} was accepted")
    try:
        second_box_decode(np.ones((1, 6)), valid)
    except ValueError:
        pass
    else:
        raise AssertionError("malformed encoding shape was accepted")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true", help="print only the final status")
    args = parser.parse_args(argv)
    _check("corners [N,8,3] and extents", check_corners, args.quiet)
    _check("encode/decode round-trip and dimension-order guard", check_round_trip, args.quiet)
    _check("period limiting", check_period, args.quiet)
    _check("malformed shape errors", check_malformed_shapes, args.quiet)
    print("geometry smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
