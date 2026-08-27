#!/usr/bin/env python3
"""Run deterministic, local-only invariants for nuPlan core geometry.

The helper performs no downloads, dataset reads, credential access, training,
or writes. Run it with the nuPlan package installed. Use ``--skip-torch`` to
check only state/NumPy APIs, or explicitly request ``--device cuda`` after a
CUDA runtime check.
"""

from __future__ import annotations

import argparse
import math
from typing import Callable, List


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check nuPlan pose, footprint, and tensor-geometry invariants."
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda"),
        default="cpu",
        help="Torch device for tensor checks (default: cpu; cuda is never implicit).",
    )
    parser.add_argument(
        "--skip-torch",
        action="store_true",
        help="Run state/NumPy checks only; useful without PyTorch.",
    )
    return parser.parse_args()


def _assert_close(actual: float, expected: float, tolerance: float = 1e-6) -> None:
    if not math.isclose(actual, expected, rel_tol=tolerance, abs_tol=tolerance):
        raise AssertionError(f"expected {expected}, got {actual}")


def _check_state_and_box() -> None:
    from nuplan.common.actor_state.car_footprint import CarFootprint
    from nuplan.common.actor_state.oriented_box import OrientedBoxPointType
    from nuplan.common.actor_state.state_representation import StateSE2
    from nuplan.common.actor_state.vehicle_parameters import get_pacifica_parameters
    from nuplan.common.geometry.compute import principal_value
    from nuplan.common.geometry.convert import matrix_from_pose, pose_from_matrix
    from nuplan.common.geometry.transform import translate_longitudinally_and_laterally

    pose = StateSE2(10.0, 4.0, 0.0)
    round_trip = pose_from_matrix(matrix_from_pose(pose))
    for actual, expected in zip(round_trip.serialize(), pose.serialize()):
        _assert_close(float(actual), float(expected))

    front_left = translate_longitudinally_and_laterally(pose, 2.0, 1.0).point
    _assert_close(front_left.x, 12.0)
    _assert_close(front_left.y, 5.0)

    vehicle = get_pacifica_parameters()
    footprint = CarFootprint.build_from_rear_axle(pose, vehicle)
    if footprint.rear_axle != pose:
        raise AssertionError("rear-axle construction did not round-trip")
    corner = footprint.corner(OrientedBoxPointType.FRONT_LEFT)
    _assert_close(corner.x, pose.x + vehicle.front_length)
    _assert_close(corner.y, pose.y + vehicle.half_width)

    wrapped = principal_value(2.0 * math.pi)
    _assert_close(float(wrapped), 0.0)


def _check_torch(device_name: str) -> None:
    import torch

    from nuplan.common.geometry.torch_geometry import (
        coordinates_to_local_frame,
        global_state_se2_tensor_to_local,
        state_se2_tensor_to_transform_matrix,
        state_se2_tensor_to_transform_matrix_batch,
        transform_matrix_to_state_se2_tensor_batch,
    )
    from nuplan.common.utils.torch_math import approximate_derivatives_tensor, unwrap

    if device_name == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("--device cuda was requested, but CUDA is unavailable")
    device = torch.device(device_name)
    dtype = torch.float64

    state = torch.tensor([2.0, 3.0, math.pi / 2.0], dtype=dtype, device=device)
    matrix = state_se2_tensor_to_transform_matrix(state, precision=dtype)
    if tuple(matrix.shape) != (3, 3) or matrix.device != state.device:
        raise AssertionError(f"unexpected single transform: {matrix.shape}, {matrix.device}")

    batch = state.unsqueeze(0)
    batch_matrix = state_se2_tensor_to_transform_matrix_batch(batch, precision=dtype)
    restored = transform_matrix_to_state_se2_tensor_batch(batch_matrix)
    if tuple(restored.shape) != (1, 3):
        raise AssertionError(f"unexpected restored batch shape: {restored.shape}")
    # The batch inverse returns a strided view into the matrix's third column;
    # stride is not part of this numerical invariant.
    torch.testing.assert_close(restored, batch, rtol=1e-6, atol=1e-6, check_stride=False)

    anchor = torch.tensor([5.0, 5.0, math.pi / 2.0], dtype=dtype, device=device)
    global_states = torch.tensor([[1.0, 1.0, 0.0]], dtype=dtype, device=device)
    local_states = global_state_se2_tensor_to_local(global_states, anchor, precision=dtype)
    torch.testing.assert_close(
        local_states,
        torch.tensor([[-4.0, 4.0, -math.pi / 2.0]], dtype=dtype, device=device),
        rtol=1e-6,
        atol=1e-6,
        check_stride=False,
    )

    coords = torch.tensor([[1.0, 1.0]], dtype=dtype, device=device)
    local_coords = coordinates_to_local_frame(coords, anchor, precision=dtype)
    torch.testing.assert_close(
        local_coords,
        torch.tensor([[-4.0, 4.0]], dtype=dtype, device=device),
        rtol=1e-6,
        atol=1e-6,
        check_stride=False,
    )

    if device_name == "cuda":
        # In the inspected package version, torch_math builds its Savitzky-
        # Golay coefficients and pi constant on CPU. Do not report those
        # helpers as CUDA-verified when the package itself cannot run them.
        print("NOTE torch_math derivative/unwrap checks skipped on cuda: the package uses CPU constants")
    else:
        x = torch.arange(5, dtype=dtype, device=device)
        y = torch.stack((x, x + 1.0))
        derivative = approximate_derivatives_tensor(y, x, window_length=3, poly_order=2, deriv_order=1)
        torch.testing.assert_close(derivative, torch.ones_like(y), rtol=1e-6, atol=1e-6)

        angles = torch.tensor([math.pi - 0.1, -math.pi + 0.1], dtype=dtype, device=device)
        unwrapped = unwrap(angles)
        if not bool(torch.all(torch.diff(unwrapped) > 0)):
            raise AssertionError(f"angle unwrap did not remove branch jump: {unwrapped}")


def main() -> int:
    args = _parse_args()
    checks: List[tuple[str, Callable[[], None]]] = [("state/box", _check_state_and_box)]
    if not args.skip_torch:
        checks.append((f"torch/{args.device}", lambda: _check_torch(args.device)))

    for name, check in checks:
        check()
        print(f"PASS {name}")
    print(f"All {len(checks)} geometry smoke checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
