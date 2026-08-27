#!/usr/bin/env python3
"""Offline, deterministic smoke checks for PyPose geometry/evaluation APIs."""

from __future__ import annotations

import argparse

import torch
import pypose as pp
from pypose.metric.ape_rpe import (
    StampedSE3,
    associate_traj,
    compute_error,
    matching_time_indices,
)


def check_projection(device: torch.device) -> None:
    dtype = torch.float64
    points = torch.tensor(
        [[0.5, -0.25, 2.0], [1.0, 1.0, 4.0]], dtype=dtype, device=device
    )
    intrinsics = torch.tensor(
        [[4.0, 0.0, 2.0], [0.0, 4.0, 1.0], [0.0, 0.0, 1.0]],
        dtype=dtype,
        device=device,
    )
    pixels = pp.point2pixel(points, intrinsics)
    recovered = pp.pixel2point(pixels, points[..., 2], intrinsics)
    pp.testing.assert_close(recovered, points, rtol=1e-10, atol=1e-10)

    residual = pp.reprojerr(points, pixels, intrinsics, reduction="norm")
    pp.testing.assert_close(residual, torch.zeros_like(residual), atol=1e-10, rtol=1e-10)
    homogeneous = pp.cart2homo(points)
    pp.testing.assert_close(pp.homo2cart(homogeneous), points, atol=1e-10, rtol=1e-10)

    source = torch.tensor(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        dtype=dtype,
        device=device,
    )
    target = source + torch.tensor([1.0, 2.0, 3.0], dtype=dtype, device=device)
    estimated = pp.svdtf(source, target)
    pp.testing.assert_close(estimated @ source, target, atol=1e-10, rtol=1e-10)
    scaled_target = 2.0 * source + torch.tensor([1.0, 2.0, 3.0], dtype=dtype, device=device)
    estimated_sim3 = pp.svdstf(source, scaled_target, with_scale=True)
    pp.testing.assert_close(estimated_sim3 @ source, scaled_target, atol=1e-9, rtol=1e-9)


def check_splines(device: torch.device) -> None:
    dtype = torch.float64
    waypoints = torch.tensor(
        [[0.0, 0.0, 0.0], [1.0, 0.5, 0.0], [2.0, 0.0, 0.0]],
        dtype=dtype,
        device=device,
    )
    cubic = pp.chspline(waypoints, interval=0.5)
    assert cubic.shape == (5, 3), cubic.shape
    pp.testing.assert_close(cubic[[0, 2, 4]], waypoints)

    poses = pp.SE3(
        torch.tensor(
            [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                [2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                [3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                [4.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            ],
            dtype=dtype,
            device=device,
        )
    )
    spline = pp.bspline(poses, interval=0.5)
    assert spline.shape == (5, 7), spline.shape
    extrapolated = pp.bspline(poses, interval=0.5, extrapolate=True)
    assert extrapolated.shape == (13, 7), extrapolated.shape
    pp.testing.assert_close(extrapolated[0], poses[0])
    pp.testing.assert_close(extrapolated[-1], poses[-1])


def check_point_tools(device: torch.device) -> None:
    dtype = torch.float64
    points = torch.tensor(
        [[0.0, 0.0, 0.0], [0.5, 0.0, 0.0], [0.0, 0.5, 0.0], [8.0, 8.0, 8.0]],
        dtype=dtype,
        device=device,
    )
    random_devices = [torch.cuda.current_device()] if device.type == "cuda" else []
    with torch.random.fork_rng(devices=random_devices):
        torch.manual_seed(7)
        sampled = pp.random_filter(points.unsqueeze(0), 3)
    assert sampled.shape == (1, 3, 3), sampled.shape

    voxel = pp.voxel_filter(points, [1.0, 1.0, 1.0])
    assert voxel.ndim == 2 and voxel.shape[1] == 3 and voxel.shape[0] == 2, voxel.shape

    filtered, mask = pp.nbr_filter(points, nbr=1, radius=1.0, return_mask=True)
    assert filtered.shape[0] == int(mask.sum()) and mask.shape == (4,), mask.shape

    smoothed = pp.knn_filter(points.unsqueeze(0), k=1)
    assert smoothed.shape == points.unsqueeze(0).shape, smoothed.shape
    values, indices = pp.knn(points[:2], points, k=1)
    assert values.shape == (2, 1) and indices.shape == (2, 1), (values.shape, indices.shape)


def make_trajectory(device: torch.device) -> tuple[torch.Tensor, pp.LieTensor]:
    dtype = torch.float64
    stamps = torch.arange(4, dtype=dtype, device=device)
    poses = pp.SE3(
        torch.tensor(
            [
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                [2.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
                [3.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            ],
            dtype=dtype,
            device=device,
        )
    )
    return stamps, poses


def check_trajectory_metrics(device: torch.device) -> None:
    stamps, poses = make_trajectory(device)
    reference = StampedSE3(stamps, poses)
    estimate = StampedSE3(stamps.clone(), poses.clone())
    assert reference.dtype == torch.float64
    assert reference.num_poses == 4

    ids_ref, ids_est = matching_time_indices(stamps, stamps.clone(), max_diff=1e-6)
    assert ids_ref == [0, 1, 2, 3] and ids_est == [0, 1, 2, 3]
    associated_ref, associated_est = associate_traj(reference, estimate, max_diff=1e-6)
    assert associated_ref.num_poses == associated_est.num_poses == 4

    ape = compute_error(associated_ref, associated_est, output="translation", mtype="ape", otype="All")
    rpe = compute_error(associated_ref, associated_est, output="translation", mtype="rpe", otype="All")
    assert set(ape) == {"Max", "Min", "Mean", "Median", "RMSE", "SSE", "STD"}
    assert set(rpe) == set(ape)
    for value in ape.values():
        pp.testing.assert_close(value, torch.zeros_like(value))
    for value in rpe.values():
        pp.testing.assert_close(value, torch.zeros_like(value))

    assert torch.equal(
        pp.metric.ape(stamps, poses, stamps, poses, etype="translation", otype="Mean"),
        torch.tensor(0.0, dtype=torch.float64, device=device),
    )
    assert torch.equal(
        pp.metric.rpe(stamps, poses, stamps, poses, etype="translation", otype="Mean"),
        torch.tensor(0.0, dtype=torch.float64, device=device),
    )


def check_stepper() -> None:
    stepper = pp.utils.ReduceToBason(steps=3, patience=2, tol=1e-12)
    while stepper.continual():
        stepper.step(1.0)
    assert stepper.steps == 3
    stepper.reset()
    assert stepper.continual() and stepper.steps == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run deterministic offline PyPose geometry checks.")
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Torch device for tensor checks (default: cpu).",
    )
    parser.add_argument("--verbose", action="store_true", help="Print each completed check.")
    args = parser.parse_args()
    if args.device == "cuda" and not torch.cuda.is_available():
        parser.error("--device cuda requested, but CUDA is unavailable")
    device = torch.device(args.device)

    checks = (
        ("projection and rigid fit", lambda: check_projection(device)),
        ("splines", lambda: check_splines(device)),
        ("point tools", lambda: check_point_tools(device)),
        ("trajectory metrics", lambda: check_trajectory_metrics(device)),
        ("stepper", check_stepper),
    )
    for name, check in checks:
        check()
        if args.verbose:
            print(f"ok: {name}")
    print(f"geometry smoke checks passed on {device}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
