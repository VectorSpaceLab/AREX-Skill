#!/usr/bin/env python3
"""Small PhiFlow scene / field round-trip smoke test.

This helper creates a temporary scene, writes a couple of simple fields,
reads them back through both the Scene API and field.read(), and removes the
scene afterwards.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile

from phi.flow import *  # noqa: F403,F401 - standard PhiFlow import for field demos
from phi import field


def build_sample_fields(resolution: int):
    smoke = CenteredGrid(  # noqa: F405
        1,
        extrapolation.BOUNDARY,  # noqa: F405
        x=resolution,
        y=resolution,
    )
    velocity = StaggeredGrid(  # noqa: F405
        (2, 0),
        extrapolation.ZERO,  # noqa: F405
        x=resolution,
        y=resolution,
    )
    return smoke, velocity


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a small PhiFlow scene round-trip smoke test.")
    parser.add_argument("--resolution", type=int, default=16, help="Grid resolution per axis (default: 16).")
    args = parser.parse_args(argv)

    if args.resolution <= 1:
        parser.error("--resolution must be greater than 1")

    with tempfile.TemporaryDirectory(prefix="phiflow-scene-") as tmp:
        scene = Scene.create(tmp)  # noqa: F405
        smoke, velocity = build_sample_fields(args.resolution)
        scene.write(smoke=smoke, velocity=velocity)

        smoke_read = scene.read("smoke")
        velocity_read = scene.read("velocity")
        field.assert_close(smoke, smoke_read)
        field.assert_close(velocity, velocity_read)

        smoke_npz = field.read(os.path.join(scene.path, "smoke_000000.npz"))
        velocity_npz = field.read(os.path.join(scene.path, "velocity_000000.npz"))
        field.assert_close(smoke, smoke_npz)
        field.assert_close(velocity, velocity_npz)

        print(f"scene round-trip ok: {scene.path}")
        print(f"scene field names: {scene.fieldnames}")
        print(f"scene frames: {scene.frames}")
        scene.remove()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
