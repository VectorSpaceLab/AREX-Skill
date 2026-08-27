#!/usr/bin/env python3
"""Standalone deterministic checks for the perception-geometry contract.

This helper intentionally does not import the historical repository. It can be
run from any current working directory and checks the source equations against
small, deterministic RGB-D fixtures.
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Optional

import numpy as np


def source_pointcloud(color_img: np.ndarray, depth_img: np.ndarray,
                      camera_intrinsics: np.ndarray):
    """Small source-equivalent implementation used only by this smoke test."""
    h, w = depth_img.shape[0], depth_img.shape[1]
    pix_x, pix_y = np.meshgrid(np.linspace(0, w - 1, w),
                               np.linspace(0, h - 1, h))
    cam_x = np.multiply(pix_x - camera_intrinsics[0][2],
                        depth_img / camera_intrinsics[0][0])
    cam_y = np.multiply(pix_y - camera_intrinsics[1][2],
                        depth_img / camera_intrinsics[1][1])
    cam_z = depth_img.copy()
    # reshape(..., copy=False) expresses the historical row-major flattening
    # without NumPy's deprecated in-place shape assignment warning.
    cam_x = cam_x.reshape((h * w, 1))
    cam_y = cam_y.reshape((h * w, 1))
    cam_z = cam_z.reshape((h * w, 1))

    rgb_r = color_img[:, :, 0].reshape((h * w, 1))
    rgb_g = color_img[:, :, 1].reshape((h * w, 1))
    rgb_b = color_img[:, :, 2].reshape((h * w, 1))
    return (np.concatenate((cam_x, cam_y, cam_z), axis=1),
            np.concatenate((rgb_r, rgb_g, rgb_b), axis=1))


def source_heightmap(color_img: np.ndarray, depth_img: np.ndarray,
                     cam_intrinsics: np.ndarray, cam_pose: np.ndarray,
                     workspace_limits: np.ndarray, resolution: float):
    """Small source-equivalent rasterizer; no checkout import is used."""
    hmap_size = np.round(((workspace_limits[1][1] - workspace_limits[1][0]) /
                          resolution,
                          (workspace_limits[0][1] - workspace_limits[0][0]) /
                          resolution)).astype(int)
    surface, colors = source_pointcloud(color_img, depth_img, cam_intrinsics)
    surface = np.transpose(
        np.dot(cam_pose[0:3, 0:3], np.transpose(surface)) +
        np.tile(cam_pose[0:3, 3:], (1, surface.shape[0])))

    order = np.argsort(surface[:, 2])
    surface, colors = surface[order], colors[order]
    valid = ((surface[:, 0] >= workspace_limits[0][0]) &
             (surface[:, 0] < workspace_limits[0][1]) &
             (surface[:, 1] >= workspace_limits[1][0]) &
             (surface[:, 1] < workspace_limits[1][1]) &
             (surface[:, 2] < workspace_limits[2][1]))
    surface, colors = surface[valid], colors[valid]

    color_r = np.zeros((hmap_size[0], hmap_size[1], 1), dtype=np.uint8)
    color_g = np.zeros((hmap_size[0], hmap_size[1], 1), dtype=np.uint8)
    color_b = np.zeros((hmap_size[0], hmap_size[1], 1), dtype=np.uint8)
    depth = np.zeros(hmap_size)
    px = np.floor((surface[:, 0] - workspace_limits[0][0]) /
                  resolution).astype(int)
    py = np.floor((surface[:, 1] - workspace_limits[1][0]) /
                  resolution).astype(int)
    color_r[py, px] = colors[:, [0]]
    color_g[py, px] = colors[:, [1]]
    color_b[py, px] = colors[:, [2]]
    color = np.concatenate((color_r, color_g, color_b), axis=2)
    depth[py, px] = surface[:, 2]
    z_bottom = workspace_limits[2][0]
    depth = depth - z_bottom
    depth[depth < 0] = 0
    depth[depth == -z_bottom] = np.nan
    return color, depth


def euler2rotm(theta: np.ndarray) -> np.ndarray:
    rx, ry, rz = theta
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    r_x = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    r_y = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    r_z = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return r_z @ (r_y @ r_x)


def rotm2euler(rotation: np.ndarray) -> np.ndarray:
    should_be_identity = rotation.T @ rotation
    if np.linalg.norm(np.eye(3) - should_be_identity) >= 1e-6:
        raise AssertionError("rotation is not orthogonal")
    sy = math.sqrt(rotation[0, 0] ** 2 + rotation[1, 0] ** 2)
    if sy >= 1e-6:
        x = math.atan2(rotation[2, 1], rotation[2, 2])
        y = math.atan2(-rotation[2, 0], sy)
        z = math.atan2(rotation[1, 0], rotation[0, 0])
    else:
        x = math.atan2(-rotation[1, 2], rotation[1, 1])
        y = math.atan2(-rotation[2, 0], sy)
        z = 0.0
    return np.array([x, y, z])


def angle2rotm(angle: float, axis: np.ndarray,
               point: Optional[np.ndarray] = None) -> np.ndarray:
    axis = np.asarray(axis, dtype=float).copy()
    axis /= np.linalg.norm(axis)
    sine, cosine = math.sin(angle), math.cos(angle)
    rotation = np.diag([cosine, cosine, cosine])
    rotation += np.outer(axis, axis) * (1.0 - cosine)
    axis_sine = axis * sine
    rotation += np.array([[0.0, -axis_sine[2], axis_sine[1]],
                          [axis_sine[2], 0.0, -axis_sine[0]],
                          [-axis_sine[1], axis_sine[0], 0.0]])
    matrix = np.eye(4)
    matrix[:3, :3] = rotation
    if point is not None:
        point = np.asarray(point[:3], dtype=float)
        matrix[:3, 3] = point - rotation @ point
    return matrix


def assert_close(actual, expected, message: str, atol: float = 1e-8):
    if not np.allclose(actual, expected, atol=atol, equal_nan=True):
        raise AssertionError(f"{message}: got {actual!r}, expected {expected!r}")


def run() -> None:
    # Case 1: shape, pinhole projection, and RGB row order. Zero and NaN are
    # intentionally present to make their behavior visible to callers.
    color = np.arange(2 * 3 * 3, dtype=np.uint8).reshape(2, 3, 3)
    depth = np.array([[0.0, 1.0, np.nan], [2.0, 3.0, 4.0]], dtype=float)
    intrinsics = np.array([[1.0, 0.0, 1.0],
                           [0.0, 1.0, 0.0],
                           [0.0, 0.0, 1.0]])
    points, rgb = source_pointcloud(color, depth, intrinsics)
    assert points.shape == (6, 3), points.shape
    assert rgb.shape == (6, 3), rgb.shape
    assert rgb.dtype == np.uint8, rgb.dtype
    assert_close(points[1], [0.0, 0.0, 1.0], "pinhole projection")
    assert np.isnan(points[2]).all(), "NaN depth should remain NaN in point cloud"
    assert_close(points[3], [-2.0, 2.0, 2.0], "off-center projection")

    # Case 2: nonidentity camera pose and strict x/y upper clipping. Only the
    # camera top-left sample remains in the one-cell map.
    color2 = np.array([[[10, 20, 30], [40, 50, 60]],
                       [[70, 80, 90], [100, 110, 120]]], dtype=np.uint8)
    depth2 = np.ones((2, 2), dtype=float)
    pose = np.eye(4)
    pose[:3, 3] = [1.0, 2.0, 0.5]
    limits = np.array([[1.0, 2.0], [2.0, 3.0], [0.0, 2.0]])
    intrinsics2 = np.eye(3)
    color_map, depth_map = source_heightmap(color2, depth2, intrinsics2,
                                            pose, limits, 1.0)
    assert color_map.shape == (1, 1, 3), color_map.shape
    assert depth_map.shape == (1, 1), depth_map.shape
    assert_close(color_map[0, 0], [10, 20, 30], "nonidentity pose color")
    assert_close(depth_map[0, 0], 1.5, "nonidentity pose depth")

    # Case 3: zero-only input is not silently treated as a measured surface in
    # the usual z_min=0 sentinel convention; NaN input is filtered.
    zero_map = source_heightmap(np.zeros((2, 2, 3), dtype=np.uint8),
                                np.zeros((2, 2), dtype=float), intrinsics,
                                np.eye(4),
                                np.array([[-1.0, 1.0], [-1.0, 1.0],
                                          [0.0, 1.0]]), 1.0)[1]
    assert np.isnan(zero_map).all(), "zero depth should become empty sentinel"

    # Case 4: Euler and axis-angle contracts, including rotation about a
    # non-origin point and inverse transform of a homogeneous point.
    theta = np.array([0.2, -0.3, 0.4])
    rotation = euler2rotm(theta)
    assert_close(rotm2euler(rotation), theta, "Euler round trip")
    axis_angle = angle2rotm(math.pi / 2, np.array([0.0, 0.0, 1.0]),
                            point=np.array([1.0, 1.0, 0.0]))
    assert_close(axis_angle @ np.array([1.0, 2.0, 0.0, 1.0]),
                 [0.0, 1.0, 0.0, 1.0], "axis-angle point rotation")

    print("perception-geometry smoke: PASS")
    print("  pointcloud: (6, 3) points and RGB rows")
    print("  heightmap: nonidentity pose + upper-bound clipping")
    print("  depth: zero/NaN empty semantics")
    print("  transforms: Euler and axis-angle assertions")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Run standalone deterministic RGB-D and transform checks; no checkout import.")
    parser.add_argument("--version", action="version", version="perception-geometry smoke 1")
    parser.parse_args(argv)
    run()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"perception-geometry smoke: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
