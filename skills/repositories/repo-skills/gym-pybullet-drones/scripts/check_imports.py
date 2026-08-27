#!/usr/bin/env python3
"""Check that gym-pybullet-drones is installed and, optionally, smoke-run a headless env.

This helper is intentionally small and safe:
- it verifies the installed package metadata and imports,
- it confirms Gymnasium env registration,
- and, when requested, it creates a single headless Aviary env and steps once.
"""
from __future__ import annotations

import argparse
import json
import sys
from importlib import import_module
from importlib.metadata import PackageNotFoundError, version
from typing import Any

ENV_IDS = (
    "ctrl-aviary-v0",
    "velocity-aviary-v0",
    "hover-aviary-v0",
    "multihover-aviary-v0",
)


def _dist(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def _load() -> tuple[Any, Any]:
    try:
        gym = import_module("gymnasium")
        import_module("gym_pybullet_drones")
        return gym, import_module("gym_pybullet_drones")
    except Exception as exc:  # noqa: BLE001 - CLI boundary.
        raise SystemExit(
            "Failed to import gym-pybullet-drones or Gymnasium. "
            "Install the package and its dependencies in the active environment, "
            f"then retry. Original error: {type(exc).__name__}: {exc}"
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check gym-pybullet-drones installation and env registration.")
    parser.add_argument(
        "--env-id",
        choices=ENV_IDS,
        default="hover-aviary-v0",
        help="Gymnasium env ID to instantiate during the optional headless smoke check.",
    )
    parser.add_argument(
        "--headless-smoke",
        action="store_true",
        help="Instantiate the selected env with gui=False and step once.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    gym, _ = _load()

    payload: dict[str, Any] = {
        "ok": True,
        "versions": {
            "gym-pybullet-drones": _dist("gym-pybullet-drones"),
            "gymnasium": _dist("gymnasium"),
            "pybullet": _dist("pybullet"),
            "stable-baselines3": _dist("stable-baselines3"),
            "torch": _dist("torch"),
        },
        "registered_envs": {env_id: str(gym.spec(env_id).entry_point) for env_id in ENV_IDS},
    }

    if args.headless_smoke:
        import numpy as np

        env = gym.make(args.env_id, gui=False, record=False)
        try:
            obs, info = env.reset(seed=0, options={})
            action = env.action_space.sample()
            obs2, reward, terminated, truncated, info2 = env.step(action)
            payload["headless_smoke"] = {
                "env_id": args.env_id,
                "reset_obs_shape": list(np.asarray(obs).shape),
                "step_obs_shape": list(np.asarray(obs2).shape),
                "reward_type": type(reward).__name__,
                "terminated": bool(terminated),
                "truncated": bool(truncated),
            }
        finally:
            env.close()

    json.dump(payload, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
