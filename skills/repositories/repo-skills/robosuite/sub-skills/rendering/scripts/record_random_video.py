#!/usr/bin/env python
"""Record a short random-action robosuite video to an explicit output path.

This helper uses offscreen rendering and sets the global image convention to OpenCV so the
written frames are right-side up for imageio.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import robosuite as suite
from robosuite.controllers import load_composite_controller_config


def build_env(args: argparse.Namespace):

    controller_configs = load_composite_controller_config(controller=args.controller, robot=args.robot)
    return suite.make(
        env_name=args.environment,
        robots=args.robot,
        controller_configs=controller_configs,
        has_renderer=False,
        has_offscreen_renderer=True,
        ignore_done=True,
        use_camera_obs=True,
        use_object_obs=False,
        camera_names=args.camera,
        camera_heights=args.height,
        camera_widths=args.width,
        control_freq=args.control_freq,
        seed=args.seed,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", default="Lift", help="robosuite env name")
    parser.add_argument("--robot", default="Panda", help="Single robot name for the env")
    parser.add_argument("--camera", default="agentview", help="Fixed camera name to record")
    parser.add_argument("--output", required=True, help="Explicit path to the output video file")
    parser.add_argument("--timesteps", type=int, default=20, help="Number of random control steps")
    parser.add_argument("--skip-frame", type=int, default=1, help="Write every Nth frame")
    parser.add_argument("--fps", type=int, default=20, help="Video frames per second")
    parser.add_argument("--height", type=int, default=128, help="Camera height in pixels")
    parser.add_argument("--width", type=int, default=128, help="Camera width in pixels")
    parser.add_argument("--control-freq", type=int, default=20, help="Control frequency for the env")
    parser.add_argument("--controller", default="BASIC", help="Composite controller name")
    parser.add_argument("--seed", type=int, default=None, help="Optional RNG seed for random actions")
    args = parser.parse_args()

    try:
        import imageio
        import robosuite.macros as macros
    except Exception as exc:  # pragma: no cover - handled as runtime guidance
        raise SystemExit(f"Could not import video dependencies: {exc}") from exc

    macros.IMAGE_CONVENTION = "opencv"

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    env = build_env(args)
    rng = np.random.default_rng(args.seed)
    writer = imageio.get_writer(str(output_path), fps=args.fps)
    try:
        obs = env.reset()
        low, high = env.action_spec
        for step in range(args.timesteps):
            action = rng.uniform(low, high)
            obs, _, done, _ = env.step(action)
            if step % args.skip_frame == 0:
                writer.append_data(obs[f"{args.camera}_image"])
                print(f"Wrote frame {step}")
            if done:
                break
    finally:
        writer.close()
        env.close()

    print(f"Video saved to {output_path}")


if __name__ == "__main__":
    main()
