#!/usr/bin/env python3
"""Tiny ANTsPy image-core smoke check.

Usage:
    python antspy_image_smoke.py
    python antspy_image_smoke.py --verbose

The script uses only tiny in-memory arrays. It validates import, from_numpy,
metadata setters/getters, NumPy copy semantics, new_image_like/from_numpy_like,
allclose, physical-space consistency, pixeltype casting, and vector component
layout without relying on source-repository files.
"""

from __future__ import annotations

import argparse
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny deterministic ANTsPy ANTsImage smoke check."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print image properties as checks run.",
    )
    return parser.parse_args()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    args = parse_args()

    try:
        import numpy as np
        import ants
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"Failed to import numpy/ants: {exc}", file=sys.stderr)
        return 2

    arr = np.arange(12, dtype="float32").reshape(3, 4)
    origin = (10.0, 20.0)
    spacing = (0.5, 0.75)
    direction = np.eye(2)
    img = ants.from_numpy(arr, origin=origin, spacing=spacing, direction=direction)

    require(ants.is_image(img), "from_numpy did not return an ANTsImage")
    require(img.shape == arr.shape, "shape mismatch")
    require(img.dimension == 2, "dimension mismatch")
    require(img.origin == origin, "origin mismatch")
    require(img.spacing == spacing, "spacing mismatch")
    require(np.allclose(img.direction, direction), "direction mismatch")
    require(img.pixeltype == "float", "expected float pixeltype")

    copied = img.numpy()
    copied[:] = -1
    require(not np.allclose(img.numpy(), copied), "numpy() unexpectedly mutated image")

    doubled = img.new_image_like(img.numpy() * 2.0)
    require(
        ants.image_physical_space_consistency(img, doubled),
        "new_image_like did not preserve physical space",
    )
    require(np.allclose(doubled.numpy(), arr * 2.0), "new_image_like data mismatch")
    require(ants.allclose(doubled, img + img), "allclose failed for equivalent images")

    liked = ants.from_numpy_like(img.numpy() + 1.0, img)
    require(
        ants.image_physical_space_consistency(img, liked),
        "from_numpy_like did not preserve physical space",
    )

    mismatched = ants.from_numpy(img.numpy())
    require(
        not ants.image_physical_space_consistency(img, mismatched),
        "default from_numpy unexpectedly matched non-default physical space",
    )
    repaired = ants.copy_image_info(img, mismatched)
    require(
        ants.image_physical_space_consistency(img, repaired),
        "copy_image_info did not repair matching-grid metadata",
    )

    cast = img.clone("unsigned char")
    require(cast.pixeltype == "unsigned char", "clone pixeltype cast failed")
    require(
        ants.image_physical_space_consistency(img, cast),
        "clone did not preserve physical space",
    )
    require(
        ants.image_physical_space_consistency(img, cast, datatype=False),
        "datatype=False consistency failed after cast",
    )
    require(
        not ants.image_physical_space_consistency(img, cast, datatype=True),
        "datatype=True should detect pixeltype mismatch",
    )

    vec_arr = np.zeros((3, 4, 2), dtype="float32")
    vec_arr[..., 0] = 1.0
    vec_arr[..., 1] = 2.0
    vec = ants.from_numpy(
        vec_arr,
        origin=origin,
        spacing=spacing,
        direction=direction,
        has_components=True,
    )
    require(vec.has_components, "vector image missing components")
    require(vec.dimension == 2, "vector image spatial dimension mismatch")
    require(vec.components == 2, "vector component count mismatch")
    require(vec.numpy().shape == vec_arr.shape, "vector numpy shape mismatch")
    require(np.allclose(vec.numpy()[..., 1], 2.0), "vector channel order mismatch")

    if args.verbose:
        print(img)
        print("vector:", vec.shape, vec.dimension, vec.components, vec.pixeltype)

    print("ANTsPy image-core smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
