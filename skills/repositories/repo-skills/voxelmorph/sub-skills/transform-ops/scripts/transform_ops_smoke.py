#!/usr/bin/env python3
"""Deterministic smoke checks for VoxelMorph PyTorch transform operations.

The script uses tiny synthetic tensors only. It does not download data, read
checkpoints, train models, or write output files.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Sequence

import numpy as np
import torch


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic VoxelMorph transform-operation smoke checks on "
            "tiny synthetic tensors."
        )
    )
    parser.add_argument(
        "--dim",
        type=int,
        choices=(2, 3),
        default=2,
        help="Spatial dimensionality to check (default: 2).",
    )
    parser.add_argument(
        "--shape",
        type=int,
        nargs="*",
        default=None,
        help=(
            "Optional spatial shape. Provide exactly --dim integers. Defaults "
            "to 8 12 for 2D or 5 6 7 for 3D."
        ),
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=2,
        help="Scaling-and-squaring integration steps for nonzero checks (default: 2).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Seed for both NumPy and PyTorch RNGs (default: 13).",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help="Torch device, for example cpu or cuda (default: cpu).",
    )
    parser.add_argument(
        "--atol",
        type=float,
        default=1e-5,
        help="Absolute tolerance for equality checks (default: 1e-5).",
    )
    return parser.parse_args(argv)


def _shape(args: argparse.Namespace) -> tuple[int, ...]:
    if args.shape is None or len(args.shape) == 0:
        return (8, 12) if args.dim == 2 else (5, 6, 7)
    if len(args.shape) != args.dim:
        raise SystemExit(f"--shape must contain exactly {args.dim} integers")
    if any(s < 4 for s in args.shape):
        raise SystemExit("all --shape values must be at least 4 for the smoke checks")
    return tuple(args.shape)


def _allclose(a: torch.Tensor, b: torch.Tensor, *, atol: float, msg: str) -> None:
    if not torch.allclose(a, b, atol=atol, rtol=0):
        diff = (a - b).abs().max().item()
        raise AssertionError(f"{msg}: max abs diff {diff:.6g}")


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        raise AssertionError(msg)


def _interior_slices(ndim: int) -> tuple[slice, ...]:
    return (slice(None),) + (slice(2, -2),) * ndim


def run_checks(args: argparse.Namespace) -> None:
    import voxelmorph as vxm
    import voxelmorph.nn.functional as vxf
    from voxelmorph.nn.modules import (
        IntegrateVelocityField,
        ResizeDisplacementField,
        SpatialTransformer,
    )

    spatial_shape = _shape(args)
    ndim = len(spatial_shape)
    device = torch.device(args.device)
    if device.type == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested, but torch.cuda.is_available() is false")

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    # Affine construction and affine-to-displacement conversion.
    identity = torch.eye(ndim + 1, dtype=torch.float32, device=device)
    zero_disp = vxm.affine_to_disp(identity, shape=spatial_shape)
    _assert(zero_disp.shape == (ndim, *spatial_shape), "identity affine displacement shape")
    _allclose(zero_disp, torch.zeros_like(zero_disp), atol=args.atol, msg="identity affine")

    translation = torch.arange(1, ndim + 1, dtype=torch.float32, device=device)
    affine = vxm.params_to_affine(ndim=ndim, translation=translation, device=device)
    trans_disp = vxm.affine_to_disp(affine, shape=spatial_shape, origin_at_center=False)
    expected = translation.view(ndim, *([1] * ndim)).expand_as(trans_disp)
    _allclose(trans_disp, expected, atol=args.atol, msg="translation affine displacement")

    # Displacement <-> transformation-field conversions and normalized coords.
    field = torch.randn(ndim, *spatial_shape, device=device) * 0.03
    trf = vxm.disp_to_trf(field)
    recovered = vxm.trf_to_disp(trf)
    _allclose(field, recovered, atol=args.atol, msg="disp/trf round trip")

    coords = vxm.disp_to_coords(torch.zeros_like(field))
    _assert(coords.shape == field.shape, "disp_to_coords shape")
    _assert(torch.isfinite(coords).all().item(), "disp_to_coords finite values")
    try:
        vxm.coords_to_disp(coords)
    except NotImplementedError:
        pass
    else:
        raise AssertionError("coords_to_disp should raise NotImplementedError")

    # Spatial warping via top-level and nn.functional APIs.
    image = torch.randn(1, *spatial_shape, device=device)
    warped_identity = vxm.spatial_transform(image, torch.zeros_like(field), non_spatial_dims=(0,))
    _allclose(image, warped_identity, atol=5e-5, msg="top-level zero warp")

    batch_image = torch.randn(2, 1, *spatial_shape, device=device)
    batch_field = torch.zeros(2, ndim, *spatial_shape, device=device)
    warped_batch = vxf.spatial_transform(batch_image, batch_field)
    _allclose(batch_image, warped_batch, atol=5e-5, msg="nn.functional zero warp")

    # Scaling-and-squaring integration.
    _allclose(vxm.integrate_disp(field, steps=0), field, atol=args.atol, msg="zero-step integration")
    integrated = vxm.integrate_disp(field, steps=args.steps)
    _assert(integrated.shape == field.shape, "integrated field shape")
    _assert(torch.isfinite(integrated).all().item(), "integrated field finite values")

    # Resize and magnitude scaling.
    ones = torch.ones(ndim, *spatial_shape, device=device)
    resized = vxm.resize_disp(ones, scale_factor=2.0)
    _assert(resized.shape == (ndim, *[s * 2 for s in spatial_shape]), "resize_disp shape")
    _allclose(resized, torch.full_like(resized, 2.0), atol=args.atol, msg="resize_disp magnitude")

    # Dense composition: constant displacements add in the interior.
    disp_a = torch.zeros_like(ones)
    disp_b = torch.zeros_like(ones)
    disp_a[0] = 1.0
    disp_b[min(1, ndim - 1)] = 1.0
    composed = vxm.compose([disp_a, disp_b])
    expected_comp = disp_a + disp_b
    interior = _interior_slices(ndim)
    _allclose(composed[interior], expected_comp[interior], atol=1e-4, msg="dense compose interior")

    # Random helpers with deterministic settings.
    random_affine = vxm.random_affine(ndim=ndim, max_translation=1.0, max_rotation=0.0,
                                      max_scaling=1.0, sampling=False, device=device)
    _assert(random_affine.shape == (ndim + 1, ndim + 1), "random_affine shape")
    random_transform = vxm.random_transform(
        shape=spatial_shape,
        affine_probability=1.0,
        warp_probability=0.0,
        max_translation=1.0,
        max_rotation=0.0,
        max_scaling=1.0,
        sampling=False,
        device=device,
    )
    _assert(random_transform.shape == (ndim, *spatial_shape), "random_transform shape")

    # Module wrappers.
    transformer = SpatialTransformer(interpolation_mode="linear")
    module_warped = transformer(batch_image, batch_field)
    _allclose(batch_image, module_warped, atol=5e-5, msg="SpatialTransformer zero warp")

    integrator = IntegrateVelocityField(steps=0)
    _allclose(integrator(batch_field), batch_field, atol=args.atol, msg="IntegrateVelocityField steps=0")

    resizer = ResizeDisplacementField(scale_factor=2.0, interpolation_mode="linear")
    module_resized = resizer(torch.ones(1, ndim, *spatial_shape, device=device))
    _assert(module_resized.shape == (1, ndim, *[s * 2 for s in spatial_shape]),
            "ResizeDisplacementField shape")
    _allclose(module_resized, torch.full_like(module_resized, 2.0),
              atol=args.atol, msg="ResizeDisplacementField magnitude")

    print(
        "PASS transform_ops_smoke",
        f"dim={ndim}",
        f"shape={spatial_shape}",
        f"device={device}",
        f"torch={torch.__version__}",
        f"voxelmorph={getattr(vxm, '__version__', 'unknown')}",
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.steps < 0:
        raise SystemExit("--steps must be nonnegative")
    try:
        run_checks(args)
    except Exception as exc:  # noqa: BLE001 - keep CLI failure concise.
        print(f"FAIL transform_ops_smoke: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
