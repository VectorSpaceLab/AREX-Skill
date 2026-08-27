#!/usr/bin/env python3
"""Build a tiny Tianshou high-level CartPole DQN experiment.

The default mode performs imports and builder construction only. It does not
train, render, download assets, or require the original Tianshou checkout.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_experiment(args: argparse.Namespace) -> Any:
    from tianshou.highlevel.config import OffPolicyTrainingConfig
    from tianshou.highlevel.env import EnvFactoryRegistered, VectorEnvType
    from tianshou.highlevel.experiment import DQNExperimentBuilder, ExperimentConfig
    from tianshou.highlevel.params.algorithm_params import DQNParams
    from tianshou.highlevel.trainer import EpochStopCallbackRewardThreshold

    env_factory = EnvFactoryRegistered(task=args.task, venv_type=VectorEnvType.DUMMY)
    experiment_config = ExperimentConfig(
        seed=args.seed,
        device=args.device,
        persistence_enabled=False,
        log_file_enabled=False,
        watch=False,
    )
    training_config = OffPolicyTrainingConfig(
        max_epochs=args.max_epochs,
        epoch_num_steps=args.epoch_steps,
        num_training_envs=args.training_envs,
        num_test_envs=args.test_envs,
        test_step_num_episodes=args.test_envs,
        buffer_size=args.buffer_size,
        batch_size=args.batch_size,
        collection_step_num_env_steps=args.collect_steps,
        update_step_num_gradient_steps_per_sample=args.update_ratio,
        start_timesteps=0,
        start_timesteps_random=False,
    )

    builder = (
        DQNExperimentBuilder(env_factory, experiment_config, training_config)
        .with_dqn_params(
            DQNParams(
                lr=args.lr,
                gamma=args.gamma,
                n_step_return_horizon=args.n_step,
                target_update_freq=args.target_update_freq,
                eps_training=args.eps_training,
                eps_inference=args.eps_inference,
            )
        )
        .with_model_factory_default(hidden_sizes=tuple(args.hidden_sizes))
        .with_epoch_stop_callback(EpochStopCallbackRewardThreshold(args.reward_threshold))
        .with_name(args.run_name)
    )
    return builder.build()


def summarize(experiment: Any, ran_training: bool) -> dict[str, Any]:
    config = experiment.config
    training_config = experiment.training_config
    return {
        "ok": True,
        "ran_training": ran_training,
        "experiment_name": experiment.name,
        "task": experiment.env_factory.task,
        "venv_type": experiment.env_factory.venv_type.value,
        "device": str(config.device),
        "persistence_enabled": config.persistence_enabled,
        "log_file_enabled": config.log_file_enabled,
        "watch": config.watch,
        "training_config": {
            key: value
            for key, value in asdict(training_config).items()
            if key
            in {
                "max_epochs",
                "epoch_num_steps",
                "num_training_envs",
                "num_test_envs",
                "test_step_num_episodes",
                "buffer_size",
                "batch_size",
                "collection_step_num_env_steps",
                "update_step_num_gradient_steps_per_sample",
            }
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import Tianshou high-level APIs and build a tiny CartPole DQN experiment."
    )
    parser.add_argument("--task", default="CartPole-v1", help="Gymnasium task id to construct.")
    parser.add_argument("--seed", type=int, default=42, help="Experiment seed.")
    parser.add_argument("--device", default="cpu", help="Torch device for the high-level experiment.")
    parser.add_argument("--run-name", default="cartpole_dqn_highlevel_smoke", help="Experiment name.")
    parser.add_argument("--max-epochs", type=positive_int, default=1, help="Tiny training epoch count.")
    parser.add_argument("--epoch-steps", type=positive_int, default=32, help="Environment steps per epoch.")
    parser.add_argument("--training-envs", type=positive_int, default=1, help="Training vector env count.")
    parser.add_argument("--test-envs", type=positive_int, default=1, help="Test vector env count.")
    parser.add_argument("--buffer-size", type=positive_int, default=256, help="Replay buffer size.")
    parser.add_argument("--batch-size", type=positive_int, default=32, help="DQN batch size.")
    parser.add_argument("--collect-steps", type=positive_int, default=8, help="Collection steps per training step.")
    parser.add_argument("--update-ratio", type=float, default=0.125, help="Gradient steps per collected sample.")
    parser.add_argument("--lr", type=float, default=1e-3, help="DQN learning rate.")
    parser.add_argument("--gamma", type=float, default=0.9, help="Discount factor.")
    parser.add_argument("--n-step", type=positive_int, default=3, help="N-step return horizon.")
    parser.add_argument("--target-update-freq", type=int, default=32, help="DQN target update frequency.")
    parser.add_argument("--eps-training", type=float, default=0.1, help="Training epsilon.")
    parser.add_argument("--eps-inference", type=float, default=0.0, help="Inference epsilon.")
    parser.add_argument("--reward-threshold", type=float, default=195.0, help="Early-stop reward threshold.")
    parser.add_argument(
        "--hidden-sizes",
        type=positive_int,
        nargs="+",
        default=[64, 64],
        help="Hidden layer sizes for the default DQN model factory.",
    )
    parser.add_argument(
        "--run-tiny-training",
        action="store_true",
        help="Also call experiment.run(); still disables persistence and watch.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    experiment = build_experiment(args)
    ran_training = False
    if args.run_tiny_training:
        experiment.run(run_name=args.run_name, raise_error_on_dirname_collision=False)
        ran_training = True
    print(json.dumps(summarize(experiment, ran_training), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
