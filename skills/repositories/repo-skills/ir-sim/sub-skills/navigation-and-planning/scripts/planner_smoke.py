#!/usr/bin/env python3
"""Run bounded planner checks on self-contained temporary scenes."""

from __future__ import annotations

import argparse
import os
import random
import tempfile
from pathlib import Path

# This helper is deliberately headless even when the caller's shell has a GUI
# backend configured. Set it before importing IR-SIM/Matplotlib.
os.environ["MPLBACKEND"] = "Agg"

import numpy as np
import yaml

PLANNER_NAMES = ("astar", "jps", "rrt", "rrtstar", "informed", "prm")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plan on a tiny temporary map without animation or source examples."
    )
    parser.add_argument(
        "--planners",
        default=",".join(PLANNER_NAMES),
        help="comma-separated: astar,jps,rrt,rrtstar,informed,prm",
    )
    parser.add_argument("--resolution", type=float, default=0.5)
    parser.add_argument("--max-iter", type=int, default=120)
    parser.add_argument("--samples", type=int, default=60)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument(
        "--blocked",
        action="store_true",
        help="cover the goal; no route is expected (degenerate results are reported)",
    )
    return parser.parse_args()


def config(blocked: bool) -> tuple[dict, list[float], list[float]]:
    goal = [8.5, 8.5, 0.0]
    obstacles = []
    if blocked:
        obstacles.append(
            {
                "shape": {"name": "circle", "radius": 1.0},
                "state": [goal[0], goal[1], 0.0],
            }
        )
    scene = {
        "world": {
            "height": 10,
            "width": 10,
            "offset": [0, 0],
            "step_time": 0.1,
            "sample_time": 0.1,
            "control_mode": "auto",
            "collision_mode": "stop",
        },
        "robot": [
            {
                "kinematics": {"name": "diff"},
                "shape": [{"name": "circle", "radius": 0.2}],
                "state": [1.0, 1.0, 0.0],
                "goal": goal,
                "behavior": {"name": "dash"},
                "vel_min": [-1.5, -3.0],
                "vel_max": [1.5, 3.0],
                "arrive_mode": "position",
                "goal_threshold": 0.15,
            }
        ],
    }
    if obstacles:
        scene["obstacle"] = obstacles
    return scene, [1.0, 1.0], goal[:2]


def make_planner(name: str, env_map, robot, max_iter: int, samples: int):
    from irsim.lib.path_planners import (
        AStarPlanner,
        InformedRRTStar,
        JPSPlanner,
        PRMPlanner,
        RRT,
        RRTStar,
    )

    if name == "astar":
        return AStarPlanner(env_map)
    if name == "jps":
        return JPSPlanner(env_map)
    if name == "rrt":
        return RRT(env_map, robot=robot, max_iter=max_iter, expand_dis=1.5)
    if name == "rrtstar":
        return RRTStar(env_map, robot=robot, max_iter=max_iter, expand_dis=1.5)
    if name == "informed":
        return InformedRRTStar(env_map, robot=robot, max_iter=max_iter, expand_dis=1.5)
    if name == "prm":
        return PRMPlanner(
            env_map,
            robot_radius=float(robot.radius),
            n_sample=samples,
            n_knn=8,
            max_edge_len=5.0,
        )
    raise ValueError(f"unknown planner {name!r}")


def no_route(result) -> bool:
    if result is None:
        return True
    try:
        return np.asarray(result).size == 0 or np.asarray(result).shape[-1] < 2
    except (AttributeError, IndexError, TypeError):
        return False


def main() -> int:
    args = parse_args()
    names = [item.strip().lower() for item in args.planners.split(",") if item.strip()]
    unknown = sorted(set(names) - set(PLANNER_NAMES))
    if unknown:
        raise SystemExit(f"unknown planners: {', '.join(unknown)}")
    if args.resolution <= 0 or args.max_iter <= 0 or args.samples <= 0:
        raise SystemExit("resolution, max-iter, and samples must be positive")

    random.seed(args.seed)
    np.random.seed(args.seed)
    import irsim
    from irsim.util.random import set_seed

    set_seed(args.seed)
    scene, start, goal = config(args.blocked)
    with tempfile.TemporaryDirectory(prefix="ir-sim-planner-") as directory:
        config_path = Path(directory) / "scene.yaml"
        config_path.write_text(yaml.safe_dump(scene), encoding="utf-8")
        env = irsim.make(
            str(config_path),
            display=False,
            save_ani=False,
            seed=args.seed,
        )
        try:
            env_map = env.get_map(resolution=args.resolution)
            for name in names:
                planner = make_planner(name, env_map, env.robot, args.max_iter, args.samples)
                result = planner.planning(start, goal, show_animation=False)
                empty = no_route(result)
                status = "no-route" if empty else "path"
                if not args.blocked and empty:
                    raise RuntimeError(f"{name} failed on the tiny open map")
                if not empty:
                    env.draw_trajectory(result, traj_type="r-")
                print(f"planner={name} status={status}")
        finally:
            env.end(suppress_summary=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
