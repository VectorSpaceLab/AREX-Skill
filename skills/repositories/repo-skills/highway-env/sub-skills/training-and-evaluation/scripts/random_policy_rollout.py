#!/usr/bin/env python3
"""Bounded random-policy rollouts for HighwayEnv without RL dependencies."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any


def positive_int(value: str) -> int:
    """Parse a positive integer argparse value."""
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


def load_config(config_arg: str | None) -> dict[str, Any] | None:
    """Load an optional environment config from a JSON string or JSON file path."""
    if not config_arg:
        return None

    stripped = config_arg.strip()
    if stripped.startswith("{"):
        raw = stripped
    else:
        candidate = Path(config_arg)
        if candidate.exists():
            raw = candidate.read_text(encoding="utf-8")
        else:
            raw = config_arg

    try:
        config = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--config-json must be a JSON object or path: {exc}") from exc

    if not isinstance(config, dict):
        raise SystemExit("--config-json must decode to a JSON object")
    return config


def coerce_optional_bool(value: Any) -> bool | None:
    """Best-effort conversion for bool-like info values and nested summaries."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (list, tuple, set)):
        converted = [coerce_optional_bool(item) for item in value]
        converted = [item for item in converted if item is not None]
        return any(converted) if converted else None
    if isinstance(value, dict):
        converted = [coerce_optional_bool(item) for item in value.values()]
        converted = [item for item in converted if item is not None]
        return any(converted) if converted else None
    if hasattr(value, "tolist"):
        try:
            return coerce_optional_bool(value.tolist())
        except Exception:  # noqa: BLE001 - diagnostics must stay best-effort
            return None
    if hasattr(value, "item"):
        try:
            item = value.item()
        except Exception:  # noqa: BLE001 - diagnostics must stay best-effort
            return None
        return coerce_optional_bool(item)
    return None


