#!/usr/bin/env python3
"""Bounded CUDA construction smoke for cuRobo optimization configs."""
from __future__ import annotations

import argparse

import torch

from curobo.model_predictive_control import ModelPredictiveControl, ModelPredictiveControlCfg
from curobo.types import DeviceCfg
from curobo.trajectory_optimizer import TrajectoryOptimizer, TrajectoryOptimizerCfg


def main() -> None:
    parser = argparse.ArgumentParser(description="Construct cuRobo optimization solvers")
    parser.add_argument("--robot", default="franka.yml")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this smoke check")
    device_cfg = DeviceCfg(device=torch.device("cuda:0"), dtype=torch.float32)
    traj = TrajectoryOptimizer(
        TrajectoryOptimizerCfg.create(robot=args.robot, num_seeds=2, device_cfg=device_cfg)
    )
    mpc = ModelPredictiveControl(ModelPredictiveControlCfg.create(robot=args.robot, device_cfg=device_cfg))
    print({"trajopt_action_dim": traj.action_dim, "mpc_action_dim": mpc.action_dim})


if __name__ == "__main__":
    main()
