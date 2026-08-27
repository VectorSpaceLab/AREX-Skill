#!/usr/bin/env python3
"""Run a bounded, headless individual-behavior smoke check.

This helper creates its own temporary scene. It deliberately does not test ORCA;
use --probe-orca only for an independent import-status report.
"""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

# This helper is deliberately headless even when the caller's shell has a GUI
# backend configured. Set it before importing IR-SIM/Matplotlib.
os.environ["MPLBACKEND"] = "Agg"

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Step a tiny temporary IR-SIM scene with dash, rvo, or sfm."
    )
    parser.add_argument("--behavior", choices=("dash", "rvo", "sfm"), default="rvo")
    parser.add_argument("--kinematics", choices=("diff", "omni"), default="diff")
    parser.add_argument("--steps", type=int, default=4, help="bounded step count")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--mode",
        choices=("rvo", "vo", "hrvo"),
        default="rvo",
        help="RVO mode; ignored for dash and sfm",
    )
    parser.add_argument(
        "--probe-orca",
        action="store_true",
        help="report whether pyrvo imports; does not run or verify ORCA",
    )
    return parser.parse_args()


def scene_config(behavior: str, kinematics: str, mode: str) -> dict:
    behavior_config: dict[str, object] = {"name": behavior}
    if behavior == "rvo":
        behavior_config.update(
            vxmax=1.0,
            vymax=1.0,
            acce=1.0,
            factor=1.5,
            mode=mode,
            neighbor_threshold=4.0,
        )
    elif behavior == "sfm":
        behavior_config.update(
            vmax=0.8,
            neighbor_threshold=4.0,
            force_factor_social=2.5,
            force_factor_obstacle=3.0,
            sigma_obstacle=0.5,
            safety_radius=0.05,
        )

    limits = [-1.5, -3.0] if kinematics == "diff" else [-1.5, -1.5]
    maximum = [1.5, 3.0] if kinematics == "diff" else [1.5, 1.5]
    return {
        "world": {
            "height": 6,
            "width": 10,
            "offset": [-5, -3],
            "step_time": 0.1,
            "sample_time": 0.1,
            "control_mode": "auto",
            "collision_mode": "unobstructed",
        },
        "robot": [
            {
                "kinematics": {"name": kinematics},
                "shape": [{"name": "circle", "radius": 0.2}],
                "state": [-3.5, 0.0, 0.0],
                "goal": [3.5, 0.0, 0.0],
                "behavior": behavior_config,
                "vel_min": limits,
                "vel_max": maximum,
                "goal_threshold": 0.15,
                "arrive_mode": "position",
            },
            {
                "kinematics": {"name": kinematics},
                "shape": [{"name": "circle", "radius": 0.2}],
                "state": [3.5, 0.2, 3.14159],
                "goal": [-3.5, 0.2, 3.14159],
                "behavior": behavior_config,
                "vel_min": limits,
                "vel_max": maximum,
                "goal_threshold": 0.15,
                "arrive_mode": "position",
            },
        ],
        "obstacle": [
            {
                "shape": {
                    "name": "linestring",
                    "vertices": [[-4.5, 2.0], [0.0, 2.0], [4.5, 2.0]],
                },
                "state": [0, 0, 0],
                "unobstructed": True,
            }
        ],
    }


def main() -> int:
    args = parse_args()
    if args.steps < 0:
        raise SystemExit("--steps must be non-negative")

    if args.probe_orca:
        try:
            import pyrvo  # type: ignore  # optional probe only
        except ImportError as exc:
            print(f"ORCA not verified: pyrvo unavailable ({exc})")
        else:
            print(f"pyrvo importable ({pyrvo!r}); ORCA still requires an independent run")

    import irsim
    import irsim.lib.behavior.behavior_methods  # noqa: F401

    from irsim.lib.behavior.behavior_registry import behaviors_map

    key = (args.kinematics, args.behavior)
    if key not in behaviors_map:
        raise SystemExit(f"unsupported built-in behavior pair: {key!r}")

    with tempfile.TemporaryDirectory(prefix="ir-sim-behavior-") as directory:
        config_path = Path(directory) / "scene.yaml"
        config_path.write_text(
            yaml.safe_dump(scene_config(args.behavior, args.kinematics, args.mode)),
            encoding="utf-8",
        )
        env = irsim.make(
            str(config_path),
            display=False,
            disable_all_plot=True,
            save_ani=False,
            seed=args.seed,
        )
        try:
            for _ in range(args.steps):
                env.step()
            print(
                f"behavior={args.behavior} kinematics={args.kinematics} "
                f"mode={args.mode} steps={args.steps} ok"
            )
        finally:
            env.end(suppress_summary=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
