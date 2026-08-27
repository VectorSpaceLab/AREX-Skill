#!/usr/bin/env python3
"""Bounded, no-render DeepQNetwork CartPole smoke for ML-From-Scratch."""

from __future__ import annotations

import argparse
import os
import random
import sys
from typing import Any, Callable

os.environ.setdefault("MPLBACKEND", "Agg")
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")


def load_runtime_modules() -> None:
    """Import Gym and ML-From-Scratch only after argparse has handled --help."""
    global np, gym, NeuralNetwork, Activation, Dense, SquareLoss, Adam, DeepQNetwork

    import numpy as np_module

    # Gym releases used by this educational package may still reference np.bool8.
    # NumPy 2 removed that alias; keep the workaround process-local to this script.
    if "bool8" not in np_module.__dict__:
        np_module.bool8 = np_module.bool_

    import gym as gym_module
    from mlfromscratch.deep_learning import NeuralNetwork as NeuralNetwork_module
    from mlfromscratch.deep_learning.layers import Activation as Activation_module
    from mlfromscratch.deep_learning.layers import Dense as Dense_module
    from mlfromscratch.deep_learning.loss_functions import SquareLoss as SquareLoss_module
    from mlfromscratch.deep_learning.optimizers import Adam as Adam_module
    from mlfromscratch.reinforcement_learning import DeepQNetwork as DeepQNetwork_module

    np = np_module
    gym = gym_module
    NeuralNetwork = NeuralNetwork_module
    Activation = Activation_module
    Dense = Dense_module
    SquareLoss = SquareLoss_module
    Adam = Adam_module
    DeepQNetwork = DeepQNetwork_module


class OldGymAPIAdapter:
    """Expose reset/step outputs in the form expected by DeepQNetwork.train."""

    def __init__(self, env: Any, max_steps: int, seed: int | None) -> None:
        self._env = env
        self.max_steps = max_steps
        self.seed = seed
        self.steps = 0
        self.resets = 0
        if seed is not None:
            for space_name in ("action_space", "observation_space"):
                space = getattr(env, space_name, None)
                if hasattr(space, "seed"):
                    space.seed(seed)

    @property
    def observation_space(self) -> Any:
        return self._env.observation_space

    @property
    def action_space(self) -> Any:
        return self._env.action_space

    def reset(self, *args: Any, **kwargs: Any) -> np.ndarray:
        self.steps = 0
        if self.seed is not None and "seed" not in kwargs:
            kwargs["seed"] = self.seed + self.resets
        self.resets += 1

        try:
            out = self._env.reset(*args, **kwargs)
        except TypeError:
            # Older Gym did not accept reset(seed=...). Seed separately if possible.
            seed = kwargs.pop("seed", None)
            if seed is not None and hasattr(self._env, "seed"):
                self._env.seed(seed)
            out = self._env.reset(*args, **kwargs)

        obs = out[0] if isinstance(out, tuple) and len(out) == 2 else out
        return np.asarray(obs, dtype=float)

    def step(self, action: int) -> tuple[np.ndarray, float, bool, dict[str, Any]]:
        out = self._env.step(action)
        if len(out) == 5:
            obs, reward, terminated, truncated, info = out
            done = bool(terminated or truncated)
        elif len(out) == 4:
            obs, reward, done, info = out
            done = bool(done)
        else:
            raise RuntimeError(f"Unsupported Gym step output length: {len(out)!r}")

        self.steps += 1
        if self.max_steps and self.steps >= self.max_steps:
            done = True
            info = dict(info or {})
            info["dqn_smoke_time_limit"] = True

        return np.asarray(obs, dtype=float), float(reward), done, dict(info or {})

    def render(self, *args: Any, **kwargs: Any) -> Any:
        return self._env.render(*args, **kwargs)

    def close(self) -> None:
        self._env.close()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._env, name)


def build_model(n_inputs: int, n_outputs: int, hidden_units: int, learning_rate: float) -> NeuralNetwork:
    """Small DQN model builder matching DeepQNetwork.set_model's callback contract."""
    model = NeuralNetwork(optimizer=Adam(learning_rate=learning_rate), loss=SquareLoss)
    model.add(Dense(hidden_units, input_shape=(n_inputs,)))
    model.add(Activation("relu"))
    model.add(Dense(n_outputs))
    return model


def patched_gym_make(original_make: Callable[..., Any], max_steps: int, seed: int | None) -> Callable[..., Any]:
    def make(env_name: str, *args: Any, **kwargs: Any) -> OldGymAPIAdapter:
        env = original_make(env_name, *args, **kwargs)
        return OldGymAPIAdapter(env, max_steps=max_steps, seed=seed)

    return make


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a bounded, no-render ML-From-Scratch DeepQNetwork smoke on CartPole. "
            "The script adapts Gym reset/step outputs to the old API expected by the package."
        )
    )
    parser.add_argument("--env-name", default="CartPole-v1", help="Gym environment name (default: CartPole-v1).")
    parser.add_argument("--epochs", type=int, default=1, help="Training epochs; default is one smoke epoch.")
    parser.add_argument("--max-steps", type=int, default=8, help="Maximum steps per epoch before forced done.")
    parser.add_argument("--batch-size", type=int, default=4, help="Replay batch size for the smoke.")
    parser.add_argument("--hidden-units", type=int, default=8, help="Hidden units in the tiny DQN model.")
    parser.add_argument("--learning-rate", type=float, default=0.001, help="Adam learning rate for the tiny model.")
    parser.add_argument("--seed", type=int, default=13, help="Seed for Python, NumPy, and Gym spaces.")
    parser.add_argument("--summary", action="store_true", help="Print the tiny model summary before training.")
    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    for name in ("epochs", "max_steps", "batch_size", "hidden_units"):
        value = getattr(args, name)
        if value < 1:
            raise SystemExit(f"--{name.replace('_', '-')} must be >= 1")
    if args.learning_rate <= 0:
        raise SystemExit("--learning-rate must be > 0")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    validate_args(args)

    load_runtime_modules()

    random.seed(args.seed)
    np.random.seed(args.seed)

    original_make = gym.make
    gym.make = patched_gym_make(original_make, max_steps=args.max_steps, seed=args.seed)
    dqn: DeepQNetwork | None = None
    try:
        # epsilon=1.0 intentionally keeps smoke action selection random, avoiding the
        # package's greedy 1-D state prediction edge during the episode.
        dqn = DeepQNetwork(env_name=args.env_name, epsilon=1.0, gamma=0.9, decay_rate=0.005, min_epsilon=0.1)
        dqn.set_model(lambda n_inputs, n_outputs: build_model(n_inputs, n_outputs, args.hidden_units, args.learning_rate))

        probe = dqn.model.predict(np.zeros((1, dqn.n_states), dtype=float))
        expected_shape = (1, dqn.n_actions)
        if probe.shape != expected_shape:
            raise AssertionError(f"model output shape {probe.shape!r} != expected {expected_shape!r}")

        if args.summary:
            dqn.model.summary(name="DQN Smoke Model")

        dqn.train(n_epochs=args.epochs, batch_size=args.batch_size)
        print(
            "DQN smoke passed: "
            f"env={args.env_name} states={dqn.n_states} actions={dqn.n_actions} "
            f"epochs={args.epochs} max_steps={args.max_steps} memory={len(dqn.memory)} "
            f"epsilon={dqn.epsilon:.4f}"
        )
        return 0
    finally:
        gym.make = original_make
        if dqn is not None:
            try:
                dqn.env.close()
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
