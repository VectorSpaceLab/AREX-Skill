#!/usr/bin/env python3
"""Run deterministic, CPU-safe geometry checks without external data.

The checks intentionally exercise both package-level projective exports and
explicit geometryutils/se3utils imports. No network, GPU, file, or GUI flow is
used. The script is runnable from any current working directory when the
GradSLAM environment is installed.
"""

from __future__ import annotations

import argparse
import json


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run deterministic GradSLAM geometry smoke checks on CPU."
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-5,
        help="Absolute tolerance for round-trip checks (default: 1e-5).",
    )
    return parser


def run_checks(atol: float) -> dict:
    if atol <= 0:
        raise ValueError("--atol must be positive")

    import torch
    import gradslam as gs
    from gradslam.geometry.geometryutils import (
        compose_transforms_3d,
        create_meshgrid,
        normalize_pixel_coords,
        quaternion_to_rotation_matrix,
        transform_normals,
        transform_pointcloud,
    )
    from gradslam.geometry.se3utils import se3_exp

    torch.manual_seed(0)
    dtype = torch.float32

    # Public projective conversion and a pinhole projection/unprojection round trip.
    points = torch.tensor(
        [[0.0, 0.0, 2.0], [0.5, -0.25, 4.0]], dtype=dtype
    )
    homogeneous = gs.homogenize_points(points)
    assert homogeneous.shape == (2, 4)
    assert torch.allclose(gs.unhomogenize_points(homogeneous), points, atol=atol)

    K = torch.eye(3, dtype=dtype)
    K[0, 0], K[1, 1] = 100.0, 100.0
    K[0, 2], K[1, 2] = 32.0, 24.0
    K_inv = gs.inverse_intrinsics(K)
    projection = torch.eye(4, dtype=dtype)
    projection[:3, :3] = K
    pixels = gs.project_points(points, projection)
    recovered = gs.unproject_points(pixels, K_inv, points[:, 2])
    assert pixels.shape == (2, 2)
    assert torch.allclose(recovered, points, atol=atol)

    # Batched shape path and zero-weight finite fallback.
    batched = points.view(1, 2, 3).repeat(2, 1, 1)
    batched_pixels = gs.project_points(batched, projection)
    assert batched_pixels.shape == (2, 2, 2)
    zero_weight = torch.tensor([[1.0, 2.0, 0.0]], dtype=dtype)
    assert torch.isfinite(gs.unhomogenize_points(zero_weight)).all()

    # Direct geometryutils helpers: grid, transform, normals, and quaternion.
    grid = create_meshgrid(3, 4, normalized_coords=False)
    assert grid.shape == (1, 3, 4, 2)
    normalized = normalize_pixel_coords(grid, 3, 4)
    assert normalized.shape == grid.shape

    transform = torch.eye(4, dtype=dtype)
    transform[:3, 3] = torch.tensor([1.0, 2.0, 3.0])
    moved = transform_pointcloud(points, transform)
    assert torch.allclose(moved, points + transform[:3, 3], atol=atol)
    normals = torch.tensor([[1.0, 0.0, 0.0]], dtype=dtype)
    assert torch.allclose(transform_normals(normals, transform), normals, atol=atol)
    assert torch.allclose(
        compose_transforms_3d(transform, torch.eye(4)), transform, atol=atol
    )

    q = torch.tensor([0.0, 0.0, 0.0, 1.0], dtype=dtype, requires_grad=True)
    rotation = quaternion_to_rotation_matrix(q)
    assert torch.allclose(rotation, torch.eye(3), atol=atol)

    # Direct se3utils import and differentiability check.
    xi = torch.tensor(
        [0.1, 0.0, 0.0, 0.0, 0.0, 0.05], dtype=dtype, requires_grad=True
    )
    update = se3_exp(xi)
    loss = transform_pointcloud(points, update).square().sum() + rotation.sum()
    loss.backward()
    assert xi.grad is not None and torch.isfinite(xi.grad).all()
    assert q.grad is not None and torch.isfinite(q.grad).all()

    return {
        "device": "cpu",
        "points_shape": list(points.shape),
        "pixels_shape": list(pixels.shape),
        "batched_pixels_shape": list(batched_pixels.shape),
        "se3_shape": list(update.shape),
        "finite_gradients": True,
    }


def main(argv=None) -> int:
    args = make_parser().parse_args(argv)
    try:
        result = run_checks(args.atol)
    except Exception as exc:  # concise failure for a skill usability check
        print("geometry smoke failed: {0}: {1}".format(type(exc).__name__, exc))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
