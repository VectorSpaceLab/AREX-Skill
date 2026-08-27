#!/usr/bin/env python3
"""Safe smoke test for Kaolin quaternion and transform helpers.

The script uses only installed Python packages. It does not read from a Kaolin
source checkout and can be run from any working directory.
"""

from __future__ import annotations

import argparse
import math
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-test kaolin.math.quat quaternion, matrix, Euclidean, and compact transform helpers."
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Device for the smoke tensors. Default: cpu.",
    )
    parser.add_argument(
        "--dtype",
        choices=("float32", "float64"),
        default="float32",
        help="Floating dtype for the smoke tensors. Default: float32.",
    )
    return parser.parse_args()


def _resolve_dtype(torch, name: str):
    return {"float32": torch.float32, "float64": torch.float64}[name]


def _tolerance(dtype) -> tuple[float, float]:
    if str(dtype).endswith("float64"):
        return 1e-8, 1e-8
    return 1e-5, 1e-5


def run_smoke(device_name: str, dtype_name: str) -> None:
    try:
        import torch
        from kaolin.math import quat as quat_ops
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise SystemExit(
            "Unable to import torch and kaolin.math.quat. Install Kaolin and its base dependencies first. "
            f"Original error: {exc}"
        ) from exc

    if device_name == "cuda" and not torch.cuda.is_available():
        raise SystemExit("CUDA was requested but torch.cuda.is_available() is false.")

    device = torch.device(device_name)
    dtype = _resolve_dtype(torch, dtype_name)
    atol, rtol = _tolerance(dtype)
    torch.manual_seed(0)

    # Build two non-degenerate xyzw quaternions from angle-axis inputs.
    angles = torch.tensor([[math.pi / 2.0], [0.75]], device=device, dtype=dtype)
    axes = torch.tensor([[0.0, 0.0, 1.0], [1.0, 2.0, 3.0]], device=device, dtype=dtype)
    quats = quat_ops.quat_unit_positive(quat_ops.quat_from_angle_axis(angles, axes))

    norms = quat_ops.quat_abs(quats)
    torch.testing.assert_close(norms, torch.ones_like(norms), atol=atol, rtol=rtol)

    identity = quat_ops.quat_identity([2], device=device).to(dtype)
    expected_identity = torch.tensor(
        [[0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0]], device=device, dtype=dtype
    )
    torch.testing.assert_close(identity, expected_identity, atol=atol, rtol=rtol)

    rot33 = quat_ops.rot33_from_quat(quats)
    if not quat_ops.is_rot33_valid(rot33, atol=max(atol, 1e-6)):
        raise AssertionError("rot33_from_quat produced a matrix that is not a valid rotation.")

    quats_from_rot = quat_ops.quat_unit_positive(quat_ops.quat_from_rot33(rot33))
    torch.testing.assert_close(quats_from_rot, quats, atol=atol, rtol=rtol)

    roundtrip_angles, roundtrip_axes = quat_ops.angle_axis_from_quat(quats)
    quats_from_angle_axis = quat_ops.quat_unit_positive(
        quat_ops.quat_from_angle_axis(roundtrip_angles, roundtrip_axes)
    )
    torch.testing.assert_close(quats_from_angle_axis, quats, atol=atol, rtol=rtol)

    translation = torch.tensor([[1.0, -2.0, 0.5]], device=device, dtype=dtype)
    compact_transform = quat_ops.transform_from_rotation_translation(quats[:1], translation)
    point = torch.tensor([[0.25, -0.5, 1.25]], device=device, dtype=dtype)
    transformed = quat_ops.transform_apply(compact_transform, point)
    recovered = quat_ops.transform_apply(quat_ops.transform_inverse(compact_transform), transformed)
    torch.testing.assert_close(recovered, point, atol=atol, rtol=rtol)

    euclidean = quat_ops.euclidean_from_rotation_translation(r=quats[:1], t=translation)
    if not quat_ops.is_euclidean_valid(euclidean, throw=False):
        raise AssertionError("euclidean_from_rotation_translation produced an invalid Euclidean matrix.")
    compact_from_euclidean = quat_ops.transform_from_euclidean(euclidean)
    transformed_from_euclidean = quat_ops.transform_apply(compact_from_euclidean, point)
    torch.testing.assert_close(transformed_from_euclidean, transformed, atol=atol, rtol=rtol)

    rot44 = quat_ops.rot44_from_quat(quats[:1])
    if tuple(rot44.shape) != (1, 4, 4):
        raise AssertionError(f"Expected rot44 shape (1, 4, 4), got {tuple(rot44.shape)}")

    print(
        "PASS quaternion smoke: "
        f"device={device}, dtype={dtype}, max_roundtrip_error={(quats_from_rot - quats).abs().max().item():.3e}"
    )


def main() -> int:
    args = parse_args()
    run_smoke(args.device, args.dtype)
    return 0


if __name__ == "__main__":
    sys.exit(main())
