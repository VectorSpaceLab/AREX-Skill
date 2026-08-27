#!/usr/bin/env python3
"""Smoke-check the ACT++ simulation backend.

This helper imports the repo modules from an explicit checkout, seeds the
correct object pose for a selected task, and resets both the end-effector and
joint-space environments without stepping the episode.

Example:
    MUJOCO_GL=egl python scripts/check_sim_backend.py --repo-root /path/to/act-plus-plus --task sim_transfer_cube
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def add_repo_root(repo_root: str) -> None:
    root = Path(repo_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"repo root does not exist: {root}")
    sys.path.insert(0, str(root))


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check ACT++ sim backend.")
    parser.add_argument("--repo-root", required=True, help="Path to an ACT++ checkout.")
    parser.add_argument("--task", default="sim_transfer_cube", choices=["sim_transfer_cube", "sim_insertion"], help="Task name prefix used for the smoke reset.")
    args = parser.parse_args()

    add_repo_root(args.repo_root)

    try:
        from utils import sample_box_pose, sample_insertion_pose
        from sim_env import make_sim_env, BOX_POSE
        from ee_sim_env import make_ee_sim_env
    except Exception as exc:
        print(f"IMPORT FAIL: {type(exc).__name__}: {exc}")
        return 1

    print(f"MUJOCO_GL={os.environ.get('MUJOCO_GL', '<unset>')}")
    print(f"task={args.task}")

    if args.task == "sim_transfer_cube":
        BOX_POSE[0] = sample_box_pose()
        expected_cam_names = ["top", "left_wrist", "right_wrist"]
    else:
        peg_pose, socket_pose = sample_insertion_pose()
        BOX_POSE[0] = list(peg_pose) + list(socket_pose)
        expected_cam_names = ["top", "left_wrist", "right_wrist"]

    try:
        joint_env = make_sim_env(args.task)
        joint_ts = joint_env.reset()
        print("joint_env_ok", joint_env.task.max_reward)
        print("joint_obs_keys", sorted(joint_ts.observation.keys()))
        print("joint_image_keys", sorted(joint_ts.observation["images"].keys()))
    except Exception as exc:
        print(f"JOINT RESET FAIL: {type(exc).__name__}: {exc}")
        return 2

    ee_task = args.task.replace("_scripted", "")
    try:
        ee_env = make_ee_sim_env(ee_task)
        ee_ts = ee_env.reset()
        print("ee_env_ok", ee_env.task.max_reward)
        print("ee_obs_keys", sorted(ee_ts.observation.keys()))
        print("ee_image_keys", sorted(ee_ts.observation["images"].keys()))
    except Exception as exc:
        print(f"EE RESET FAIL: {type(exc).__name__}: {exc}")
        return 3

    print("expected_camera_names", expected_cam_names)
    print("simulation backend smoke passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
