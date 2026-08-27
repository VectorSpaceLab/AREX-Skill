#!/usr/bin/env python3
"""Check a ManiSkill installation without relying on a source checkout.

Default mode only imports public packages and prints version/backend facts. Add
`--env-smoke` for a bounded no-render CPU environment reset/step.
"""

from __future__ import annotations

import argparse
import json
import os
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def dist_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def summarize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): summarize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [summarize(v) for v in value]
    if hasattr(value, "shape") and hasattr(value, "dtype"):
        return {"shape": list(value.shape), "dtype": str(value.dtype)}
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    return type(value).__name__


def collect_import_facts() -> dict[str, Any]:
    import gymnasium
    import mani_skill
    import mani_skill.envs  # noqa: F401 - registers public envs
    import sapien
    import torch
    from mani_skill.utils.registration import REGISTERED_ENVS

    return {
        "mani_skill_version": getattr(mani_skill, "__version__", dist_version("mani_skill")),
        "gymnasium_version": getattr(gymnasium, "__version__", dist_version("gymnasium")),
        "sapien_version": getattr(sapien, "__version__", dist_version("sapien")),
        "torch_version": getattr(torch, "__version__", dist_version("torch")),
        "torch_cuda_runtime": getattr(torch.version, "cuda", None),
        "torch_cuda_available": bool(torch.cuda.is_available()),
        "registered_env_count": len(REGISTERED_ENVS),
        "sample_env_ids": sorted(REGISTERED_ENVS)[:12],
    }


def run_env_smoke(env_id: str, steps: int, seed: int) -> dict[str, Any]:
    import gymnasium as gym
    import mani_skill.envs  # noqa: F401
    from mani_skill.utils.wrappers.gymnasium import CPUGymWrapper

    os.environ.setdefault("MS_SKIP_ASSET_DOWNLOAD_PROMPT", "1")
    raw_env = gym.make(
        env_id,
        num_envs=1,
        obs_mode="state",
        reward_mode="none",
        render_mode=None,
        sim_backend="physx_cpu",
        render_backend="none",
    )
    env = CPUGymWrapper(raw_env, record_metrics=True)
    try:
        if hasattr(env.action_space, "seed"):
            env.action_space.seed(seed)
        obs, info = env.reset(seed=seed)
        step_summaries = []
        for idx in range(steps):
            action = env.action_space.sample() if env.action_space is not None else None
            obs, reward, terminated, truncated, info = env.step(action)
            step_summaries.append(
                {
                    "step": idx + 1,
                    "reward": summarize(reward),
                    "terminated": summarize(terminated),
                    "truncated": summarize(truncated),
                }
            )
            if terminated or truncated:
                break
        return {
            "env_id": env_id,
            "reset_obs": summarize(obs),
            "reset_info": summarize(info),
            "steps": step_summaries,
        }
    finally:
        env.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-smoke", action="store_true", help="Also reset/step one CPU no-render environment")
    parser.add_argument("--env-id", default="PickCube-v1", help="Environment id for --env-smoke")
    parser.add_argument("--steps", type=int, default=2, help="Number of smoke steps")
    parser.add_argument("--seed", type=int, default=0, help="Reset/action seed for --env-smoke")
    parser.add_argument("--json", action="store_true", help="Emit JSON only")
    args = parser.parse_args()

    report: dict[str, Any] = {"status": "ok", "imports": collect_import_facts()}
    if args.env_smoke:
        report["env_smoke"] = run_env_smoke(args.env_id, args.steps, args.seed)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        print("\nUse --env-smoke only when a bounded CPU reset/step is acceptable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
