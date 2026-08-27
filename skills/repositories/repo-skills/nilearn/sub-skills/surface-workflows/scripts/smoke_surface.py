#!/usr/bin/env python
"""No-network Nilearn surface object smoke test."""

from __future__ import annotations

import argparse


def _surface_api():
    import numpy as np
    from nilearn.maskers import SurfaceMasker
    from nilearn.surface import InMemoryMesh, PolyMesh, SurfaceImage

    return np, SurfaceMasker, InMemoryMesh, PolyMesh, SurfaceImage


def _triangle_mesh(np, InMemoryMesh, offset: float = 0.0):
    coordinates = np.asarray(
        [
            [offset + 0.0, 0.0, 0.0],
            [offset + 1.0, 0.0, 0.0],
            [offset + 0.0, 1.0, 0.0],
        ],
        dtype=np.float64,
    )
    faces = np.asarray([[0, 1, 2]], dtype=np.int32)
    return InMemoryMesh(coordinates=coordinates, faces=faces)


def build_surface_image(n_samples: int):
    """Build a tiny left/right SurfaceImage with deterministic data."""
    np, _, InMemoryMesh, PolyMesh, SurfaceImage = _surface_api()
    mesh = PolyMesh(
        left=_triangle_mesh(np, InMemoryMesh),
        right=_triangle_mesh(np, InMemoryMesh, offset=2.0),
    )
    left = np.arange(1, 1 + 3 * n_samples, dtype=np.float64).reshape(
        3, n_samples
    )
    right = left + 100.0
    return SurfaceImage(mesh=mesh, data={"left": left, "right": right})


def run_smoke(n_samples: int, use_masker: bool) -> None:
    _, SurfaceMasker, _, _, _ = _surface_api()
    img = build_surface_image(n_samples=n_samples)

    expected_shape = (6, n_samples)
    if img.shape != expected_shape:
        raise RuntimeError(
            f"Expected SurfaceImage shape {expected_shape}, got {img.shape}"
        )

    for part, mesh_part in img.mesh.parts.items():
        data_part = img.data.parts[part]
        if data_part.shape[0] != mesh_part.n_vertices:
            raise RuntimeError(
                f"{part} data has {data_part.shape[0]} rows for "
                f"{mesh_part.n_vertices} vertices"
            )

    print("surface-image-ok")
    print(f"shape={img.shape}")
    print(
        "vertices="
        + ",".join(
            f"{part}:{mesh_part.n_vertices}"
            for part, mesh_part in img.mesh.parts.items()
        )
    )

    if use_masker:
        masker = SurfaceMasker(standardize=False, reports=False).fit(img)
        signals = masker.transform(img)
        if signals.shape != (n_samples, 6):
            raise RuntimeError(
                "Expected masker signals shape "
                f"{(n_samples, 6)}, got {signals.shape}"
            )
        reconstructed = masker.inverse_transform(signals)
        if reconstructed.shape != img.shape:
            raise RuntimeError(
                "Inverse-transformed SurfaceImage shape mismatch: "
                f"{reconstructed.shape} != {img.shape}"
            )
        print("surface-masker-ok")
        print(f"signals_shape={signals.shape}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a tiny in-memory Nilearn SurfaceImage and optionally run "
            "SurfaceMasker transform/inverse_transform. No files, downloads, "
            "or plotting backends are required."
        )
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=2,
        help="Number of sample/time columns per hemisphere data array.",
    )
    parser.add_argument(
        "--skip-masker",
        action="store_true",
        help="Only validate SurfaceImage construction, not SurfaceMasker.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.n_samples < 1:
        raise SystemExit("--n-samples must be at least 1")
    run_smoke(n_samples=args.n_samples, use_masker=not args.skip_masker)


if __name__ == "__main__":
    main()
