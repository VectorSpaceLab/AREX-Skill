#!/usr/bin/env python3
"""Small deterministic CPU smoke checks for the public utility layer.

This helper uses seven real synthetic points plus one padded point so the
package's torch MDS implementation has enough columns for its default
low-rank SVD. It never downloads data, invokes a model, runs native tests, or
uses CUDA. Missing scientific imports are reported as an actionable skip.
"""
from __future__ import annotations

import math
import sys

try:
    import torch
    from alphafold2_pytorch.utils import MDScaling, Kabsch, GDT, TMscore
    from alphafold2_pytorch.utils import center_distogram_torch
except Exception as exc:
    print(
        "SKIP: alphafold2_pytorch.utils is unavailable; install the compatible "
        "torch and scientific utility dependencies. "
        f"Original error: {type(exc).__name__}: {exc}"
    )
    raise SystemExit(0)


def assert_finite(name: str, value: torch.Tensor) -> None:
    if not torch.isfinite(value).all():
        raise AssertionError(f"{name} contains non-finite values")


def main() -> None:
    torch.manual_seed(7)
    torch.set_default_dtype(torch.float32)
    device = torch.device("cpu")

    # Seven real points plus one padded point. The torch implementation calls
    # svd_lowrank with its default rank, so retain at least six active columns.
    real = torch.tensor(
        [
            [0.0, 0.0, 0.0],
            [1.5, 0.0, 0.0],
            [1.5, 1.2, 0.0],
            [0.0, 1.2, 0.8],
            [0.4, 0.3, 1.7],
            [1.8, 0.4, 1.1],
            [0.8, 1.7, 0.9],
        ],
        device=device,
    )
    padded = torch.cat([real, torch.zeros(1, 3, device=device)], dim=0)
    distances = torch.cdist(padded, padded)
    bins = torch.linspace(2.0, 20.0, 37, device=device)
    bucket = torch.bucketize(distances, bins[:-1]).clamp(max=36)
    distogram = torch.nn.functional.one_hot(bucket, num_classes=37).float()

    central, weights = center_distogram_torch(
        distogram.unsqueeze(0), bins=bins, center="mean", wide="std"
    )
    central = central.nan_to_num(0.0)
    weights = weights.nan_to_num(0.0)
    total_points = padded.shape[0]
    diagonal = torch.arange(total_points, device=device)
    # Padding and diagonal pairs do not contribute to MDS.
    weights[:, -1, :] = 0.0
    weights[:, :, -1] = 0.0
    weights[:, diagonal, diagonal] = 0.0
    central[:, diagonal, diagonal] = 0.0
    central = 0.5 * (central + central.transpose(-1, -2))
    assert central.shape == (1, total_points, total_points)
    assert weights.shape == (1, total_points, total_points)
    assert_finite("central distances", central)
    assert_finite("MDS weights", weights)

    # Generic point cloud: mirror correction is off because no protein N/CA/C
    # masks are available for this synthetic fixture.
    coords, stress = MDScaling(
        central,
        weights=weights,
        iters=3,
        fix_mirror=False,
        verbose=0,
        backend="torch",
    )
    assert coords.shape == (1, 3, total_points), coords.shape
    assert stress.ndim == 2 and stress.shape[1] == 1
    assert_finite("MDS coordinates", coords)

    # Kabsch is source-tested in the unbatched (3,N) layout. The metric
    # wrappers add their own batch dimension around the same 2-D inputs.
    target = real.transpose(0, 1)
    angle = torch.tensor(0.35)
    rotation = torch.tensor(
        [
            [torch.cos(angle), -torch.sin(angle), 0.0],
            [torch.sin(angle), torch.cos(angle), 0.0],
            [0.0, 0.0, 1.0],
        ]
    )
    transformed = rotation @ target + torch.tensor([[2.0], [-1.0], [0.5]])
    aligned, target_centered = Kabsch(transformed, target)
    assert aligned.shape == target.shape == target_centered.shape
    assert_finite("aligned coordinates", aligned)
    gdt = GDT(aligned, target_centered, mode="TS", weights=[1, 1, 1, 1])
    tm = TMscore(aligned, target_centered)
    assert gdt.shape == (1,) and tm.shape == (1,)
    assert_finite("GDT", gdt)
    assert_finite("TM-score", tm)
    if not (math.isfinite(float(gdt[0])) and math.isfinite(float(tm[0]))):
        raise AssertionError("metric result is not finite")

    print("PASS: center_distogram_torch, MDScaling, Kabsch, GDT, TMscore")
    print(f"PASS: central={tuple(central.shape)} coords={tuple(coords.shape)}")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, RuntimeError) as exc:
        print(f"utility_smoke: check failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1)
