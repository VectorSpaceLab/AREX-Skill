#!/usr/bin/env python3
"""Bounded ANTsPy registration and transform smoke test.

The default check uses tiny in-memory 2D images, a short translation
registration, transform application to an image and point set, and transform
object IO. It avoids downloads and avoids nonlinear SyN.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def make_blob(shape: tuple[int, int], center: tuple[float, float]):
    import numpy as np

    yy, xx = np.indices(shape, dtype=np.float32)
    squared_distance = (yy - center[0]) ** 2 + (xx - center[1]) ** 2
    return np.exp(-squared_distance / 18.0).astype(np.float32)


def affine_inverse_flags(transformlist) -> list[bool]:
    return [str(transform).endswith(".mat") for transform in transformlist]


def as_list(transformlist):
    if isinstance(transformlist, (list, tuple)):
        return list(transformlist)
    return [transformlist]


def run_smoke(verbose: bool = False, transform_only: bool = False) -> None:
    import ants
    import numpy as np
    import pandas as pd

    fixed = ants.from_numpy(
        make_blob((32, 32), (15.0, 15.0)),
        origin=(0.0, 0.0),
        spacing=(1.0, 1.0),
        direction=np.eye(2),
    )
    moving = ants.from_numpy(
        make_blob((32, 32), (17.0, 14.0)),
        origin=(0.0, 0.0),
        spacing=(1.0, 1.0),
        direction=np.eye(2),
    )

    with tempfile.TemporaryDirectory(prefix="antspy_registration_smoke_") as tmpdir:
        tmpdir_path = Path(tmpdir)

        if not transform_only:
            tx = ants.registration(
                fixed=fixed,
                moving=moving,
                type_of_transform="Translation",
                outprefix=str(tmpdir_path / "translation_"),
                aff_iterations=(30, 0, 0, 0),
                aff_shrink_factors=(1, 1, 1, 1),
                aff_smoothing_sigmas=(0, 0, 0, 0),
                aff_random_sampling_rate=1.0,
                singleprecision=True,
                verbose=verbose,
            )

            required_keys = {"warpedmovout", "warpedfixout", "fwdtransforms", "invtransforms"}
            missing = required_keys.difference(tx)
            if missing:
                raise RuntimeError(f"registration output missing keys: {sorted(missing)}")

            fwdtransforms = as_list(tx["fwdtransforms"])
            invtransforms = as_list(tx["invtransforms"])
            if not fwdtransforms or not invtransforms:
                raise RuntimeError("registration did not produce forward and inverse transforms")

            warped = ants.apply_transforms(
                fixed=fixed,
                moving=moving,
                transformlist=fwdtransforms,
                interpolator="linear",
                whichtoinvert=[False] * len(fwdtransforms),
            )
            if warped.shape != fixed.shape:
                raise RuntimeError(f"warped image shape {warped.shape} != fixed shape {fixed.shape}")

            points = pd.DataFrame({"x": [14.0], "y": [17.0]})
            moved_points = ants.apply_transforms_to_points(
                2,
                points,
                invtransforms,
                whichtoinvert=affine_inverse_flags(invtransforms),
            )
            if list(moved_points.columns[:2]) != ["x", "y"]:
                raise RuntimeError("transformed point DataFrame lost x/y coordinate columns")

        transform = ants.create_ants_transform(
            transform_type="AffineTransform",
            dimension=2,
            translation=(1.0, -1.0),
        )
        transform_path = tmpdir_path / "manual_affine.mat"
        ants.write_transform(transform, str(transform_path))
        loaded = ants.read_transform(str(transform_path))
        transformed_point = loaded.apply_to_point((2.0, 3.0))
        if len(transformed_point) != 2:
            raise RuntimeError("loaded transform did not return a 2D point")

    print("ANTsPy registration smoke passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a bounded ANTsPy registration/transform smoke test on tiny in-memory images."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose backend output from registration and transform application.",
    )
    parser.add_argument(
        "--transform-only",
        action="store_true",
        help="Skip registration and check only transform object create/write/read/apply behavior.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    run_smoke(verbose=args.verbose, transform_only=args.transform_only)


if __name__ == "__main__":
    main()
