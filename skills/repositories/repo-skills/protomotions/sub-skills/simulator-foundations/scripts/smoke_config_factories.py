#!/usr/bin/env python3
"""Construct ProtoMotions robot/simulator configs without starting a simulator.

This is a safe pre-runtime smoke for install or custom-robot tasks. It imports
factory/config surfaces only and does not allocate simulator state, open a
viewer, download assets, or run training.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--robot", default="g1", help="Robot name, e.g. g1, h1_2, smpl, smplx, amp, soma23")
    parser.add_argument("--simulator", default="mujoco", help="Simulator name, e.g. mujoco, isaaclab, isaacgym, newton, genesis")
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--headless", action="store_true", default=True)
    parser.add_argument("--experiment-name", default="config_smoke")
    args = parser.parse_args()

    from protomotions.robot_configs.factory import robot_config
    from protomotions.simulator.factory import simulator_config

    captured = io.StringIO()
    with contextlib.redirect_stdout(captured):
        robot_cfg = robot_config(args.robot)
        sim_cfg = simulator_config(
            args.simulator,
            robot_cfg,
            headless=args.headless,
            num_envs=args.num_envs,
            experiment_name=args.experiment_name,
        )
    payload = {
        "robot": args.robot,
        "robot_config_class": type(robot_cfg).__name__,
        "number_of_actions": robot_cfg.number_of_actions,
        "num_dofs": robot_cfg.kinematic_info.num_dofs,
        "num_bodies": len(robot_cfg.kinematic_info.body_names),
        "anchor_body_name": robot_cfg.anchor_body_name,
        "asset_file_name": getattr(robot_cfg.asset, "asset_file_name", None),
        "simulator": args.simulator,
        "simulator_config_class": type(sim_cfg).__name__,
        "simulator_target": sim_cfg._target_,
        "simulator_num_envs": sim_cfg.num_envs,
        "simulator_w_last": getattr(sim_cfg, "w_last", None),
        "fps": getattr(sim_cfg.sim, "fps", None),
        "decimation": getattr(sim_cfg.sim, "decimation", None),
        "captured_stdout": captured.getvalue().strip().splitlines()[-20:],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
