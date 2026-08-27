#!/usr/bin/env python3
"""Small, non-interactive CUDA IK smoke check."""
from __future__ import annotations

import argparse

import torch

from curobo.inverse_kinematics import InverseKinematics, InverseKinematicsCfg
from curobo.types import DeviceCfg, GoalToolPose, Pose


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded cuRobo IK smoke check")
    parser.add_argument("--robot", default="franka.yml")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this smoke check")
    device_cfg = DeviceCfg(device=torch.device("cuda"), dtype=torch.float32)
    cfg = InverseKinematicsCfg.create(
        robot=args.robot, num_seeds=4, use_cuda_graph=True, device_cfg=device_cfg
    )
    solver = InverseKinematics(cfg)
    frame = solver.tool_frames[0]
    goal = Pose(
        position=torch.tensor([[0.4, 0.0, 0.4]], device="cuda", dtype=torch.float32),
        quaternion=torch.tensor([[1.0, 0.0, 0.0, 0.0]], device="cuda", dtype=torch.float32),
    )
    result = solver.solve_pose(GoalToolPose.from_poses({frame: goal}))
    print({"success": result.success.detach().cpu().tolist(), "frame": frame})
    if not bool(result.success.reshape(-1)[0]):
        raise RuntimeError("bounded IK target did not solve")


if __name__ == "__main__":
    main()
