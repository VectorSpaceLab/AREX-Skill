#!/usr/bin/env python3
"""Tiny PhysicsNeMo mesh smoke.

Builds a three-point triangle mesh, validates it, prints quality metrics, and
optionally moves it to CUDA when available.
"""

from __future__ import annotations

import argparse
import json

import torch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cuda", action="store_true", help="Move the tiny mesh to CUDA if available.")
    args = parser.parse_args()

    from physicsnemo.mesh import Mesh
    from physicsnemo.mesh.validation import compute_quality_metrics, validate_mesh

    points = torch.tensor(
        [[0.0, 0.0], [1.0, 0.0], [0.5, 1.0]],
        dtype=torch.float32,
    )
    cells = torch.tensor([[0, 1, 2]], dtype=torch.int64)
    mesh = Mesh(points=points, cells=cells)
    if args.cuda and torch.cuda.is_available():
        mesh = mesh.to("cuda")

    validation = validate_mesh(mesh, raise_on_error=False)
    quality = compute_quality_metrics(mesh)
    payload = {
        "device": str(mesh.points.device),
        "manifold_dim": mesh.n_manifold_dims,
        "spatial_dim": mesh.n_spatial_dims,
        "validation": dict(validation),
        "quality_keys": list(quality.keys()) if hasattr(quality, "keys") else None,
        "quality_repr": str(quality),
    }
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
