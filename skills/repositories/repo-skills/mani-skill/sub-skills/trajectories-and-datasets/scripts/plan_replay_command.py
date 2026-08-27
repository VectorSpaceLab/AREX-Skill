#!/usr/bin/env python3
"""Print a safe ManiSkill replay_trajectory command without running replay."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path
from typing import Any

CPU_BACKEND_TOKENS = ("cpu", "physx_cpu")
GPU_BACKEND_TOKENS = ("cuda", "gpu", "physx_cuda", "physx_gpu")


def shell_join(cmd: list[str]) -> str:
    return " \\\n  ".join(shlex.quote(x) for x in cmd)


def load_metadata(path: Path) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    json_path = path.with_suffix(".json")
    if not path.exists():
        warnings.append(f"HDF5 file does not exist: {path}")
    if not json_path.exists():
        warnings.append(f"sibling JSON metadata file is missing: {json_path}")
        return {}, warnings
    try:
        return json.loads(json_path.read_text(encoding="utf-8")), warnings
    except Exception as exc:
        warnings.append(f"could not parse JSON metadata: {exc}")
        return {}, warnings


def backend_kind(value: str | None) -> str:
    if not value:
        return "unknown"
    lower = value.lower()
    if any(tok in lower for tok in GPU_BACKEND_TOKENS):
        return "gpu"
    if any(tok in lower for tok in CPU_BACKEND_TOKENS):
        return "cpu"
    return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traj_path", type=Path, help="Path to a ManiSkill .h5 trajectory")
    parser.add_argument("-b", "--sim-backend", help="Target simulation backend, e.g. physx_cpu or physx_cuda")
    parser.add_argument("-o", "--obs-mode", help="Target observation mode to record")
    parser.add_argument("-c", "--target-control-mode", help="Target control mode for action conversion")
    parser.add_argument("--save-traj", action="store_true", help="Include --save-traj in the printed command")
    parser.add_argument("--save-video", action="store_true", help="Include --save-video in the printed command")
    parser.add_argument("--vis", action="store_true", help="Include --vis in the printed command")
    parser.add_argument("--use-env-states", action="store_true", help="Replay by saved env states")
    parser.add_argument("--use-first-env-state", action="store_true", help="Seed replay with the first saved env state")
    parser.add_argument("--allow-failure", action="store_true", help="Include failed episodes in saved output")
    parser.add_argument("--discard-timeout", action="store_true", help="Discard timeout/truncated episodes in saved output")
    parser.add_argument("--record-rewards", action="store_true", help="Record rewards in the replayed trajectory")
    parser.add_argument("--reward-mode", help="Reward mode to request during replay")
    parser.add_argument("--render-mode", help="Render mode for saved videos")
    parser.add_argument("--shader", help="Shader override for replay rendering")
    parser.add_argument("--video-fps", type=int, help="Saved video FPS")
    parser.add_argument("--count", type=int, help="Replay only the first N demonstrations")
    parser.add_argument("-n", "--num-envs", type=int, default=1, help="Number of replay envs/processes")
    args = parser.parse_args()

    metadata, warnings = load_metadata(args.traj_path)
    env_info = metadata.get("env_info", {}) or {}
    env_kwargs = env_info.get("env_kwargs", {}) or {}
    episodes = metadata.get("episodes", []) or []
    original_backend = env_kwargs.get("sim_backend") or "physx_cpu"
    target_backend = args.sim_backend or original_backend
    original_control_modes = sorted({ep.get("control_mode") for ep in episodes if ep.get("control_mode")})

    cmd = ["python", "-m", "mani_skill.trajectory.replay_trajectory", "--traj-path", str(args.traj_path)]
    if args.sim_backend:
        cmd.extend(["--sim-backend", args.sim_backend])
    if args.obs_mode:
        cmd.extend(["--obs-mode", args.obs_mode])
    if args.target_control_mode:
        cmd.extend(["--target-control-mode", args.target_control_mode])
    if args.save_traj:
        cmd.append("--save-traj")
    if args.save_video:
        cmd.append("--save-video")
    if args.vis:
        cmd.append("--vis")
    if args.use_env_states:
        cmd.append("--use-env-states")
    if args.use_first_env_state:
        cmd.append("--use-first-env-state")
    if args.allow_failure:
        cmd.append("--allow-failure")
    if args.discard_timeout:
        cmd.append("--discard-timeout")
    if args.record_rewards:
        cmd.append("--record-rewards")
    if args.reward_mode:
        cmd.extend(["--reward-mode", args.reward_mode])
    if args.render_mode:
        cmd.extend(["--render-mode", args.render_mode])
    if args.shader:
        cmd.extend(["--shader", args.shader])
    if args.video_fps is not None:
        cmd.extend(["--video-fps", str(args.video_fps)])
    if args.count is not None:
        cmd.extend(["--count", str(args.count)])
    if args.num_envs != 1:
        cmd.extend(["--num-envs", str(args.num_envs)])

    if not args.save_traj and not args.save_video and not args.vis:
        warnings.append("planned command replays but produces no saved output and no GUI; add --save-traj, --save-video, or --vis if desired")
    if len(original_control_modes) > 1:
        warnings.append(f"multiple original control modes found: {original_control_modes}; GPU-parallel replay requires batches with the same control mode")
    if args.target_control_mode and original_control_modes:
        differs = any(mode != args.target_control_mode for mode in original_control_modes)
        if differs and args.use_env_states:
            warnings.append("control-mode conversion cannot be combined with --use-env-states")
        if differs and backend_kind(target_backend) == "gpu":
            warnings.append("GPU-parallel replay does not support converting to a different control mode; use CPU for conversion")
    if args.sim_backend and backend_kind(args.sim_backend) != backend_kind(original_backend):
        if not (args.use_first_env_state or args.use_env_states):
            warnings.append("target backend differs from metadata backend; consider --use-first-env-state or replay on the original backend")
    if args.num_envs > 1 and backend_kind(target_backend) == "cpu":
        warnings.append("CPU replay with --num-envs > 1 uses multiprocessing and may create/merge per-worker files")

    print("Planned command (not executed):")
    print(shell_join(cmd))
    print("\nDetected metadata:")
    print(f"  env_id: {env_info.get('env_id')}")
    print(f"  original_backend: {original_backend}")
    print(f"  original_control_modes: {original_control_modes or None}")
    print(f"  episode_count: {len(episodes) if episodes else None}")
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")
        return 1 if any("does not exist" in w or "missing" in w for w in warnings) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
