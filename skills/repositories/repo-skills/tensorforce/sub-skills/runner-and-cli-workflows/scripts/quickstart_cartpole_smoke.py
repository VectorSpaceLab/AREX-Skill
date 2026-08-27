#!/usr/bin/env python3
"""Bounded Tensorforce quickstart smoke for CartPole-style training and evaluation."""

from __future__ import annotations

import argparse
import json
from typing import Any

from tensorforce import Runner


def build_environment_spec(name: str, level: str) -> Any:
    if name == 'custom_cartpole':
        return dict(environment='custom_cartpole')
    if name == 'gym':
        return dict(environment='gym', level=level)
    raise ValueError(f'Unsupported environment: {name}')


def build_agent_spec(agent_name: str) -> Any:
    if agent_name == 'random':
        return 'random'

    if agent_name == 'ppo':
        return dict(
            agent='ppo',
            network='auto',
            batch_size=4,
            update_frequency=1,
            learning_rate=3e-4,
            multi_step=2,
            subsampling_fraction=0.33,
            likelihood_ratio_clipping=0.2,
            discount=0.99,
            predict_terminal_values=False,
            baseline=dict(type='auto', size=16, depth=1),
            baseline_optimizer=dict(optimizer='adam', learning_rate=1e-3, multi_step=2),
            state_preprocessing='linear_normalization',
            exploration=0.0,
            variable_noise=0.0,
            config=dict(device='CPU', eager_mode=True, tf_log_level=20),
        )

    raise ValueError(f'Unsupported agent: {agent_name}')


def summarize_runner(runner: Runner, run_label: str) -> dict[str, Any]:
    return dict(
        run=run_label,
        episodes=int(runner.episodes),
        timesteps=int(runner.timesteps),
        updates=int(runner.updates),
        returns=[float(x) for x in runner.episode_returns],
        episode_timesteps=[int(x) for x in runner.episode_timesteps],
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Tiny Tensorforce CartPole quickstart smoke using the public Runner API.'
    )
    parser.add_argument(
        '--agent', choices=('ppo', 'random'), default='ppo',
        help='Agent to train for the smoke run.'
    )
    parser.add_argument(
        '--environment', choices=('custom_cartpole', 'gym'), default='custom_cartpole',
        help='CartPole-style environment to use.'
    )
    parser.add_argument(
        '--level', default='CartPole-v1',
        help='Gym level when --environment gym is selected.'
    )
    parser.add_argument(
        '--max-episode-timesteps', type=int, default=20,
        help='Per-episode cap for the quick smoke run.'
    )
    parser.add_argument(
        '--train-episodes', type=int, default=3,
        help='Number of training episodes.'
    )
    parser.add_argument(
        '--eval-episodes', type=int, default=1,
        help='Number of deterministic evaluation episodes after training.'
    )
    parser.add_argument(
        '--mean-horizon', type=int, default=1,
        help='Averaging window for the evaluation pass.'
    )
    parser.add_argument(
        '--tqdm', action='store_true',
        help='Show tqdm progress bars.'
    )
    args = parser.parse_args()

    if args.train_episodes < 0 or args.eval_episodes < 0:
        raise SystemExit('train-episodes and eval-episodes must be non-negative')
    if args.train_episodes == 0 and args.eval_episodes == 0:
        raise SystemExit('at least one of train-episodes or eval-episodes must be positive')

    environment = build_environment_spec(args.environment, args.level)
    agent = build_agent_spec(args.agent)

    runner = Runner(agent=agent, environment=environment, max_episode_timesteps=args.max_episode_timesteps)
    try:
        result = dict(
            tensorforce='quickstart_cartpole_smoke',
            environment=args.environment,
            agent=args.agent,
            max_episode_timesteps=args.max_episode_timesteps,
        )

        if args.train_episodes > 0:
            runner.run(
                num_episodes=args.train_episodes,
                use_tqdm=args.tqdm,
                mean_horizon=args.mean_horizon,
            )
            result['training'] = summarize_runner(runner, 'training')

        if args.eval_episodes > 0:
            runner.run(
                num_episodes=args.eval_episodes,
                evaluation=True,
                use_tqdm=args.tqdm,
                mean_horizon=args.mean_horizon,
            )
            result['evaluation'] = summarize_runner(runner, 'evaluation')

        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        runner.close()


if __name__ == '__main__':
    main()
