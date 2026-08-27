#!/usr/bin/env python3
"""Smoke-test a HighwayEnv Gymnasium environment with sampled actions.

The helper requires only installed Python packages (gymnasium and highway-env).
It does not rely on repository-local data.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from typing import Any


def _jsonable(value: Any) -> Any:
    """Convert common Gymnasium/NumPy values into JSON-safe structures."""
    try:
        import numpy as np
    except Exception:  # pragma: no cover - numpy is a highway-env dependency
        np = None  # type: ignore[assignment]

    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if np is not None:
        if isinstance(value, np.generic):
            return value.item()
        if isinstance(value, np.ndarray):
            if value.size <= 12:
                return value.tolist()
            return {
                "type": "ndarray",
                "shape": list(value.shape),
                "dtype": str(value.dtype),
                "min": float(np.nanmin(value)) if value.size else None,
                "max": float(np.nanmax(value)) if value.size else None,
            }
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return repr(value)


def _done(value: Any) -> bool:
    """Return True if a scalar/tuple/list/array done-like value has any true item."""
    try:
        import numpy as np

        if isinstance(value, np.ndarray):
            return bool(np.asarray(value).any())
        if isinstance(value, np.generic):
            return bool(value.item())
    except Exception:  # pragma: no cover
        pass
    if isinstance(value, (list, tuple)):
        return any(_done(v) for v in value)
    return bool(value)


def _space_summary(space: Any) -> dict[str, Any]:
    summary = {"repr": repr(space), "type": type(space).__name__}
    for attr in ("shape", "dtype", "n"):
        if hasattr(space, attr):
            summary[attr] = _jsonable(getattr(space, attr))
    if hasattr(space, "spaces"):
        spaces = getattr(space, "spaces")
        if isinstance(spaces, dict):
            summary["spaces"] = {str(k): _space_summary(v) for k, v in spaces.items()}
        else:
            summary["spaces"] = [_space_summary(v) for v in spaces]
    return summary


def _parse_config_json(text: str | None) -> dict[str, Any]:
    if not text:
        return {}
    parsed = json.loads(text)
    if not isinstance(parsed, dict):
        raise ValueError("--config-json must decode to a JSON object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a short HighwayEnv rollout with sampled actions and print a JSON summary."
    )
    parser.add_argument("--env-id", default="highway-v0", help="Gymnasium env id, e.g. highway-v0 or highway_env:highway-v0.")
    parser.add_argument("--steps", type=int, default=5, help="Maximum number of sampled actions to step.")
    parser.add_argument("--duration", type=float, default=None, help="Optional config duration in seconds.")
    parser.add_argument("--vehicles-count", type=int, default=None, help="Optional config vehicles_count value.")
    parser.add_argument("--seed", type=int, default=0, help="Reset and action-space seed.")
    parser.add_argument(
        "--render-mode",
        choices=("none", "rgb_array", "human"),
        default="none",
        help="Gymnasium render mode to request.",
    )
    parser.add_argument(
        "--render-rgb",
        action="store_true",
        help="Force rgb_array mode and capture render frame metadata after reset/steps.",
    )
    parser.add_argument(
        "--config-json",
        default=None,
        help="Additional JSON object merged into the HighwayEnv config before duration/vehicles-count overrides.",
    )
    parser.add_argument(
        "--stop-on-done",
        action="store_true",
        help="Stop at the first terminated/truncated episode instead of resetting to finish --steps actions.",
    )
    parser.add_argument(
        "--show-traceback",
        action="store_true",
        help="Include a traceback string in the JSON summary on failure.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    if args.steps < 0:
        raise ValueError("--steps must be non-negative")

    config = _parse_config_json(args.config_json)
    if args.duration is not None:
        config["duration"] = args.duration
    if args.vehicles_count is not None:
        config["vehicles_count"] = args.vehicles_count

    render_mode = "rgb_array" if args.render_rgb else args.render_mode
    if render_mode == "none":
        render_mode = None

    import gymnasium as gym
    import highway_env
    import numpy as np

    try:
        gym.register_envs(highway_env)
    except Exception:
        if hasattr(highway_env, "_register_highway_envs"):
            highway_env._register_highway_envs()
        else:
            raise

    make_kwargs: dict[str, Any] = {}
    if config:
        make_kwargs["config"] = config
    if render_mode is not None:
        make_kwargs["render_mode"] = render_mode

    render_mode_fallback_set = False
    try:
        env = gym.make(args.env_id, **make_kwargs)
    except TypeError as exc:
        if render_mode is None or "render_mode" not in str(exc):
            raise
        # Some registered env constructors do not accept render_mode even though
        # their unwrapped AbstractEnv rendering machinery can use it after make.
        fallback_kwargs = dict(make_kwargs)
        fallback_kwargs.pop("render_mode", None)
        env = gym.make(args.env_id, **fallback_kwargs)
        env.unwrapped.render_mode = render_mode
        try:
            env.unwrapped.configure({})
        except Exception:
            pass
        render_mode_fallback_set = True

    frames_captured = 0
    first_frame_shape = None
    first_frame_dtype = None
    reset_count = 0
    episodes_finished = 0
    steps_executed = 0
    last_reward = None
    last_terminated = False
    last_truncated = False
    last_info: dict[str, Any] = {}

    def capture_frame() -> None:
        nonlocal frames_captured, first_frame_shape, first_frame_dtype
        if render_mode != "rgb_array":
            return
        frame = env.render()
        if isinstance(frame, np.ndarray):
            frames_captured += 1
            if first_frame_shape is None:
                first_frame_shape = list(frame.shape)
                first_frame_dtype = str(frame.dtype)

    try:
        obs, info = env.reset(seed=args.seed)
        reset_count += 1
        try:
            env.action_space.seed(args.seed)
        except Exception:
            pass
        capture_frame()

        for step_index in range(args.steps):
            action = env.action_space.sample()
            obs, reward, terminated, truncated, info = env.step(action)
            steps_executed += 1
            last_reward = reward
            last_terminated = terminated
            last_truncated = truncated
            last_info = info if isinstance(info, dict) else {"info": info}
            capture_frame()

            done = _done(terminated) or _done(truncated)
            if done:
                episodes_finished += 1
                if args.stop_on_done or step_index == args.steps - 1:
                    break
                obs, info = env.reset()
                reset_count += 1
                last_info = info if isinstance(info, dict) else {"info": info}
                capture_frame()

        summary = {
            "ok": True,
            "env_id_requested": args.env_id,
            "env_spec_id": getattr(getattr(env, "spec", None), "id", None),
            "highway_env_version": getattr(highway_env, "__version__", None),
            "unwrapped_class": type(env.unwrapped).__name__,
            "config_applied": config,
            "seed": args.seed,
            "render_mode": render_mode,
            "render_mode_fallback_set": render_mode_fallback_set,
            "steps_requested": args.steps,
            "steps_executed": steps_executed,
            "reset_count": reset_count,
            "episodes_finished": episodes_finished,
            "last_terminated": _jsonable(last_terminated),
            "last_truncated": _jsonable(last_truncated),
            "last_reward": _jsonable(last_reward),
            "observation_space": _space_summary(env.observation_space),
            "action_space": _space_summary(env.action_space),
            "observation_summary": _jsonable(obs),
            "info_keys": sorted(str(k) for k in last_info.keys()),
            "info_summary": _jsonable(last_info),
            "rgb_frames_captured": frames_captured,
            "first_rgb_frame_shape": first_frame_shape,
            "first_rgb_frame_dtype": first_frame_dtype,
        }
        print(json.dumps(summary, sort_keys=True))
        return 0
    finally:
        env.close()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except Exception as exc:  # Print machine-readable failure for automation.
        payload = {
            "ok": False,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "env_id_requested": getattr(args, "env_id", None),
        }
        if getattr(args, "show_traceback", False):
            payload["traceback"] = traceback.format_exc()
        print(json.dumps(payload, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
