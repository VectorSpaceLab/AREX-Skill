#!/usr/bin/env python3
"""Small, deterministic CPU-safe smoke check for IKPy's optional JAX backend.

The script intentionally builds its chain inline. It does not load a robot file,
use repository resources, or require a GPU.
"""

from __future__ import annotations

import argparse
import os
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare NumPy/JAX FK on a tiny inline IKPy chain; optionally run "
            "bounded JAX position IK."
        )
    )
    parser.add_argument(
        "--ik",
        action="store_true",
        help="also run bounded JAX position IK (default: FK parity only)",
    )
    parser.add_argument(
        "--max-nfev",
        type=int,
        default=50,
        help="finite SciPy IK evaluation limit when --ik is used (default: 50)",
    )
    parser.add_argument(
        "--lazy",
        action="store_true",
        help="defer JAX compilation until the first operation",
    )
    parser.add_argument(
        "--platform",
        choices=("cpu", "default"),
        default="cpu",
        help="use CPU JAX (default) or leave platform selection unchanged",
    )
    parser.add_argument(
        "--x64",
        action="store_true",
        help="request JAX float64 before importing JAX",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.max_nfev < 1:
        print("error: --max-nfev must be at least 1", file=sys.stderr)
        return 2

    # Set configuration before importing JAX. CPU is the portable, no-GPU
    # baseline; this does not imply that CUDA acceleration is unavailable.
    if args.platform == "cpu":
        os.environ["JAX_PLATFORMS"] = "cpu"
    if args.x64:
        os.environ["JAX_ENABLE_X64"] = "True"

    try:
        import ikpy
    except Exception as exc:  # pragma: no cover - environment-dependent
        print(f"IKPy is not importable in this environment: {exc}")
        return 0

    if not getattr(ikpy, "JAX_AVAILABLE", False):
        print("JAX is not installed or could not be imported; FK parity smoke skipped.")
        print("Install the optional dependency with: python -m pip install 'ikpy[jax]'")
        return 0

    try:
        import jax
        import numpy as np
        from ikpy.chain import Chain
        from ikpy.link import OriginLink, URDFLink
    except Exception as exc:  # pragma: no cover - environment-dependent
        print(f"JAX backend is unavailable in this environment: {exc}")
        return 0

    if args.platform == "cpu" and jax.default_backend() != "cpu":
        print(
            "error: requested CPU JAX, but the runtime selected "
            f"{jax.default_backend()!r}",
            file=sys.stderr,
        )
        return 1

    chain = Chain(
        [
            OriginLink(),
            URDFLink(
                name="tiny_revolute",
                origin_translation=np.array([0.5, 0.0, 0.0]),
                origin_orientation=np.zeros(3),
                rotation=np.array([0.0, 0.0, 1.0]),
                bounds=(-np.pi, np.pi),
                use_symbolic_matrix=False,
                joint_type="revolute",
            ),
            URDFLink(
                name="tiny_tip",
                origin_translation=np.array([0.2, 0.0, 0.0]),
                origin_orientation=np.zeros(3),
                bounds=(-np.inf, np.inf),
                use_symbolic_matrix=False,
                joint_type="fixed",
            ),
        ],
        active_links_mask=[False, True, False],
        name="jax_smoke_chain",
        jax_precompile=not args.lazy,
    )

    joints = np.array([0.0, 0.35, 0.0], dtype=float)
    fk_numpy = chain.forward_kinematics(joints, backend="numpy")
    fk_jax = chain.forward_kinematics(joints, backend="jax")
    np.testing.assert_allclose(fk_jax, fk_numpy, rtol=1e-5, atol=1e-5)

    full_numpy = chain.forward_kinematics(joints, full_kinematics=True, backend="numpy")
    full_jax = chain.forward_kinematics(joints, full_kinematics=True, backend="jax")
    if len(full_numpy) != len(full_jax):
        raise AssertionError("full FK returned a different number of frames")
    for index, (numpy_frame, jax_frame) in enumerate(zip(full_numpy, full_jax)):
        np.testing.assert_allclose(
            jax_frame,
            numpy_frame,
            rtol=1e-5,
            atol=1e-5,
            err_msg=f"full FK mismatch at link {index}",
        )

    print(f"JAX backend: {jax.default_backend()} ({jax.devices()})")
    print(f"FK parity: ok (rtol=1e-5, atol=1e-5; lazy={args.lazy})")

    if args.ik:
        target = fk_numpy.copy()
        result = chain.inverse_kinematics_frame(
            target,
            initial_position=np.zeros(len(chain.links), dtype=float),
            backend="jax",
            orientation_mode=None,
            no_position=False,
            scipy_method="trf",
            scipy_x_scale="jac",
            scipy_max_nfev=args.max_nfev,
            scipy_verbose=0,
        )
        achieved = chain.forward_kinematics(result, backend="jax")
        position_error = float(np.linalg.norm(achieved[:3, 3] - target[:3, 3]))
        if not np.isfinite(position_error) or position_error >= 1e-2:
            raise AssertionError(f"bounded JAX IK position error too high: {position_error}")
        print(f"bounded IK: ok (position_error={position_error:.3e})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
