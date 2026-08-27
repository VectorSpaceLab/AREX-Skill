#!/usr/bin/env python3
"""CPU-only Tensorforce custom Environment smoke check.

This script is self-contained: it uses only an installed Tensorforce package plus
NumPy, defines its own custom environment class, and performs bounded checks for
Environment.create(), reward shaping, close(), and time-limit abort terminals.
"""

import argparse
import json

import numpy as np

from tensorforce import Environment


class CounterEnvironment(Environment):
    """Tiny deterministic custom environment for Tensorforce API smoke tests."""

    def __init__(self, goal=50, start=0):
        super().__init__()
        self.goal = int(goal)
        self.start = float(start)
        self.position = None
        self.num_steps = None
        self.closed = False

    def states(self):
        return dict(
            type='float', shape=(2,), min_value=0.0, max_value=float(max(self.goal, self.start) + 5)
        )

    def actions(self):
        return dict(type='int', shape=(), num_values=3)

    def reset(self):
        self.position = self.start
        self.num_steps = 0
        return self._state()

    def execute(self, actions):
        if self.position is None:
            raise RuntimeError('CounterEnvironment.reset() must be called before execute().')

        action = int(np.asarray(actions).item())
        if action < 0 or action >= 3:
            raise ValueError('Expected scalar action in {0, 1, 2}; got {!r}.'.format(actions))

        self.num_steps += 1
        self.position = float(np.clip(self.position + (action - 1), 0.0, float(self.goal)))
        terminal = self.position >= float(self.goal)
        reward = 1.0 if action == 2 else -0.1
        return self._state(), terminal, float(reward)

    def close(self):
        self.closed = True

    def _state(self):
        return np.asarray([self.position, float(self.goal)], dtype=np.float32)


def callable_reward_shaping(states, actions, terminal, reward, next_states):
    del states, actions, next_states
    return float(reward) + 0.25, terminal


def run_custom_class_smoke(max_timesteps, goal):
    env = Environment.create(
        environment=dict(
            environment=CounterEnvironment,
            goal=goal,
            start=0,
            max_episode_timesteps=max_timesteps,
        ),
        reward_shaping=callable_reward_shaping,
    )
    try:
        assert env.max_episode_timesteps() == max_timesteps, env.max_episode_timesteps()
        state = env.reset()
        assert isinstance(state, np.ndarray), type(state)
        assert state.shape == (2,), state.shape

        terminals = []
        rewards = []
        for _ in range(max_timesteps):
            state, terminal, reward = env.execute(actions=1)  # no-op: never reaches natural goal
            assert state.shape == (2,), state.shape
            terminals.append(int(terminal))
            rewards.append(float(reward))

        assert terminals[:-1] == [0] * (max_timesteps - 1), terminals
        assert terminals[-1] == 2, terminals
        assert np.isclose(rewards[0], 0.15), rewards
    finally:
        env.close()

    assert env.closed is True
    return dict(terminals=terminals, rewards=rewards, closed=env.closed)


def run_string_reward_shaping_smoke(goal):
    env = Environment.create(
        environment=CounterEnvironment,
        goal=goal,
        start=0,
        max_episode_timesteps=1,
        reward_shaping='reward + 0.5',
    )
    try:
        env.reset()
        _, terminal, reward = env.execute(actions=2)
        assert int(terminal) == 2, terminal
        assert np.isclose(float(reward), 1.5), reward
    finally:
        env.close()
    return dict(terminal=int(terminal), reward=float(reward))


def run_builtin_custom_cartpole_smoke():
    env = Environment.create(environment='custom_cartpole', max_episode_timesteps=5)
    try:
        states_spec = env.states()
        actions_spec = env.actions()
        states = env.reset()
        if actions_spec.get('type') == 'int':
            action = min(1, int(actions_spec.get('num_values', 1)) - 1)
        else:
            action = 0.0
        next_states, terminal, reward = env.execute(actions=action)
        assert int(terminal) in (0, 1, 2), terminal
        assert isinstance(float(reward), float)
    finally:
        env.close()
    return dict(
        states_spec=states_spec,
        actions_spec=actions_spec,
        first_state_shape=list(np.asarray(states).shape),
        next_state_shape=list(np.asarray(next_states).shape),
        terminal=int(terminal),
        reward=float(reward),
    )


def to_jsonable(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--max-timesteps', type=int, default=3,
        help='Wrapper time limit for the custom environment smoke (default: 3).'
    )
    parser.add_argument(
        '--goal', type=int, default=50,
        help='Natural goal kept above the time limit so terminal=2 is tested (default: 50).'
    )
    parser.add_argument(
        '--skip-built-in-custom-cartpole', dest='skip_builtin_custom_cartpole', action='store_true',
        help='Skip the extra built-in custom_cartpole one-step smoke.'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    if args.max_timesteps < 1:
        raise SystemExit('--max-timesteps must be >= 1')
    if args.goal <= args.max_timesteps + 1:
        raise SystemExit('--goal must be greater than --max-timesteps + 1 for abort-terminal check')

    result = dict(
        status='ok',
        custom_class=run_custom_class_smoke(max_timesteps=args.max_timesteps, goal=args.goal),
        string_reward_shaping=run_string_reward_shaping_smoke(goal=args.goal),
    )
    if not args.skip_builtin_custom_cartpole:
        result['builtin_custom_cartpole'] = run_builtin_custom_cartpole_smoke()

    print(json.dumps(to_jsonable(result), indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
