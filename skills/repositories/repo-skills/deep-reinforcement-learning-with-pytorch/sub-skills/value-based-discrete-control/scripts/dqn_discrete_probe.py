#!/usr/bin/env python3
"""Bounded DQN classic-control compatibility probe.

This helper creates a Gym discrete-action environment, runs a few random steps
without rendering, instantiates a tiny Q-network with matching dimensions, and
prints JSON with replay-shape and API facts. It does not train and does not read
from the original repository checkout.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Tuple


def _obs_from_reset(result: Any) -> Tuple[Any, str]:
    if isinstance(result, tuple) and len(result) == 2:
        return result[0], "new_reset_tuple"
    return result, "old_reset_obs"


def _step_parts(result: Any) -> Tuple[Any, float, bool, dict, str]:
    if isinstance(result, tuple) and len(result) == 5:
        obs, reward, terminated, truncated, info = result
        return obs, float(reward), bool(terminated or truncated), dict(info), "new_step_5_tuple"
    if isinstance(result, tuple) and len(result) == 4:
        obs, reward, done, info = result
        return obs, float(reward), bool(done), dict(info), "old_step_4_tuple"
    raise RuntimeError(f"Unsupported env.step return format: {type(result)!r} {result!r}")


def _shape_size(shape: Any) -> int:
    import numpy as np

    if shape is None:
        return 1
    return int(np.prod(shape))


def _shaped_reward(style: str, raw_reward: float, state: Any, next_state: Any, env: Any) -> float:
    import numpy as np

    if style == "none":
        return raw_reward
    next_arr = np.asarray(next_state, dtype=float)
    if style == "mountaincar-legacy-scale":
        return raw_reward * 100.0 if raw_reward > 0 else raw_reward * 5.0
    if style == "mountaincar-position-bonus":
        # A tiny explicit shaping probe: reward higher positions without hiding raw reward.
        position = float(next_arr[0]) if next_arr.size else 0.0
        return raw_reward + 0.1 * (position + 0.5)
    if style == "cartpole-balance":
        x, _x_dot, theta, _theta_dot = next_arr.tolist()
        x_threshold = float(getattr(env, "x_threshold", 2.4))
        theta_threshold = float(getattr(env, "theta_threshold_radians", 12 * 2 * np.pi / 360))
        r1 = (x_threshold - abs(x)) / x_threshold - 0.5
        r2 = (theta_threshold - abs(theta)) / theta_threshold - 0.5
        return float(r1 + r2)
    raise ValueError(f"Unknown reward shaping style: {style}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", default="CartPole-v0", help="Gym environment id, e.g. CartPole-v0 or MountainCar-v0")
    parser.add_argument("--steps", type=int, default=3, help="Random no-render steps to run; capped at 100")
    parser.add_argument("--seed", type=int, default=1, help="Seed for env/action space when supported")
    parser.add_argument(
        "--reward-shaping",
        choices=["none", "mountaincar-legacy-scale", "mountaincar-position-bonus", "cartpole-balance"],
        default="none",
        help="Optional shaping calculation to report; no training uses it",
    )
    args = parser.parse_args()
    steps = max(0, min(args.steps, 100))

    try:
        import gym
        import numpy as np
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(json.dumps({"status": "missing_dependency", "error": repr(exc)}, indent=2), file=sys.stderr)
        return 2

    class TinyQNet(nn.Module):
        def __init__(self, state_dim: int, action_dim: int) -> None:
            super().__init__()
            self.fc1 = nn.Linear(state_dim, 16)
            self.out = nn.Linear(16, action_dim)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            return self.out(F.relu(self.fc1(x)))

    env = gym.make(args.env)
    try:
        try:
            reset_result = env.reset(seed=args.seed)
        except TypeError:
            if hasattr(env, "seed"):
                env.seed(args.seed)
            reset_result = env.reset()
        if hasattr(env.action_space, "seed"):
            env.action_space.seed(args.seed)

        state, reset_api = _obs_from_reset(reset_result)
        state_dim = _shape_size(getattr(env.observation_space, "shape", None))
        action_dim = int(getattr(env.action_space, "n", 0))
        if action_dim <= 0:
            raise RuntimeError("This probe only supports discrete action spaces with action_space.n")

        net = TinyQNet(state_dim, action_dim)
        with torch.no_grad():
            q_shape = list(net(torch.as_tensor(state, dtype=torch.float32).view(1, -1)).shape)

        transitions = []
        step_api = "not_stepped"
        done_seen = False
        for _ in range(steps):
            action = int(env.action_space.sample())
            next_state, raw_reward, done, _info, step_api = _step_parts(env.step(action))
            shaped = _shaped_reward(args.reward_shaping, raw_reward, state, next_state, env.unwrapped)
            transitions.append({"action": action, "raw_reward": raw_reward, "shaped_reward": shaped, "done": done})
            state = next_state
            done_seen = done_seen or done
            if done:
                state, _ = _obs_from_reset(env.reset())

        report = {
            "status": "ok",
            "env_id": args.env,
            "gym_version": getattr(gym, "__version__", "unknown"),
            "torch_version": getattr(torch, "__version__", "unknown"),
            "reset_api": reset_api,
            "step_api": step_api,
            "state_dim": state_dim,
            "action_dim": action_dim,
            "tiny_q_output_shape": q_shape,
            "repo_numpy_replay_row_width": state_dim * 2 + 2,
            "repo_list_replay_transition_fields": ["state", "action", "reward", "next_state"],
            "steps_run": steps,
            "done_seen": done_seen,
            "reward_shaping": args.reward_shaping,
            "transitions": transitions,
        }
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    finally:
        env.close()


if __name__ == "__main__":
    raise SystemExit(main())
