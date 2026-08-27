#!/usr/bin/env python3
"""Bounded no-render CPU smoke for an installed or local ManiSkill package.

The helper is intentionally conservative:
- single environment
- PhysX CPU simulation
- rendering disabled
- asset-download prompts skipped by default
- bounded random actions

It can be executed from any current working directory by passing the script path
to Python. It first tries the active Python environment, then falls back to a
repo root found by walking upward from this file.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def _find_repo_root_from_this_file() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "mani_skill").is_dir() and (
            (parent / "pyproject.toml").exists() or (parent / "setup.py").exists()
        ):
            return parent
    return None


def _bootstrap_mani_skill_import() -> None:
    try:
        import mani_skill  # noqa: F401
        return
    except ModuleNotFoundError as exc:
        if exc.name != "mani_skill":
            raise
    repo_root = _find_repo_root_from_this_file()
    if repo_root is not None:
        sys.path.insert(0, str(repo_root))


def _summarize(value: Any) -> Any:
    try:
        import numpy as np
    except Exception:  # pragma: no cover - only for broken environments
        np = None  # type: ignore[assignment]

    if isinstance(value, dict):
        return {str(k): _summarize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_summarize(v) for v in value]
    if np is not None and isinstance(value, np.ndarray):
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    if np is not None and isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return type(value).__name__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-id", default="PickCube-v1", help="ManiSkill environment id to smoke-test")
    parser.add_argument("--obs-mode", default="state", help="Observation mode; keep 'state' for the cheapest smoke")
    parser.add_argument("--control-mode", default="pd_joint_delta_pos", help="Control mode for the default robot")
    parser.add_argument("--reward-mode", default="none", help="Reward mode; 'none' keeps the smoke cheap")
    parser.add_argument("--steps", type=int, default=3, help="Number of bounded random-action steps")
    parser.add_argument("--seed", type=int, default=0, help="Seed for reset and action-space sampling")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.steps < 1:
        raise SystemExit("--steps must be >= 1")

    os.environ.setdefault("MS_SKIP_ASSET_DOWNLOAD_PROMPT", "1")
    _bootstrap_mani_skill_import()

    import gymnasium as gym
    import mani_skill.envs  # noqa: F401 - registers public environments
    from mani_skill.utils.wrappers.gymnasium import CPUGymWrapper

    raw_env = None
    env = None
    try:
        raw_env = gym.make(
            args.env_id,
            num_envs=1,
            obs_mode=args.obs_mode,
            reward_mode=args.reward_mode,
            control_mode=args.control_mode,
            render_mode=None,
            sim_backend="physx_cpu",
            render_backend="none",
        )
        raw_env.unwrapped.print_sim_details()
        env = CPUGymWrapper(raw_env, record_metrics=True)
        raw_env = None

        if env.action_space is not None and hasattr(env.action_space, "seed"):
            env.action_space.seed(args.seed)

        obs, info = env.reset(seed=args.seed)
        print(
            json.dumps(
                {
                    "status": "reset_ok",
                    "env_id": args.env_id,
                    "obs_mode": args.obs_mode,
                    "action_space": str(env.action_space),
                    "observation_space": str(env.observation_space),
                    "obs": _summarize(obs),
                    "info": _summarize(info),
                },
                sort_keys=True,
            )
        )

        for step_idx in range(args.steps):
            action = env.action_space.sample() if env.action_space is not None else None
            obs, reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)
            print(
                json.dumps(
                    {
                        "status": "step_ok",
                        "step": step_idx + 1,
                        "reward": _summarize(reward),
                        "terminated": _summarize(terminated),
                        "truncated": _summarize(truncated),
                        "obs": _summarize(obs),
                        "episode": _summarize(info.get("episode", {})),
                    },
                    sort_keys=True,
                )
            )
            if done and step_idx + 1 < args.steps:
                obs, info = env.reset()
                print(json.dumps({"status": "reset_after_done", "step": step_idx + 1}, sort_keys=True))

        print(json.dumps({"status": "smoke_passed", "steps": args.steps}, sort_keys=True))
        return 0
    finally:
        if env is not None:
            env.close()
        elif raw_env is not None:
            raw_env.close()


if __name__ == "__main__":
    raise SystemExit(main())
