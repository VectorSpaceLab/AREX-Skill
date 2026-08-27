#!/usr/bin/env python3
"""
Tiny Tensorforce act/observe smoke test.

Purpose:
  Validate Agent.create(..., environment=...), the non-independent act/observe
  sequence, and an independent deterministic evaluation call using a built-in
  or high-level Tensorforce agent alias.

Examples:
  python scripts/act_observe_smoke.py --episodes 1 --max-timesteps 3
  python scripts/act_observe_smoke.py --agent ppo --episodes 1 --max-timesteps 4 --batch-size 2

The script is self-contained and does not read the original Tensorforce checkout.
Default agent "random" is intentionally cheap and deterministic enough for API
validation; use trainable aliases only when the runtime TensorFlow stack is ready.
"""

import argparse
import os
import sys
from typing import Sequence

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np


def _import_tensorforce():
    try:
        from tensorforce import Agent, Environment
    except Exception as exc:  # pragma: no cover - diagnostic user interface
        print(
            "Failed to import Tensorforce. Use a Tensorforce 0.6.x-compatible "
            "Python/TensorFlow/Gym/NumPy environment before debugging interaction loops.\n"
            f"Import error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return None, None
    return Agent, Environment


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny Tensorforce Agent.act/observe smoke loop."
    )
    parser.add_argument(
        "--agent", choices=("random", "ppo", "tensorforce"), default="random",
        help="Agent alias to construct (default: random).",
    )
    parser.add_argument(
        "--episodes", type=int, default=2,
        help="Number of online act/observe episodes (default: 2).",
    )
    parser.add_argument(
        "--max-timesteps", type=int, default=5,
        help="Maximum timesteps per tiny episode (default: 5).",
    )
    parser.add_argument(
        "--batch-size", type=int, default=2,
        help="Batch size for trainable aliases ppo/tensorforce (default: 2).",
    )
    parser.add_argument(
        "--seed", type=int, default=7,
        help="Random seed passed to Tensorforce config and NumPy (default: 7).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print every transition instead of only episode summaries.",
    )
    return parser.parse_args(argv)


def build_agent_kwargs(agent_alias: str, batch_size: int, seed: int):
    config = dict(device="CPU", seed=seed, tf_log_level=40)
    if agent_alias == "random":
        return dict(agent="random", config=config)
    if agent_alias == "ppo":
        return dict(
            agent="ppo",
            batch_size=batch_size,
            network=dict(type="auto", size=8, depth=1),
            update_frequency=1.0,
            learning_rate=1e-3,
            config=config,
        )
    if agent_alias == "tensorforce":
        return dict(
            agent="tensorforce",
            update=batch_size,
            optimizer=dict(optimizer="adam", learning_rate=1e-3),
            objective="policy_gradient",
            reward_estimation=dict(horizon=1),
            policy=dict(network=dict(type="auto", size=8, depth=1)),
            config=config,
        )
    raise ValueError(agent_alias)


def make_tiny_environment_class(EnvironmentBase, horizon: int):
    class TinyLineWorld(EnvironmentBase):
        """Two-action line world with a float vector state."""

        def __init__(self):
            super().__init__()
            self.position = 0.0
            self.timestep = 0

        def states(self):
            bound = float(max(1, horizon))
            return dict(type="float", shape=(2,), min_value=-bound, max_value=bound)

        def actions(self):
            return dict(type="int", shape=(), num_values=2)

        def max_episode_timesteps(self):
            return horizon

        def reset(self):
            self.position = 0.0
            self.timestep = 0
            return np.asarray([self.position, 0.0], dtype=np.float32)

        def execute(self, actions):
            action = int(actions)
            if action not in (0, 1):
                raise ValueError(f"Expected action 0 or 1, received {action!r}")
            self.timestep += 1
            self.position += 1.0 if action == 1 else -1.0
            terminal = self.timestep >= horizon
            reward = 1.0 if action == 1 else -0.25
            state = np.asarray(
                [self.position, self.timestep / float(horizon)], dtype=np.float32
            )
            return state, terminal, reward

    TinyLineWorld.__name__ = "TinyLineWorld"
    return TinyLineWorld


def main(argv: Sequence[str] = tuple()) -> int:
    args = parse_args(argv)
    if args.episodes <= 0:
        print("--episodes must be positive", file=sys.stderr)
        return 2
    if args.max_timesteps <= 0:
        print("--max-timesteps must be positive", file=sys.stderr)
        return 2
    if args.batch_size <= 0:
        print("--batch-size must be positive", file=sys.stderr)
        return 2

    Agent, Environment = _import_tensorforce()
    if Agent is None:
        return 2

    np.random.seed(args.seed)
    environment = None
    agent = None
    try:
        TinyLineWorld = make_tiny_environment_class(Environment, args.max_timesteps)
        environment = Environment.create(
            environment=TinyLineWorld,
            max_episode_timesteps=args.max_timesteps,
        )
        agent = Agent.create(
            environment=environment,
            **build_agent_kwargs(args.agent, args.batch_size, args.seed),
        )

        total_updates = 0
        total_reward = 0.0
        for episode in range(args.episodes):
            states = environment.reset()
            terminal = False
            episode_reward = 0.0
            timestep = 0
            while not terminal:
                actions = agent.act(states=states)
                states, terminal, reward = environment.execute(actions=actions)
                updates = agent.observe(terminal=terminal, reward=reward)
                total_updates += int(updates)
                episode_reward += float(reward)
                timestep += 1
                if args.verbose:
                    print(
                        f"episode={episode} timestep={timestep} action={int(actions)} "
                        f"terminal={terminal} reward={reward} updates={updates}"
                    )
            total_reward += episode_reward
            print(
                f"episode={episode} timesteps={timestep} "
                f"return={episode_reward:.3f} updates_so_far={total_updates}"
            )

        # Independent probe/evaluation call: no observe follows this action.
        states = environment.reset()
        internals = agent.initial_internals()
        actions, next_internals = agent.act(
            states=states,
            internals=internals,
            independent=True,
            deterministic=True,
        )
        print(
            "independent_probe "
            f"action={int(actions)} internals_keys={list(next_internals.keys())}"
        )
        print(
            "PASSED act/observe smoke: "
            f"agent={args.agent} episodes={args.episodes} "
            f"max_timesteps={args.max_timesteps} total_return={total_reward:.3f} "
            f"total_updates={total_updates}"
        )
        return 0

    finally:
        if agent is not None:
            agent.close()
        if environment is not None:
            environment.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
