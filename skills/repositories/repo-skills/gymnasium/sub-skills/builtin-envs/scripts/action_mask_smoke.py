#!/usr/bin/env python3
"""Short Taxi-v4 action-mask smoke test for Gymnasium.

This script intentionally avoids full Q-learning. It verifies that Taxi-v4 can be
created, reset with a seed, expose info["action_mask"], choose valid masked
actions for a few steps, and close cleanly.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from typing import Any


ACTION_NAMES = {
    0: "south",
    1: "north",
    2: "east",
    3: "west",
    4: "pickup",
    5: "dropoff",
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create Taxi-v4, read info['action_mask'], choose valid masked "
            "actions for a short rollout, and print mask/action/reward signals."
        )
    )
    parser.add_argument("--env-id", default="Taxi-v4", help="Environment ID to create.")
    parser.add_argument("--seed", type=int, default=123, help="Seed passed to reset and action_space.")
    parser.add_argument("--steps", type=int, default=8, help="Maximum number of steps to run.")
    parser.add_argument(
        "--prefer-first",
        action="store_true",
        help="Choose the first valid action instead of sampling from the mask.",
    )
    parser.add_argument(
        "--render-mode",
        default=None,
        choices=["ansi", "rgb_array", "human"],
        help="Optional render mode for Taxi-v4 diagnostics.",
    )
    return parser.parse_args(argv)


def mask_values(mask: Any) -> list[int]:
    if hasattr(mask, "tolist"):
        values = mask.tolist()
    else:
        values = list(mask)
    return [int(value) for value in values]


def valid_action_indices(mask: Any) -> list[int]:
    return [index for index, value in enumerate(mask_values(mask)) if value == 1]


def choose_masked_action(env: Any, mask: Any | None, prefer_first: bool) -> int:
    if mask is None:
        return int(env.action_space.sample())

    valid_actions = valid_action_indices(mask)
    if len(valid_actions) == 0:
        return int(env.action_space.sample())

    if prefer_first:
        return int(valid_actions[0])

    return int(env.action_space.sample(mask))


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")

    import gymnasium as gym

    env = gym.make(args.env_id, render_mode=args.render_mode)
    try:
        env.action_space.seed(args.seed)
        observation, info = env.reset(seed=args.seed)
        print(f"env_id={args.env_id}")
        print(f"initial_observation={observation}")
        print(f"render_modes={env.metadata.get('render_modes', [])}")

        mask = info.get("action_mask")
        if mask is None:
            print("initial_action_mask=None")
        else:
            print(f"initial_action_mask={mask_values(mask)}")

        for step_index in range(args.steps):
            action = choose_masked_action(env, mask, args.prefer_first)
            action_name = ACTION_NAMES.get(action, str(action))
            observation, reward, terminated, truncated, info = env.step(action)
            next_mask = info.get("action_mask")
            printable_next_mask = None if next_mask is None else mask_values(next_mask)
            print(
                "step="
                f"{step_index} action={action}:{action_name} reward={reward} "
                f"terminated={terminated} truncated={truncated} "
                f"next_observation={observation} next_action_mask={printable_next_mask}"
            )

            if terminated or truncated:
                print("episode_finished=True")
                break

            mask = next_mask
    finally:
        env.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
