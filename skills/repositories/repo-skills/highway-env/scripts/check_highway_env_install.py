#!/usr/bin/env python3
"""Check an installed HighwayEnv package and run a bounded Gymnasium smoke test.

This helper is intentionally self-contained: it imports the installed package,
registers HighwayEnv environments, makes one environment, resets, samples a few
actions, optionally renders RGB frames, and prints a JSON summary.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import Any


def _space_summary(space: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {"type": type(space).__name__, "repr": repr(space)}
    for attr in ("shape", "dtype", "n"):
        if hasattr(space, attr):
            value = getattr(space, attr)
            try:
                if hasattr(value, "tolist"):
                    value = value.tolist()
                elif not isinstance(value, (str, int, float, bool, type(None))):
                    value = str(value)
            except Exception:
                value = str(value)
            summary[attr] = value
    if hasattr(space, "spaces"):
        spaces_obj = getattr(space, "spaces")
        if isinstance(spaces_obj, dict):
            summary["keys"] = sorted(str(k) for k in spaces_obj.keys())
        else:
            try:
                summary["length"] = len(spaces_obj)
            except Exception:
                pass
    return summary


def _shape(value: Any) -> Any:
    if hasattr(value, "shape"):
        return list(value.shape)
    if isinstance(value, dict):
        return {str(k): _shape(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_shape(v) for v in value]
    return None


def _json_default(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    if hasattr(value, "tolist"):
        return value.tolist()
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-id", default="highway-v0", help="Gymnasium environment ID to make.")
    parser.add_argument("--steps", type=int, default=3, help="Maximum sampled-action steps to run.")
    parser.add_argument("--seed", type=int, default=0, help="Reset seed.")
    parser.add_argument("--render-rgb", action="store_true", help="Create with render_mode='rgb_array' and render frames.")
    parser.add_argument("--duration", type=float, default=None, help="Optional config duration override for envs that support it.")
    parser.add_argument("--vehicles-count", type=int, default=None, help="Optional vehicles_count override for envs that support it.")
    args = parser.parse_args()

    result: dict[str, Any] = {"ok": False, "env_id": args.env_id, "steps_requested": args.steps}
    env = None
    try:
        import gymnasium as gym
        import highway_env

        gym.register_envs(highway_env)
        highway_ids = sorted(
            env_id
            for env_id, spec in gym.registry.items()
            if isinstance(spec.entry_point, str) and "highway_env" in spec.entry_point
        )
        result.update(
            {
                "highway_env_version": getattr(highway_env, "__version__", None),
                "registered_env_count": len(highway_ids),
                "registered_env_ids": highway_ids,
            }
        )

        config: dict[str, Any] = {}
        if args.duration is not None:
            config["duration"] = args.duration
        if args.vehicles_count is not None:
            config["vehicles_count"] = args.vehicles_count

        make_kwargs: dict[str, Any] = {}
        if config:
            make_kwargs["config"] = config
        if args.render_rgb:
            make_kwargs["render_mode"] = "rgb_array"

        env = gym.make(args.env_id, **make_kwargs)
        obs, info = env.reset(seed=args.seed)
        result.update(
            {
                "observation_space": _space_summary(env.observation_space),
                "action_space": _space_summary(env.action_space),
                "initial_observation_shape": _shape(obs),
                "initial_info_keys": sorted(str(k) for k in info.keys()),
            }
        )

        if args.render_rgb:
            frame = env.render()
            result["initial_render_shape"] = _shape(frame)

        terminated = truncated = False
        last_reward = None
        last_info: dict[str, Any] = {}
        steps_done = 0
        for _ in range(max(args.steps, 0)):
            if terminated or truncated:
                break
            action = env.action_space.sample()
            obs, reward, terminated, truncated, last_info = env.step(action)
            last_reward = reward
            steps_done += 1
            if args.render_rgb:
                frame = env.render()
                result["last_render_shape"] = _shape(frame)

        result.update(
            {
                "ok": True,
                "steps_done": steps_done,
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "last_reward": last_reward,
                "last_observation_shape": _shape(obs),
                "last_info_keys": sorted(str(k) for k in last_info.keys()),
            }
        )
    except Exception as exc:  # keep helper useful in broken environments
        result.update(
            {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "traceback": traceback.format_exc(limit=8),
            }
        )
    finally:
        if env is not None:
            try:
                env.close()
            except Exception as close_exc:
                result["close_error"] = f"{type(close_exc).__name__}: {close_exc}"

    print(json.dumps(result, indent=2, sort_keys=True, default=_json_default))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
