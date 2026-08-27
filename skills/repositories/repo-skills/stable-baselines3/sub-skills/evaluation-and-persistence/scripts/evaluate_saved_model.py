#!/usr/bin/env python3
"""Evaluate a saved Stable-Baselines3 model zip by algorithm name and Gymnasium env id."""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import Any

ALGORITHM_NAMES = ("A2C", "DDPG", "DQN", "PPO", "SAC", "TD3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate a saved Stable-Baselines3 .zip model on a Gymnasium environment.",
    )
    parser.add_argument("--model", required=True, help="Path to the saved SB3 .zip model.")
    parser.add_argument(
        "--algo",
        required=True,
        choices=ALGORITHM_NAMES,
        help="SB3 algorithm class used to load the model.",
    )
    parser.add_argument("--env-id", required=True, help="Gymnasium environment id, for example CartPole-v1.")
    parser.add_argument("--episodes", type=int, default=10, help="Number of evaluation episodes. Default: 10.")
    parser.add_argument(
        "--deterministic",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Use deterministic actions. Default: true; pass --no-deterministic for stochastic actions.",
    )
    parser.add_argument("--device", default="auto", help="Torch device passed to load(): auto, cpu, cuda, etc. Default: auto.")
    parser.add_argument("--render", action="store_true", help="Render the environment during evaluation.")
    parser.add_argument(
        "--reward-threshold",
        type=float,
        default=None,
        help="Optional minimum mean reward; evaluate_policy raises AssertionError if not exceeded.",
    )
    parser.add_argument(
        "--no-monitor",
        action="store_true",
        help="Do not wrap the evaluation env with Monitor. By default Monitor is used for reliable episode returns.",
    )
    parser.add_argument(
        "--print-system-info",
        action="store_true",
        help="Ask SB3 load() to print saved/current system information for portability debugging.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Optional environment reset seed before evaluation.")
    return parser.parse_args()


def load_algorithm(algo_name: str) -> Any:
    stable_baselines3 = importlib.import_module("stable_baselines3")
    return getattr(stable_baselines3, algo_name)


def make_eval_env(env_id: str, use_monitor: bool, seed: int | None) -> Any:
    gym = importlib.import_module("gymnasium")
    monitor_module = importlib.import_module("stable_baselines3.common.monitor")
    env = gym.make(env_id)
    if seed is not None:
        env.reset(seed=seed)
    if use_monitor:
        env = monitor_module.Monitor(env)
    return env


def main() -> int:
    args = parse_args()
    if args.episodes < 1:
        print("--episodes must be >= 1", file=sys.stderr)
        return 2

    evaluation_module = importlib.import_module("stable_baselines3.common.evaluation")
    algo_cls = load_algorithm(args.algo)
    eval_env = make_eval_env(args.env_id, use_monitor=not args.no_monitor, seed=args.seed)
    try:
        model = algo_cls.load(
            args.model,
            env=eval_env,
            device=args.device,
            print_system_info=args.print_system_info,
        )
        mean_reward, std_reward = evaluation_module.evaluate_policy(
            model,
            eval_env,
            n_eval_episodes=args.episodes,
            deterministic=args.deterministic,
            render=args.render,
            reward_threshold=args.reward_threshold,
            warn=not args.no_monitor,
        )
    finally:
        eval_env.close()

    mode = "deterministic" if args.deterministic else "stochastic"
    print(f"algorithm={args.algo}")
    print(f"env_id={args.env_id}")
    print(f"episodes={args.episodes}")
    print(f"mode={mode}")
    print(f"mean_reward={mean_reward:.6f}")
    print(f"std_reward={std_reward:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
