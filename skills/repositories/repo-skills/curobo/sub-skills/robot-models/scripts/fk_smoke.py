#!/usr/bin/env python3
"""Bounded cuRobo CUDA FK and autograd smoke check."""
from __future__ import annotations

import argparse

import torch

from curobo.kinematics import Kinematics, KinematicsCfg
from curobo.types import DeviceCfg, JointState


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a small cuRobo FK smoke check")
    parser.add_argument("--robot", default="franka.yml")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this smoke check")
    device = torch.device(args.device)
    device_cfg = DeviceCfg(device=device, dtype=torch.float32)
    cfg = KinematicsCfg.from_robot_yaml_file(args.robot, device_cfg=device_cfg)
    kin = Kinematics(cfg)
    q = torch.zeros((1, kin.get_dof()), device=device, dtype=torch.float32, requires_grad=True)
    state = kin.compute_kinematics(JointState.from_position(q, joint_names=kin.joint_names))
    pose = state.tool_poses.get_link_pose(kin.tool_frames[0])
    loss = pose.position.square().sum()
    loss.backward()
    assert q.grad is not None
    print({"dof": kin.get_dof(), "tool_frames": kin.tool_frames, "position_shape": list(pose.position.shape)})


if __name__ == "__main__":
    main()
