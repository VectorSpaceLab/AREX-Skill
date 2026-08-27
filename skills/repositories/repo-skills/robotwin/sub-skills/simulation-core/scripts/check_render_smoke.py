#!/usr/bin/env python3
"""Minimal SAPIEN render bootstrap smoke check for RoboTwin.

This helper is self-contained and does not import the RoboTwin source tree. It
supports --help without SAPIEN installed, then imports SAPIEN only when running
the smoke test.
"""

from __future__ import annotations

import argparse
import math
import sys
from typing import Sequence

import numpy as np


def look_at_pose(sapien, eye: Sequence[float], target: Sequence[float]):
    eye_v = np.asarray(eye, dtype=np.float32)
    target_v = np.asarray(target, dtype=np.float32)
    forward = target_v - eye_v
    forward /= np.linalg.norm(forward)
    up_hint = np.asarray([0.0, 0.0, 1.0], dtype=np.float32)
    left = np.cross(up_hint, forward)
    if np.linalg.norm(left) < 1e-6:
        up_hint = np.asarray([0.0, 1.0, 0.0], dtype=np.float32)
        left = np.cross(up_hint, forward)
    left /= np.linalg.norm(left)
    up = np.cross(forward, left)
    mat = np.eye(4, dtype=np.float32)
    mat[:3, :3] = np.stack([forward, left, up], axis=1)
    mat[:3, 3] = eye_v
    return sapien.Pose(mat)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny SAPIEN render smoke test.")
    parser.add_argument("--width", type=int, default=320, help="Camera width in pixels.")
    parser.add_argument("--height", type=int, default=240, help="Camera height in pixels.")
    parser.add_argument("--steps", type=int, default=2, help="Number of simulation steps before capture.")
    args = parser.parse_args()

    try:
        import sapien.core as sapien
        from sapien.render import set_global_config
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"[simulation-core][ERROR] Could not import sapien: {exc}", file=sys.stderr)
        return 2

    try:
        set_global_config(max_num_materials=1024, max_num_textures=1024)
        engine = sapien.Engine()
        renderer = sapien.SapienRenderer()
        engine.set_renderer(renderer)
        scene = engine.create_scene(sapien.SceneConfig())
        scene.set_timestep(1.0 / 250.0)
        scene.add_ground(0.0)
        scene.default_physical_material = scene.create_physical_material(0.5, 0.5, 0.0)
        scene.set_ambient_light([0.4, 0.4, 0.4])
        scene.add_directional_light([0.0, -1.0, -1.0], [1.0, 1.0, 1.0])

        builder = scene.create_actor_builder()
        builder.set_physx_body_type("static")
        builder.add_box_collision(half_size=[0.04, 0.04, 0.04], material=scene.default_physical_material)
        builder.add_box_visual(
            pose=sapien.Pose(),
            half_size=[0.04, 0.04, 0.04],
            material=sapien.render.RenderMaterial(base_color=[0.2, 0.6, 0.9, 1.0]),
        )
        box = builder.build(name="smoke_box")
        box.set_pose(sapien.Pose([0.0, 0.0, 0.04]))

        camera = scene.add_camera(
            name="smoke_camera",
            width=args.width,
            height=args.height,
            fovy=math.radians(60.0),
            near=0.1,
            far=10.0,
        )
        camera.entity.set_pose(look_at_pose(sapien, [0.55, -0.55, 0.45], [0.0, 0.0, 0.05]))

        for _ in range(max(args.steps, 1)):
            scene.step()
            scene.update_render()
        camera.take_picture()
        color = camera.get_picture("Color")
        shape = getattr(color, "shape", None) or np.asarray(color).shape
        print(f"Render Well: actors={len(scene.get_all_actors())} camera=smoke_camera color_shape={shape}")
        return 0
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(f"[simulation-core][ERROR] Render smoke failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
