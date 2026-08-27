#!/usr/bin/env python3
"""Bounded planner construction smoke check; no viewer or long loop."""
from __future__ import annotations

import argparse

import torch

from curobo.motion_planner import MotionPlanner, MotionPlannerCfg
from curobo.types import DeviceCfg, JointState


def main() -> None:
    parser = argparse.ArgumentParser(description="Construct a cuRobo motion planner")
    parser.add_argument("--robot", default="franka.yml")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this smoke check")
    device_cfg = DeviceCfg(device=torch.device("cuda"), dtype=torch.float32)
    cfg = MotionPlannerCfg.create(
        robot=args.robot, num_ik_seeds=4, num_trajopt_seeds=2, device_cfg=device_cfg
    )
    planner = MotionPlanner(cfg)
    state = planner.default_joint_state
    assert state.position.shape[-1] == planner.action_dim
    print({"action_dim": planner.action_dim, "tool_frames": planner.tool_frames})


if __name__ == "__main__":
    main()
