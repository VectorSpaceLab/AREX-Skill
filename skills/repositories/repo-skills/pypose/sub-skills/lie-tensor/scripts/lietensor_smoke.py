#!/usr/bin/env python3
"""Deterministic PyPose LieTensor smoke check.

Nearest skill contract: ../SKILL.md

This helper intentionally uses only tiny in-memory fixtures. It performs no
external-data access, file writes, or optimization.
"""

from __future__ import annotations

import argparse
import sys
from typing import Final

import torch


DTYPES: Final = {
    "float32": torch.float32,
    "float64": torch.float64,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic Exp/Log, point-action, matrix-conversion, "
            "batching, and autograd checks for PyPose LieTensor."
        )
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Torch device for the smoke check (default: cpu).",
    )
    parser.add_argument(
        "--dtype",
        choices=tuple(DTYPES),
        default="float64",
        help="Floating dtype (default: float64).",
    )
    return parser.parse_args()


def close_tolerance(dtype: torch.dtype) -> tuple[float, float]:
    if dtype == torch.float32:
        return 2e-5, 2e-6
    return 2e-8, 2e-9


def require_finite(name: str, value: torch.Tensor) -> None:
    assert torch.isfinite(value).all().item(), f"{name} contains non-finite values"


def check_exp_log(device: torch.device, dtype: torch.dtype) -> None:
    """Check all four algebra/group pairs with their documented dimensions."""
    atol, rtol = close_tolerance(dtype)
    fixtures = (
        ("so3", pp.so3, pp.so3_type, [0.10, -0.20, 0.05]),
        ("se3", pp.se3, pp.se3_type, [0.10, -0.20, 0.05, 0.02, 0.03, -0.01]),
        ("sim3", pp.sim3, pp.sim3_type, [0.10, -0.20, 0.05, 0.02, 0.03, -0.01, 0.04]),
        ("rxso3", pp.rxso3, pp.rxso3_type, [0.02, 0.03, -0.01, 0.04]),
    )
    expected_groups = (pp.SO3_type, pp.SE3_type, pp.Sim3_type, pp.RxSO3_type)
    expected_dims = (3, 6, 7, 4)
    expected_embeddings = (4, 7, 8, 5)

    for (name, factory, algebra_type, values), group_type, local_dim, embedding in zip(
        fixtures, expected_groups, expected_dims, expected_embeddings
    ):
        data = torch.tensor(values, dtype=dtype, device=device)
        algebra = factory(data)
        assert algebra.ltype is algebra_type
        assert algebra.shape == (local_dim,)
        assert algebra.lshape == torch.Size([])
        group = algebra.Exp()
        assert group.ltype is group_type
        assert group.shape == (embedding,)
        assert group.lshape == torch.Size([])
        recovered = group.Log()
        torch.testing.assert_close(
            recovered.tensor(), algebra.tensor(), atol=atol, rtol=rtol
        )
        require_finite(f"{name}.Exp", group.tensor())
        require_finite(f"{name}.Log", recovered.tensor())


def check_point_action_and_gradient(device: torch.device, dtype: torch.dtype) -> None:
    """Check broadcast point action and gradient flow from algebra to a scalar."""
    xi_data = torch.tensor(
        [0.10, -0.05, 0.02, 0.01, -0.02, 0.03],
        dtype=dtype,
        device=device,
    ).requires_grad_()
    xi = pp.se3(xi_data)
    assert xi.ltype is pp.se3_type

    points = torch.tensor(
        [[0.30, -0.40, 2.00], [0.10, 0.20, 1.50]],
        dtype=dtype,
        device=device,
    )
    transformed = xi.Exp().Act(points)
    assert transformed.shape == points.shape
    require_finite("point action", transformed)
    loss = transformed.square().mean()
    loss.backward()
    assert xi_data.grad is not None
    assert xi_data.grad.shape == xi_data.shape
    require_finite("algebra gradient", xi_data.grad)

    # A single SO3 group broadcasts over a batch of Euclidean points.
    rotation = pp.identity_SO3(device=device, dtype=dtype)
    rotated = rotation @ points
    assert rotated.shape == points.shape
    torch.testing.assert_close(rotated, points, atol=close_tolerance(dtype)[0], rtol=close_tolerance(dtype)[1])

    homogeneous = torch.cat(
        [points, torch.ones((*points.shape[:-1], 1), dtype=dtype, device=device)],
        dim=-1,
    )
    acted_homogeneous = xi.Exp() @ homogeneous
    assert acted_homogeneous.shape == homogeneous.shape
    torch.testing.assert_close(
        acted_homogeneous[..., -1], homogeneous[..., -1],
        atol=close_tolerance(dtype)[0], rtol=close_tolerance(dtype)[1],
    )


def check_conversion_and_batching(device: torch.device, dtype: torch.dtype) -> None:
    """Check mat2SE3 validation, differentiability, and typed batch behavior."""
    atol, rtol = close_tolerance(dtype)
    T = torch.eye(4, dtype=dtype, device=device)
    T[:3, 3] = torch.tensor([0.20, -0.30, 0.40], dtype=dtype, device=device)
    T.requires_grad_()

    pose = pp.mat2SE3(T, check=True, rtol=1e-5, atol=1e-5)
    assert pose.ltype is pp.SE3_type
    assert pose.shape == (7,)
    torch.testing.assert_close(
        pose.translation(), T[:3, 3], atol=atol, rtol=rtol
    )
    torch.testing.assert_close(pose.matrix(), T, atol=atol, rtol=rtol)
    conversion_loss = pose.translation().square().sum()
    conversion_loss.backward()
    assert T.grad is not None
    require_finite("matrix-conversion gradient", T.grad)

    batch = pp.randn_SE3(2, 3, sigma=0.05, dtype=dtype, device=device)
    assert batch.lshape == torch.Size((2, 3))
    assert batch.shape == (2, 3, 7)
    algebra_batch = batch.Log()
    assert algebra_batch.ltype is pp.se3_type
    assert algebra_batch.shape == (2, 3, 6)
    recovered_batch = algebra_batch.Exp()
    torch.testing.assert_close(
        recovered_batch.tensor(), batch.tensor(), atol=atol, rtol=rtol
    )


def main() -> int:
    args = parse_args()
    try:
        import pypose as pp  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - environment diagnostic
        raise SystemExit(
            "Unable to import pypose. Install the public package and PyTorch "
            "before running this smoke check."
        ) from exc

    # The check functions intentionally use the imported public module. Keeping
    # the import after argparse makes --help useful in an unprepared environment.
    globals()["pp"] = pp
    device = torch.device(args.device)
    dtype = DTYPES[args.dtype]

    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda was requested, but CUDA is unavailable")

    torch.manual_seed(1234)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(1234)

    check_exp_log(device, dtype)
    check_point_action_and_gradient(device, dtype)
    check_conversion_and_batching(device, dtype)
    print(f"LieTensor smoke passed: device={device}, dtype={args.dtype}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, RuntimeError, ValueError) as exc:
        print(f"LieTensor smoke failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
