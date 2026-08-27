#!/usr/bin/env python3
"""Check tiny image/Perlin maps, downsampling, fog, and grid collision."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import warnings
from pathlib import Path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Exercise IR-SIM occupancy-map APIs with generated tiny fixtures."
    )
    parser.add_argument("--seed", type=int, default=7, help="Perlin seed (default: 7).")
    return parser


def main() -> int:
    args = _parser().parse_args()
    os.environ.setdefault("MPLBACKEND", "Agg")

    import matplotlib.image as mpimg
    import numpy as np
    from shapely.geometry import Point

    from irsim.world.map import (
        FogMap,
        PerlinGridGenerator,
        build_grid_from_generator,
        resolve_obstacle_map,
    )

    from irsim.world.world import World

    with tempfile.TemporaryDirectory(prefix="irsim-map-smoke-") as tmp:
        tmp_path = Path(tmp)
        image_path = tmp_path / "tiny.png"
        image = np.ones((3, 4), dtype=np.float64)
        image[1, 2] = 0.0  # one dark/occupied pixel
        mpimg.imsave(image_path, image, cmap="gray", vmin=0.0, vmax=1.0)
        image_grid = resolve_obstacle_map({"name": "image", "path": str(image_path)})
        if image_grid is None or image_grid.dtype != np.float64:
            raise AssertionError("image resolver did not produce float64 occupancy")

        perlin_grid = build_grid_from_generator(
            {"name": "perlin", "resolution": 0.5, "fill": 0.25, "seed": args.seed},
            world_width=4.0,
            world_height=3.0,
        )
        direct = PerlinGridGenerator(8, 6, fill=0.25, seed=args.seed).generate()
        if perlin_grid.shape != direct.grid.shape:
            raise AssertionError("YAML and direct Perlin dimensions disagree")

        # A deterministic one-cell obstacle proves the conservative planner-time
        # downsample and world-offset collision path without a source asset.
        fine = np.zeros((4, 3), dtype=np.float64)
        fine[0, 0] = 100.0
        world = World(width=4.0, height=3.0, offset=[-1.0, 2.0], obstacle_map=fine)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            env_map = world.get_map(resolution=2.0)
        if not caught or env_map.grid is None:
            raise AssertionError("coarser planner map did not report/downsample a grid")
        if env_map.grid_resolution != (2.0, 1.5):
            raise AssertionError("planner grid resolution does not match map dimensions")
        if not env_map.grid_occupied(0.0, 2.75):
            raise AssertionError("occupied coarse grid cell was not found")
        if not env_map.is_collision(Point(0.0, 2.75)):
            raise AssertionError("occupied coarse grid cell did not collide")

        fog = FogMap(width=4.0, height=3.0, resolution=1.0, world_offset=(-1.0, 2.0))
        fog.reveal_from_lidar([-0.5, 2.5, 0.0], [0.0], [1.0])
        if fog.explored_ratio <= 0.0:
            raise AssertionError("tiny LiDAR reveal did not update fog")
        ratio_before = fog.explored_ratio
        fog.reveal_fov([-0.5, 2.5, 0.0], 1.5707963267948966, 1.0)
        if fog.explored_ratio < ratio_before:
            raise AssertionError("FOV reveal reduced fog coverage")

        print(
            json.dumps(
                {
                    "image_shape": list(image_grid.shape),
                    "perlin_shape": list(perlin_grid.shape),
                    "planner_shape": list(env_map.grid.shape),
                    "planner_grid_resolution": list(env_map.grid_resolution),
                    "fog_shape": list(fog.shape),
                    "fog_explored_ratio": fog.explored_ratio,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
