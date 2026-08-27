#!/usr/bin/env python3
"""Environment wrapper smoke for DI-engine.

This script checks that DingEnvWrapper can normalize a representative Gym and
Gymnasium CartPole environment and generate collector/evaluator configs.
"""

from __future__ import annotations

from easydict import EasyDict
import gym
import gymnasium

from ding.envs import DingEnvWrapper


def _check(env) -> None:
    wrapped = DingEnvWrapper(env)
    cfg = EasyDict(dict(collector_env_num=4, evaluator_env_num=2, is_train=True))
    collector_cfg = wrapped.create_collector_env_cfg(cfg)
    evaluator_cfg = wrapped.create_evaluator_env_cfg(cfg)
    obs = wrapped.reset()
    action = wrapped.random_action()
    assert isinstance(collector_cfg, list) and len(collector_cfg) == 4
    assert isinstance(evaluator_cfg, list) and len(evaluator_cfg) == 2
    print(type(obs).__name__, getattr(obs, 'shape', None))
    print(type(action).__name__, getattr(action, 'shape', None))
    print(wrapped.observation_space, wrapped.action_space)


def main() -> None:
    _check(gym.make('CartPole-v0'))
    _check(gymnasium.make('CartPole-v0'))
    print('env wrapper smoke ok')


if __name__ == '__main__':
    main()
