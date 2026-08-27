#!/usr/bin/env python3
"""Tiny no-download Kornia geometry smoke test.

Exercises resize, affine/perspective warps, perspective-transform construction,
and a small camera projection/unprojection round trip. It intentionally avoids
pretrained models, datasets, optional dependencies, and file I/O.
"""

from __future__ import annotations

import argparse
import sys


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device to use. 'auto' selects CUDA when available, otherwise CPU.",
    )
    parser.add_argument(
        "--dtype",
        choices=("float32", "float64"),
        default="float32",
        help="Floating dtype for the smoke tensors.",
    )
    return parser.parse_args()


def _select_device(torch, requested: str):
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if requested == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested, but torch.cuda.is_available() is False")
    return torch.device(requested)


def _assert_finite(name: str, tensor) -> None:
    import torch

    if not torch.isfinite(tensor).all():
        raise AssertionError(f"{name} contains non-finite values")


def main() -> int:
    args = _parse_args()
    try:
        import torch
        import kornia
        from kornia.geometry.camera import PinholeCamera, project_points, unproject_points
        from kornia.geometry.transform import get_perspective_transform, get_rotation_matrix2d, resize, warp_affine
        from kornia.geometry.transform import warp_perspective
    except Exception as exc:  # pragma: no cover - diagnostic path for broken runtimes
        print(f"Failed to import torch/kornia geometry APIs: {exc}", file=sys.stderr)
        return 2

    device = _select_device(torch, args.device)
    dtype = getattr(torch, args.dtype)

    # Deterministic BCHW image with non-square spatial shape to catch H/W swaps.
    img = torch.arange(1 * 1 * 5 * 6, device=device, dtype=dtype).reshape(1, 1, 5, 6) / 30.0
    resized = resize(img, (3, 4), interpolation="bilinear", align_corners=False, antialias=False)
    assert resized.shape == (1, 1, 3, 4)
    _assert_finite("resized", resized)

    identity_affine = torch.eye(2, 3, device=device, dtype=dtype).unsqueeze(0)
    affine_identity = warp_affine(img, identity_affine, (5, 6), align_corners=True)
    assert affine_identity.shape == img.shape
    torch.testing.assert_close(affine_identity, img, atol=1e-5, rtol=1e-5)

    center = torch.tensor([[2.5, 2.0]], device=device, dtype=dtype)
    angle = torch.tensor([10.0], device=device, dtype=dtype)
    scale = torch.ones(1, 2, device=device, dtype=dtype)
    rotation = get_rotation_matrix2d(center, angle, scale)
    rotated = warp_affine(img, rotation, (5, 6), align_corners=True)
    assert rotated.shape == img.shape
    _assert_finite("rotated", rotated)

    H_img, W_img = img.shape[-2:]
    src_corners = torch.tensor(
        [[[0.0, 0.0], [W_img - 1.0, 0.0], [W_img - 1.0, H_img - 1.0], [0.0, H_img - 1.0]]],
        device=device,
        dtype=dtype,
    )
    dst_corners = src_corners.clone()
    homography = get_perspective_transform(src_corners, dst_corners)
    assert homography.shape == (1, 3, 3)
    _assert_finite("homography", homography)

    warped = warp_perspective(img, homography, (H_img, W_img), align_corners=True)
    assert warped.shape == img.shape
    torch.testing.assert_close(warped, img, atol=1e-5, rtol=1e-5)

    # PinholeCamera uses 4x4 intrinsics/extrinsics; standalone project/unproject use 3x3 K.
    intrinsics4 = torch.eye(4, device=device, dtype=dtype).unsqueeze(0)
    intrinsics4[:, 0, 0] = 4.0
    intrinsics4[:, 1, 1] = 4.0
    intrinsics4[:, 0, 2] = 2.5
    intrinsics4[:, 1, 2] = 2.0
    extrinsics4 = torch.eye(4, device=device, dtype=dtype).unsqueeze(0)
    camera = PinholeCamera(
        intrinsics4,
        extrinsics4,
        torch.tensor([float(H_img)], device=device, dtype=dtype),
        torch.tensor([float(W_img)], device=device, dtype=dtype),
    )
    assert camera.camera_matrix.shape == (1, 3, 3)
    assert camera.rt_matrix.shape == (1, 3, 4)

    points_3d = torch.tensor([[[0.0, 0.0, 2.0], [1.0, 0.0, 2.0], [0.0, 1.0, 4.0]]], device=device, dtype=dtype)
    K = camera.camera_matrix[:, None].expand(-1, points_3d.shape[1], -1, -1)
    pixels = project_points(points_3d, K)
    assert pixels.shape == (1, 3, 2)
    _assert_finite("pixels", pixels)
    reconstructed = unproject_points(pixels, points_3d[..., 2:3], K)
    torch.testing.assert_close(reconstructed, points_3d, atol=1e-5, rtol=1e-5)

    print(
        "geometry_smoke ok: "
        f"kornia={getattr(kornia, '__version__', 'unknown')} "
        f"device={device} dtype={dtype} "
        f"resize={tuple(resized.shape)} warp={tuple(warped.shape)} pixels={tuple(pixels.shape)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
