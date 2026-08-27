#!/usr/bin/env python3
"""CLI-like Tensorforce Runner smoke using only the public Runner API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
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


def to_list(values):
    return [float(value) if isinstance(value, (int, float)) else value for value in values]


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Safe CLI-like smoke wrapper around Tensorforce Runner.'
    )
    parser.add_argument(
        '--agent', choices=('random', 'ppo'), default='random',
        help='Agent to instantiate through Runner.'
    )
    parser.add_argument(
        '--environment', choices=('custom_cartpole', 'gym'), default='custom_cartpole',
        help='Environment specification used for the smoke run.'
    )
    parser.add_argument(
        '--level', default='CartPole-v1',
        help='Gym level when --environment gym is selected.'
    )
    parser.add_argument(
        '--max-episode-timesteps', type=int, default=10,
        help='Episode cap passed to Runner.'
    )
    parser.add_argument(
        '--episodes', type=int, default=3,
        help='Episode stopping criterion for the training phase.'
    )
    parser.add_argument(
        '--timesteps', type=int, default=None,
        help='Timestep stopping criterion for the training phase.'
    )
    parser.add_argument(
        '--updates', type=int, default=None,
        help='Update stopping criterion for the training phase.'
    )
    parser.add_argument(
        '--num-parallel', type=int, default=None,
        help='Number of environments to use in the training phase.'
    )
    parser.add_argument(
        '--remote', choices=('local', 'multiprocessing'), default='local',
        help='Remote execution mode for the training phase.'
    )
    parser.add_argument(
        '--blocking', action='store_true',
        help='Use blocking remote calls when remote multiprocessing is selected.'
    )
    parser.add_argument(
        '--batch-agent-calls', action='store_true',
        help='Batch agent.act/observe calls during parallel training.'
    )
    parser.add_argument(
        '--sync-timesteps', action='store_true',
        help='Synchronize parallel training by timestep.'
    )
    parser.add_argument(
        '--sync-episodes', action='store_true',
        help='Synchronize parallel training by episode.'
    )
    parser.add_argument(
        '--evaluation', action='store_true',
        help='Run a final deterministic evaluation pass when the training phase is single-env.'
    )
    parser.add_argument(
        '--evaluation-episodes', type=int, default=1,
        help='Number of episodes for the optional evaluation pass.'
    )
    parser.add_argument(
        '--save-best-agent', default=None,
        help='Directory to save the best agent during the evaluation pass.'
    )
    parser.add_argument(
        '--callback-episode-frequency', type=int, default=None,
        help='Episode frequency for a simple training callback.'
    )
    parser.add_argument(
        '--callback-timestep-frequency', type=int, default=None,
        help='Timestep frequency for a simple training callback.'
    )
    parser.add_argument(
        '--mean-horizon', type=int, default=1,
        help='Averaging window passed to Runner.run.'
    )
    parser.add_argument(
        '--tqdm', action='store_true',
        help='Show tqdm progress bars.'
    )
    args = parser.parse_args()

    if args.episodes < 0 or args.evaluation_episodes < 0:
        raise SystemExit('episodes and evaluation-episodes must be non-negative')
    if args.episodes == 0 and args.timesteps is None and args.updates is None:
        raise SystemExit('provide at least one training stopping criterion')
    if args.callback_episode_frequency is not None and args.callback_timestep_frequency is not None:
        raise SystemExit('choose either callback-episode-frequency or callback-timestep-frequency')
    if args.remote == 'local' and args.blocking:
        raise SystemExit('blocking is only valid with remote multiprocessing')

    remote = None if args.remote == 'local' else 'multiprocessing'
    environment = build_environment_spec(args.environment, args.level)
    agent = build_agent_spec(args.agent)

    if (
        remote is None and args.num_parallel is not None and args.num_parallel > 1 and
        args.environment == 'custom_cartpole' and
        (args.batch_agent_calls or args.sync_timesteps or args.sync_episodes)
    ):
        raise SystemExit(
            'local custom_cartpole is vectorizable; omit batch/sync flags or use multiprocessing'
        )

    runner = Runner(
        agent=agent,
        environment=environment,
        max_episode_timesteps=args.max_episode_timesteps,
        num_parallel=args.num_parallel,
        remote=remote,
        blocking=args.blocking,
    )

    callback_events = []

    def callback(runner_obj, parallel):
        callback_events.append(dict(
            episodes=int(runner_obj.episodes),
            timesteps=int(runner_obj.timesteps),
            updates=int(runner_obj.updates),
            parallel=int(parallel),
            episode_timestep=int(runner_obj.episode_timestep[parallel]),
            episode_return=float(runner_obj.episode_return[parallel]),
        ))
        return True

    if callback_events:
        raise AssertionError('callback_events should start empty')

    try:
        training_kwargs = dict(
            num_episodes=args.episodes if args.timesteps is None and args.updates is None else None,
            num_timesteps=args.timesteps,
            num_updates=args.updates,
            batch_agent_calls=args.batch_agent_calls,
            sync_timesteps=args.sync_timesteps,
            sync_episodes=args.sync_episodes,
            use_tqdm=args.tqdm,
            mean_horizon=args.mean_horizon,
        )
        if args.callback_episode_frequency is not None:
            training_kwargs['callback'] = callback
            training_kwargs['callback_episode_frequency'] = args.callback_episode_frequency
        elif args.callback_timestep_frequency is not None:
            training_kwargs['callback'] = callback
            training_kwargs['callback_timestep_frequency'] = args.callback_timestep_frequency

        runner.run(**training_kwargs)
        result = dict(
            tensorforce='runner_and_cli_workflows_smoke',
            agent=args.agent,
            environment=args.environment,
            remote=args.remote,
            num_parallel=args.num_parallel,
            training=dict(
                episodes=int(runner.episodes),
                timesteps=int(runner.timesteps),
                updates=int(runner.updates),
                returns=[float(x) for x in runner.episode_returns],
                episode_timesteps=[int(x) for x in runner.episode_timesteps],
                callback_events=callback_events,
            ),
        )

        evaluation_skipped = False
        if args.evaluation:
            if args.num_parallel is None or args.num_parallel == 1:
                if args.evaluation_episodes <= 0:
                    evaluation_skipped = True
                else:
                    runner.run(
                        num_episodes=args.evaluation_episodes,
                        evaluation=True,
                        use_tqdm=args.tqdm,
                        mean_horizon=args.mean_horizon,
                        save_best_agent=args.save_best_agent,
                    )
                    result['evaluation'] = dict(
                        episodes=int(runner.episodes),
                        timesteps=int(runner.timesteps),
                        updates=int(runner.updates),
                        returns=[float(x) for x in runner.evaluation_returns],
                        episode_timesteps=[int(x) for x in runner.evaluation_timesteps],
                    )
                    if args.save_best_agent is not None:
                        result['evaluation']['save_best_agent'] = args.save_best_agent
            else:
                evaluation_skipped = True

        if evaluation_skipped:
            result['evaluation_skipped'] = 'parallel training runner does not support an in-place evaluation pass'

        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        runner.close()


if __name__ == '__main__':
    main()
