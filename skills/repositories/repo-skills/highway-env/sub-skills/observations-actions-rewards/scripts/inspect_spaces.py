#!/usr/bin/env python3
"""Inspect HighwayEnv spaces and one-step reward/info output as JSON.

This helper is intentionally bounded: it creates one environment, applies an
optional JSON config, resets once, takes one sampled action unless disabled, and
prints a JSON report. It does not run training, render, or read repository files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np


def to_jsonable(value: Any) -> Any:
    """Convert numpy/gym values into strict JSON-compatible values."""
    if isinstance(value, np.ndarray):
        return to_jsonable(value.tolist())
    if isinstance(value, np.generic):
        return to_jsonable(value.item())
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    if isinstance(value, range):
        return [to_jsonable(v) for v in value]
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if np.isfinite(value):
            return value
        if np.isnan(value):
            return "NaN"
        return "Infinity" if value > 0 else "-Infinity"
    if isinstance(value, str):
        return value
    return repr(value)


def array_summary(value: Any) -> dict[str, Any]:
    arr = np.asarray(value)
    summary: dict[str, Any] = {
        "kind": "array",
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
    }
    if arr.size and np.issubdtype(arr.dtype, np.number):
        finite = arr[np.isfinite(arr)]
        if finite.size:
            summary["min"] = to_jsonable(np.min(finite))
            summary["max"] = to_jsonable(np.max(finite))
            summary["mean"] = to_jsonable(np.mean(finite))
    return summary


def observation_summary(obs: Any) -> dict[str, Any]:
    if isinstance(obs, dict):
        return {
            "kind": "dict",
            "keys": list(obs.keys()),
            "items": {str(k): observation_summary(v) for k, v in obs.items()},
        }
    if isinstance(obs, tuple):
        return {
            "kind": "tuple",
            "length": len(obs),
            "items": [observation_summary(v) for v in obs],
        }
    return array_summary(obs)


def low_high_summary(value: Any) -> Any:
    arr = np.asarray(value)
    if arr.shape == ():
        return to_jsonable(arr.item())
    unique = np.unique(arr) if arr.size <= 16 else None
    if unique is not None and unique.size <= 4:
        return to_jsonable(unique)
    out: dict[str, Any] = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
    if arr.size and np.issubdtype(arr.dtype, np.number):
        finite = arr[np.isfinite(arr)]
        if finite.size:
            out["min"] = to_jsonable(np.min(finite))
            out["max"] = to_jsonable(np.max(finite))
    return out


def space_summary(space: Any) -> dict[str, Any]:
    from gymnasium import spaces

    if isinstance(space, spaces.Box):
        return {
            "type": "Box",
            "shape": list(space.shape),
            "dtype": str(space.dtype),
            "low": low_high_summary(space.low),
            "high": low_high_summary(space.high),
        }
    if isinstance(space, spaces.Discrete):
        return {"type": "Discrete", "n": int(space.n), "start": int(space.start)}
    if isinstance(space, spaces.Tuple):
        return {
            "type": "Tuple",
            "length": len(space.spaces),
            "spaces": [space_summary(s) for s in space.spaces],
        }
    if isinstance(space, spaces.Dict):
        return {
            "type": "Dict",
            "keys": list(space.spaces.keys()),
            "spaces": {str(k): space_summary(v) for k, v in space.spaces.items()},
        }
    if isinstance(space, spaces.MultiDiscrete):
        return {"type": "MultiDiscrete", "nvec": to_jsonable(space.nvec)}
    if isinstance(space, spaces.MultiBinary):
        return {"type": "MultiBinary", "n": to_jsonable(space.n)}
    return {"type": type(space).__name__, "repr": repr(space)}


def load_config(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.config_json and args.config_file:
        raise ValueError("use either --config-json or --config-file, not both")
    raw: str | None = None
    if args.config_json:
        raw = args.config_json
    elif args.config_file:
        if args.config_file == "-":
            raw = sys.stdin.read()
        else:
            raw = Path(args.config_file).read_text(encoding="utf-8")
    if raw is None or raw.strip() == "":
        return None
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError("config JSON must decode to an object/dict")
    return parsed


def limited_available_actions(env: Any, limit: int) -> dict[str, Any]:
    try:
        available = env.unwrapped.get_available_actions()
        values = []
        for idx, action in enumerate(available):
            if idx >= limit:
                return {"supported": True, "truncated": True, "values": values}
            values.append(to_jsonable(action))
        return {"supported": True, "truncated": False, "values": values}
    except NotImplementedError as exc:
        return {"supported": False, "error_type": type(exc).__name__, "error": str(exc)}
    except Exception as exc:  # keep errors clear without exposing traceback paths
        return {"supported": False, "error_type": type(exc).__name__, "error": str(exc)}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely inspect a HighwayEnv env's spaces and one sample step."
    )
    parser.add_argument("--env-id", default="highway-v0", help="Gymnasium env id")
    parser.add_argument(
        "--config-json",
        help="JSON object to pass as gym.make(..., config=...). Mutually exclusive with --config-file.",
    )
    parser.add_argument(
        "--config-file",
        help="Path to a JSON config file, or '-' to read JSON from stdin.",
    )
    parser.add_argument("--seed", type=int, default=0, help="Reset seed")
    parser.add_argument(
        "--available-limit",
        type=int,
        default=50,
        help="Maximum available-action entries to print",
    )
    parser.add_argument(
        "--no-step",
        action="store_true",
        help="Only reset and inspect spaces; do not take the sample step",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation; use 0 for compact output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    env = None
    stage = "load_config"
    try:
        config = load_config(args)

        stage = "import"
        import gymnasium as gym
        import highway_env  # noqa: F401 - import registers env ids

        stage = "make_env"
        make_kwargs: dict[str, Any] = {}
        if config is not None:
            make_kwargs["config"] = config
        env = gym.make(args.env_id, **make_kwargs)

        stage = "reset"
        obs, info = env.reset(seed=args.seed)

        report: dict[str, Any] = {
            "ok": True,
            "env_id": args.env_id,
            "config_provided": config is not None,
            "observation_space": space_summary(env.observation_space),
            "action_space": space_summary(env.action_space),
            "initial_observation": observation_summary(obs),
            "reset_info_keys": sorted(str(k) for k in info.keys()),
            "available_actions": limited_available_actions(env, args.available_limit),
        }

        if not args.no_step:
            stage = "sample_action"
            action = env.action_space.sample()
            stage = "step"
            next_obs, reward, terminated, truncated, step_info = env.step(action)
            rewards = step_info.get("rewards") if isinstance(step_info, dict) else None
            report["sample_step"] = {
                "action": to_jsonable(action),
                "reward": to_jsonable(reward),
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "next_observation": observation_summary(next_obs),
                "info_keys": sorted(str(k) for k in step_info.keys()),
                "reward_info_keys": sorted(str(k) for k in rewards.keys())
                if isinstance(rewards, dict)
                else [],
                "rewards": to_jsonable(rewards),
                "is_success": to_jsonable(step_info.get("is_success"))
                if isinstance(step_info, dict) and "is_success" in step_info
                else None,
            }

        indent = None if args.indent == 0 else args.indent
        print(json.dumps(report, allow_nan=False, indent=indent, sort_keys=True))
        return 0
    except json.JSONDecodeError as exc:
        error = {"ok": False, "stage": stage, "error_type": type(exc).__name__, "error": str(exc)}
    except Exception as exc:
        error = {"ok": False, "stage": stage, "error_type": type(exc).__name__, "error": str(exc)}
    finally:
        if env is not None:
            try:
                env.close()
            except Exception:
                pass

    print(json.dumps(error, allow_nan=False, indent=2, sort_keys=True), file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
