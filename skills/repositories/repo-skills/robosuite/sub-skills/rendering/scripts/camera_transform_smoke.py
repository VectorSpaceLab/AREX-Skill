#!/usr/bin/env python
"""Tiny Lift/Panda camera projection and backprojection smoke test.

This helper mirrors the verified camera transform test: it projects the lifted object into
pixel coordinates, back-projects the point through the depth map, and checks that the
reconstructed z value stays within tolerance.
"""

from __future__ import annotations

import argparse
import random

import numpy as np

import robosuite
from robosuite.controllers import load_composite_controller_config


def build_env(camera_name: str, camera_height: int, camera_width: int):

    return robosuite.make(
        "Lift",
        robots="Panda",
        controller_configs=load_composite_controller_config(controller="BASIC", robot="Panda"),
        has_renderer=False,
        has_offscreen_renderer=True,
        ignore_done=True,
        use_object_obs=True,
        use_camera_obs=True,
        camera_names=[camera_name],
        camera_depths=[True],
        camera_heights=[camera_height],
        camera_widths=[camera_width],
        reward_shaping=True,
        control_freq=20,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", default="agentview", help="Fixed camera name")
    parser.add_argument("--height", type=int, default=120, help="Camera height in pixels")
    parser.add_argument("--width", type=int, default=120, help="Camera width in pixels")
    args = parser.parse_args()

    random.seed(0)
    np.random.seed(0)

    env = build_env(args.camera, args.height, args.width)
    try:
        import robosuite.utils.camera_utils as CU

        obs = env.reset()
        sim = env.sim

        if "object-state" not in obs:
            raise SystemExit("Lift did not return object-state; ensure use_object_obs=True.")

        obj_pos = obs["object-state"][:3]
        image = obs[f"{args.camera}_image"][::-1]
        depth_map = CU.get_real_depth_map(sim=sim, depth_map=obs[f"{args.camera}_depth"][::-1])

        world_to_camera = CU.get_camera_transform_matrix(
            sim=sim,
            camera_name=args.camera,
            camera_height=args.height,
            camera_width=args.width,
        )
        camera_to_world = np.linalg.inv(world_to_camera)

        obj_pixel = CU.project_points_from_world_to_camera(
            points=obj_pos,
            world_to_camera_transform=world_to_camera,
            camera_height=args.height,
            camera_width=args.width,
        )
        estimated_obj_pos = CU.transform_from_pixels_to_world(
            pixels=obj_pixel,
            depth_map=depth_map,
            camera_to_world_transform=camera_to_world,
        )

        max_z_err = np.sqrt(3) * 0.022
        z_err = float(np.abs(obj_pos[2] - estimated_obj_pos[2]))

        print(f"{args.camera}_image shape: {image.shape}")
        print(f"{args.camera}_depth shape: {depth_map.shape}")
        print(f"projected pixel: {obj_pixel}")
        print(f"object position: {obj_pos}")
        print(f"estimated position: {estimated_obj_pos}")
        print(f"z error: {z_err:.6f} (tolerance {max_z_err:.6f})")

        if z_err >= max_z_err:
            raise SystemExit("Camera transform smoke failed: z error exceeded tolerance.")

        print("Camera transform smoke passed.")
    finally:
        env.close()


if __name__ == "__main__":
    main()
