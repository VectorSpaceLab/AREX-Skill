#!/usr/bin/env python3
"""Construct and inspect tiny procedural Tianshou DQN components.

This script intentionally avoids full training, rendering, TensorBoard, and any
source-checkout dependency. It is a bounded smoke helper for installed Tianshou,
Gymnasium, and PyTorch environments.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ComponentSummary:
    task: str
    state_shape: Any
    action_shape: Any
    action_space: str
    collected_steps: int
    sampled_batch_size: int
    forward_action_shape: tuple[int, ...]
    logits_shape: tuple[int, ...]
    trainer_param_class: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke-check Tianshou procedural DQN components without full training.",
    )
    parser.add_argument("--task", default="CartPole-v1", help="Gymnasium discrete-action task.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for envs, NumPy, and Torch.")
    parser.add_argument("--hidden-size", type=int, default=16, help="Width of the tiny MLP layers.")
    parser.add_argument("--num-envs", type=int, default=2, help="Number of DummyVectorEnv training envs.")
    parser.add_argument("--buffer-size", type=int, default=128, help="Vector replay buffer capacity.")
    parser.add_argument("--batch-size", type=int, default=4, help="Sample size for a replay-buffer smoke.")
    parser.add_argument("--collect-steps", type=int, default=8, help="Number of env steps to collect.")
    parser.add_argument("--device", default="cpu", help="Torch device for the tiny network.")
    return parser.parse_args()


def make_env(gym: Any, task: str, seed: int | None = None) -> Any:
    env = gym.make(task)
    if seed is not None:
        env.reset(seed=seed)
    return env


def build_components(args: argparse.Namespace) -> ComponentSummary:
    import gymnasium as gym
    import numpy as np
    import torch

    import tianshou as ts
    from tianshou.algorithm.modelfree.dqn import DiscreteQLearningPolicy
    from tianshou.algorithm.optim import AdamOptimizerFactory
    from tianshou.data import Batch, CollectStats, Collector, VectorReplayBuffer
    from tianshou.env import DummyVectorEnv
    from tianshou.trainer import OffPolicyTrainerParams
    from tianshou.utils.net.common import Net
    from tianshou.utils.space_info import SpaceInfo
    from tianshou.utils.torch_utils import policy_within_training_step

    if args.num_envs < 1:
        raise ValueError("--num-envs must be >= 1")
    if args.batch_size < 1:
        raise ValueError("--batch-size must be >= 1")
    if args.collect_steps < args.batch_size:
        raise ValueError("--collect-steps must be at least --batch-size")

    np.random.seed(args.seed)
    torch.manual_seed(args.seed)

    probe_env = make_env(gym, args.task, args.seed)
    if not isinstance(probe_env.action_space, gym.spaces.Discrete):
        raise TypeError(
            f"This DQN smoke requires gym.spaces.Discrete, got {probe_env.action_space!r}",
        )

    space_info = SpaceInfo.from_env(probe_env)
    state_shape = space_info.observation_info.obs_shape
    action_shape = space_info.action_info.action_shape

    training_envs = DummyVectorEnv(
        [lambda task=args.task: make_env(gym, task) for _ in range(args.num_envs)],
    )
    training_envs.seed(args.seed)

    net = Net(
        state_shape=state_shape,
        action_shape=action_shape,
        hidden_sizes=[args.hidden_size, args.hidden_size],
    ).to(args.device)
    policy = DiscreteQLearningPolicy(
        model=net,
        action_space=probe_env.action_space,
        observation_space=probe_env.observation_space,
        eps_training=0.1,
        eps_inference=0.0,
    )
    algorithm = ts.algorithm.DQN(
        policy=policy,
        optim=AdamOptimizerFactory(lr=1e-3),
        gamma=0.9,
        n_step_return_horizon=1,
        target_update_freq=0,
    )
    buffer = VectorReplayBuffer(args.buffer_size, buffer_num=len(training_envs))
    collector = Collector[CollectStats](
        algorithm,
        training_envs,
        buffer,
        exploration_noise=True,
    )

    collector.reset()
    with policy_within_training_step(policy):
        collect_stats = collector.collect(n_step=args.collect_steps)

    sample_batch, _ = buffer.sample(args.batch_size)
    obs_batch = Batch(obs=sample_batch.obs, info=sample_batch.info)
    forward_result = policy(obs_batch)

    trainer_params = OffPolicyTrainerParams(
        training_collector=collector,
        max_epochs=1,
        epoch_num_steps=args.collect_steps,
        collection_step_num_env_steps=args.collect_steps,
        test_step_num_episodes=1,
        batch_size=args.batch_size,
        update_step_num_gradient_steps_per_sample=0.0,
    )

    action_space = repr(probe_env.action_space)
    probe_env.close()
    training_envs.close()

    return ComponentSummary(
        task=args.task,
        state_shape=state_shape,
        action_shape=action_shape,
        action_space=action_space,
        collected_steps=int(collect_stats.n_collected_steps),
        sampled_batch_size=len(sample_batch),
        forward_action_shape=tuple(np.asarray(forward_result.act).shape),
        logits_shape=tuple(forward_result.logits.shape),
        trainer_param_class=type(trainer_params).__name__,
    )


def main() -> None:
    args = parse_args()
    summary = build_components(args)
    print("Tianshou procedural DQN component smoke passed")
    for field_name, value in summary.__dict__.items():
        print(f"{field_name}: {value}")


if __name__ == "__main__":
    main()