def reward_to_float(value: Any) -> float:
    """Convert scalar or nested reward values into a single summary float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, (list, tuple, set)):
        return sum(reward_to_float(item) for item in value)
    if isinstance(value, dict):
        return sum(reward_to_float(item) for item in value.values())
    if hasattr(value, "tolist"):
        return reward_to_float(value.tolist())
    if hasattr(value, "item"):
        return float(value.item())
    return float(value)


def extract_bool(info: dict[str, Any], *keys: str) -> bool | None:
    """Extract the first bool-like value from an info dictionary."""
    for key in keys:
        if key in info:
            converted = coerce_optional_bool(info[key])
            if converted is not None:
                return converted
    return None


def frame_shape(frame: Any) -> list[int] | None:
    """Return a JSON-friendly frame shape when render() returns an array-like frame."""
    shape = getattr(frame, "shape", None)
    if shape is None:
        return None
    try:
        return [int(dim) for dim in shape]
    except TypeError:
        return None


def summarize_episodes(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate rollout metrics."""
    returns = [float(item["return"]) for item in episodes]
    steps = [int(item["steps"]) for item in episodes]
    crashed = [item["crashed"] for item in episodes if item["crashed"] is not None]
    successes = [item["is_success"] for item in episodes if item["is_success"] is not None]

    summary: dict[str, Any] = {
        "episodes": len(episodes),
        "mean_return": statistics.fmean(returns) if returns else 0.0,
        "mean_steps": statistics.fmean(steps) if steps else 0.0,
        "terminated_episodes": sum(bool(item["terminated"]) for item in episodes),
        "truncated_episodes": sum(bool(item["truncated"]) for item in episodes),
        "reached_step_cap_episodes": sum(
            bool(item["reached_step_cap"]) for item in episodes
        ),
    }
    if crashed:
        summary["crash_rate"] = sum(crashed) / len(crashed)
    if successes:
        summary["success_rate"] = sum(successes) / len(successes)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run bounded random-policy HighwayEnv rollouts and summarize returns, "
            "durations, crashes, and optional rgb_array rendering."
        )
    )
    parser.add_argument("--env-id", default="highway-v0", help="Gymnasium env id")
    parser.add_argument(
        "--episodes", type=positive_int, default=1, help="number of episodes to run"
    )
    parser.add_argument(
        "--max-steps",
        type=positive_int,
        default=100,
        help="hard step cap per episode",
    )
    parser.add_argument("--seed", type=int, default=None, help="base random seed")
    parser.add_argument(
        "--render-rgb",
        action="store_true",
        help="create the env with render_mode='rgb_array' and render each step",
    )
    parser.add_argument(
        "--config-json",
        default=None,
        help="optional environment config as a JSON object string or JSON file path",
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="optional path for the JSON rollout summary",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="print only errors and optional JSON output"
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config_json)

    try:
        import gymnasium as gym
        import highway_env
    except Exception as exc:  # noqa: BLE001 - show a concise runtime diagnostic
        print(
            "Failed to import gymnasium/highway_env. Install highway-env before "
            f"running this helper. Original error: {exc}",
            file=sys.stderr,
        )
        return 2

    if hasattr(gym, "register_envs"):
        gym.register_envs(highway_env)

    make_kwargs: dict[str, Any] = {}
    if config is not None:
        make_kwargs["config"] = config
    if args.render_rgb:
        make_kwargs["render_mode"] = "rgb_array"

    env = None
    try:
        env = gym.make(args.env_id, **make_kwargs)
        if args.seed is not None:
            env.action_space.seed(args.seed)

        episode_reports: list[dict[str, Any]] = []
        for episode in range(args.episodes):
            episode_seed = None if args.seed is None else args.seed + episode
            obs, info = env.reset(seed=episode_seed)
            del obs  # the smoke helper reports rollout metrics, not observations

            total_reward = 0.0
            steps = 0
            terminated = False
            truncated = False
            crashed = extract_bool(info, "crashed")
            success = extract_bool(info, "is_success")
            last_frame_shape = None

            if args.render_rgb:
                last_frame_shape = frame_shape(env.render())

            while not (terminated or truncated) and steps < args.max_steps:
                action = env.action_space.sample()
                obs, reward, terminated, truncated, info = env.step(action)
                del obs
                total_reward += reward_to_float(reward)
                steps += 1

                step_crashed = extract_bool(info, "crashed")
                if step_crashed is not None:
                    crashed = bool(crashed) or step_crashed

                step_success = extract_bool(info, "is_success")
                if step_success is not None:
                    success = step_success

                if args.render_rgb:
                    last_frame_shape = frame_shape(env.render())

            report = {
                "episode": episode,
                "seed": episode_seed,
                "return": total_reward,
                "steps": steps,
                "terminated": bool(terminated),
                "truncated": bool(truncated),
                "reached_step_cap": not (terminated or truncated),
                "crashed": crashed,
                "is_success": success,
                "last_rgb_frame_shape": last_frame_shape,
            }
            episode_reports.append(report)

            if not args.quiet:
                print(
                    "episode={episode} return={return:.6g} steps={steps} "
                    "terminated={terminated} truncated={truncated} "
                    "step_cap={reached_step_cap} crashed={crashed} "
                    "success={is_success} frame_shape={last_rgb_frame_shape}".format(
                        **report
                    )
                )

        result = {
            "env_id": args.env_id,
            "render_rgb": bool(args.render_rgb),
            "max_steps": args.max_steps,
            "episodes": episode_reports,
            "aggregate": summarize_episodes(episode_reports),
        }

        if args.output_json:
            output_path = Path(args.output_json)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            if not args.quiet:
                print(f"wrote JSON summary to {output_path}")
        elif args.quiet:
            print(json.dumps(result, indent=2))

        return 0
    finally:
        if env is not None:
            env.close()


if __name__ == "__main__":
    raise SystemExit(main())
