#!/usr/bin/env python
"""Compile/build-only smoke helper for keras-rl continuous-action agents.

The helper builds small synthetic Pendulum-like DDPG and NAF models against an
installed keras-rl package. It does not create Gym environments, train agents,
render, download assets, save weights, or require MuJoCo.
"""
from __future__ import print_function

import argparse
import os
import sys

import numpy as np


class SmokeFailure(RuntimeError):
    """Expected diagnostic failure from the smoke helper."""


def parse_shape(text):
    try:
        dims = tuple(int(part.strip()) for part in text.split(',') if part.strip())
    except ValueError:
        raise argparse.ArgumentTypeError('shape must be comma-separated positive integers, e.g. 3 or 4,84,84')
    if not dims or any(dim <= 0 for dim in dims):
        raise argparse.ArgumentTypeError('shape must contain at least one positive dimension')
    return dims


def configure_backend(choice):
    if choice != 'auto':
        os.environ['KERAS_BACKEND'] = choice


def load_apis():
    try:
        import keras.backend as K
        from keras.models import Sequential, Model
        from keras.layers import Dense, Activation, Flatten, Input, Concatenate
        from keras.optimizers import Adam
        from rl.agents import DDPGAgent, NAFAgent
        from rl.memory import SequentialMemory
        from rl.random import OrnsteinUhlenbeckProcess, GaussianWhiteNoiseProcess
    except ImportError as exc:
        raise SmokeFailure(
            'ImportError while loading keras-rl/Keras dependencies: {0}\n'
            'Install keras-rl with a standalone Keras 2.x-compatible backend before running this smoke.'.format(exc)
        )

    return {
        'K': K,
        'Sequential': Sequential,
        'Model': Model,
        'Dense': Dense,
        'Activation': Activation,
        'Flatten': Flatten,
        'Input': Input,
        'Concatenate': Concatenate,
        'Adam': Adam,
        'DDPGAgent': DDPGAgent,
        'NAFAgent': NAFAgent,
        'SequentialMemory': SequentialMemory,
        'OrnsteinUhlenbeckProcess': OrnsteinUhlenbeckProcess,
        'GaussianWhiteNoiseProcess': GaussianWhiteNoiseProcess,
    }


def adam(api, lr, clipnorm=1.0):
    try:
        return api['Adam'](lr=lr, clipnorm=clipnorm)
    except TypeError:
        return api['Adam'](learning_rate=lr, clipnorm=clipnorm)


def dense_relu(api, x, units):
    x = api['Dense'](units)(x)
    return api['Activation']('relu')(x)


def make_actor(api, observation_shape, nb_actions, window_length):
    actor = api['Sequential']()
    actor.add(api['Flatten'](input_shape=(window_length,) + observation_shape))
    actor.add(api['Dense'](16))
    actor.add(api['Activation']('relu'))
    actor.add(api['Dense'](16))
    actor.add(api['Activation']('relu'))
    actor.add(api['Dense'](nb_actions))
    actor.add(api['Activation']('linear'))
    return actor


def make_ddpg_critic(api, observation_shape, nb_actions, window_length):
    action_input = api['Input'](shape=(nb_actions,), name='critic_action_input')
    observation_input = api['Input'](shape=(window_length,) + observation_shape, name='critic_observation_input')
    flat_observation = api['Flatten']()(observation_input)
    x = api['Concatenate']()([action_input, flat_observation])
    x = dense_relu(api, x, 32)
    x = dense_relu(api, x, 32)
    x = api['Dense'](1)(x)
    x = api['Activation']('linear')(x)
    critic = api['Model'](inputs=[action_input, observation_input], outputs=x)
    return critic, action_input


def make_naf_models(api, observation_shape, nb_actions, window_length, covariance_mode):
    V_model = api['Sequential']()
    V_model.add(api['Flatten'](input_shape=(window_length,) + observation_shape))
    V_model.add(api['Dense'](16))
    V_model.add(api['Activation']('relu'))
    V_model.add(api['Dense'](16))
    V_model.add(api['Activation']('relu'))
    V_model.add(api['Dense'](1))
    V_model.add(api['Activation']('linear'))

    mu_model = api['Sequential']()
    mu_model.add(api['Flatten'](input_shape=(window_length,) + observation_shape))
    mu_model.add(api['Dense'](16))
    mu_model.add(api['Activation']('relu'))
    mu_model.add(api['Dense'](16))
    mu_model.add(api['Activation']('relu'))
    mu_model.add(api['Dense'](nb_actions))
    mu_model.add(api['Activation']('linear'))

    if covariance_mode == 'full':
        l_units = (nb_actions * nb_actions + nb_actions) // 2
    elif covariance_mode == 'diag':
        l_units = nb_actions
    else:
        raise SmokeFailure("covariance_mode must be 'full' or 'diag', got {0!r}".format(covariance_mode))

    action_input = api['Input'](shape=(nb_actions,), name='naf_action_input')
    observation_input = api['Input'](shape=(window_length,) + observation_shape, name='naf_observation_input')
    flat_observation = api['Flatten']()(observation_input)
    x = api['Concatenate']()([action_input, flat_observation])
    x = dense_relu(api, x, 32)
    x = dense_relu(api, x, 32)
    x = api['Dense'](l_units)(x)
    x = api['Activation']('linear')(x)
    L_model = api['Model'](inputs=[action_input, observation_input], outputs=x)
    return V_model, mu_model, L_model


def make_random_process(api, kind, nb_actions, noise_size):
    if kind == 'none':
        return None
    size = nb_actions if noise_size is None else noise_size
    if kind == 'ou':
        return api['OrnsteinUhlenbeckProcess'](theta=.15, mu=0., sigma=.3, size=size)
    if kind == 'gaussian':
        return api['GaussianWhiteNoiseProcess'](mu=0., sigma=.3, size=size)
    raise SmokeFailure('unknown random process: {0}'.format(kind))


def validate_random_process(process, nb_actions):
    if process is None:
        return
    sample = np.asarray(process.sample())
    expected = (nb_actions,)
    if sample.shape != expected:
        raise SmokeFailure(
            'Random process size mismatch: sample shape {0}, expected {1}. '
            'Set size=nb_actions for continuous agents.'.format(sample.shape, expected)
        )
    if hasattr(process, 'reset_states'):
        process.reset_states()


def ddpg_optimizers(api, count):
    if count == 1:
        return adam(api, 1e-3)
    if count < 0:
        raise SmokeFailure('--ddpg-optimizer-list-size must be non-negative')
    return [adam(api, 1e-4), adam(api, 1e-3)] if count == 2 else [adam(api, 1e-3) for _ in range(count)]


def run_ddpg(api, args):
    actor = make_actor(api, args.observation_shape, args.nb_actions, args.window_length)
    critic, action_input = make_ddpg_critic(api, args.observation_shape, args.nb_actions, args.window_length)
    passed_action_input = action_input
    if args.break_critic_wiring:
        passed_action_input = api['Input'](shape=(args.nb_actions,), name='wrong_action_input')

    memory = api['SequentialMemory'](limit=args.memory_limit, window_length=args.window_length)
    random_process = make_random_process(api, args.random_process, args.nb_actions, args.noise_size)
    validate_random_process(random_process, args.nb_actions)

    try:
        agent = api['DDPGAgent'](
            nb_actions=args.nb_actions,
            actor=actor,
            critic=critic,
            critic_action_input=passed_action_input,
            memory=memory,
            nb_steps_warmup_critic=10,
            nb_steps_warmup_actor=10,
            random_process=random_process,
            gamma=.99,
            target_model_update=1e-3,
        )
    except ValueError as exc:
        raise SmokeFailure(
            'DDPG critic input wiring failure: {0}\n'
            'Pass the exact action Input object contained in critic.inputs as critic_action_input.'.format(exc)
        )
    except TypeError as exc:
        if 'len' in str(exc) and 'symbolic' in str(exc).lower():
            raise SmokeFailure(
                'DDPG model validation hit a symbolic tensor length incompatibility: {0}\n'
                'This is usually a legacy Keras/backend compatibility issue. Try a legacy-compatible backend.'.format(exc)
            )
        raise

    try:
        agent.compile(ddpg_optimizers(api, args.ddpg_optimizer_list_size), metrics=['mae'])
    except ValueError as exc:
        raise SmokeFailure(
            'DDPG optimizer-list failure: {0}\n'
            'Use one optimizer or exactly two optimizers: [actor_optimizer, critic_optimizer].'.format(exc)
        )
    return 'DDPG compile OK'


def run_naf(api, args):
    V_model, mu_model, L_model = make_naf_models(
        api, args.observation_shape, args.nb_actions, args.window_length, args.covariance_mode
    )
    memory = api['SequentialMemory'](limit=args.memory_limit, window_length=args.window_length)
    random_process = make_random_process(api, args.random_process, args.nb_actions, args.noise_size)
    validate_random_process(random_process, args.nb_actions)

    try:
        agent = api['NAFAgent'](
            nb_actions=args.nb_actions,
            V_model=V_model,
            L_model=L_model,
            mu_model=mu_model,
            memory=memory,
            nb_steps_warmup=10,
            random_process=random_process,
            covariance_mode=args.covariance_mode,
            gamma=.99,
            target_model_update=1e-3,
        )
        agent.compile(adam(api, 1e-3), metrics=['mae'])
    except RuntimeError as exc:
        raise SmokeFailure(
            'NAF model/covariance wiring failure: {0}\n'
            'Check V_model=(None,1), mu_model=(None,nb_actions), and L_model units for covariance_mode.'.format(exc)
        )
    except TypeError as exc:
        if 'len' in str(exc) and 'symbolic' in str(exc).lower():
            raise SmokeFailure(
                'NAF compile hit a symbolic tensor/backend incompatibility: {0}\n'
                'Try a legacy-compatible Keras backend.'.format(exc)
            )
        raise
    return 'NAF compile OK ({0} covariance)'.format(args.covariance_mode)


def build_parser():
    parser = argparse.ArgumentParser(
        description='Build/compile synthetic keras-rl DDPG and NAF continuous-action agents.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            'Examples:\n'
            '  python build_continuous_agents_smoke.py --agent all --backend theano\n'
            '  python build_continuous_agents_smoke.py --agent naf --covariance-mode diag\n'
            '  python build_continuous_agents_smoke.py --agent ddpg --noise-size 2 --nb-actions 1\n'
            '  python build_continuous_agents_smoke.py --agent ddpg --ddpg-optimizer-list-size 3'
        ),
    )
    parser.add_argument('--agent', choices=['ddpg', 'naf', 'all'], default='all', help='agent family to compile')
    parser.add_argument('--backend', choices=['auto', 'theano', 'tensorflow'], default='auto', help='set KERAS_BACKEND before importing Keras')
    parser.add_argument('--observation-shape', type=parse_shape, default=(3,), help='comma-separated observation shape, default: 3')
    parser.add_argument('--nb-actions', type=int, default=1, help='number of continuous action dimensions')
    parser.add_argument('--window-length', type=int, default=1, help='SequentialMemory/model window length')
    parser.add_argument('--memory-limit', type=int, default=1000, help='SequentialMemory limit')
    parser.add_argument('--random-process', choices=['ou', 'gaussian', 'none'], default='ou', help='action-noise process to construct')
    parser.add_argument('--noise-size', type=int, default=None, help='override random_process size; default is nb_actions')
    parser.add_argument('--covariance-mode', choices=['full', 'diag'], default='full', help='NAF covariance mode')
    parser.add_argument('--ddpg-optimizer-list-size', type=int, default=2, help='number of optimizers to pass to DDPG when using a list; 1 passes a single optimizer')
    parser.add_argument('--break-critic-wiring', action='store_true', help='intentionally pass the wrong critic_action_input to demonstrate diagnostics')
    return parser


def validate_args(args):
    if args.nb_actions <= 0:
        raise SmokeFailure('--nb-actions must be positive')
    if args.window_length <= 0:
        raise SmokeFailure('--window-length must be positive')
    if args.memory_limit <= args.window_length + 2:
        raise SmokeFailure('--memory-limit must exceed window_length + 2')


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(args)
    configure_backend(args.backend)
    api = load_apis()
    backend_name = api['K'].backend()

    results = []
    if args.agent in ('ddpg', 'all'):
        results.append(run_ddpg(api, args))
    if args.agent in ('naf', 'all'):
        results.append(run_naf(api, args))

    print('Backend: {0}'.format(backend_name))
    print('Observation shape: {0}; nb_actions: {1}; window_length: {2}'.format(
        args.observation_shape, args.nb_actions, args.window_length
    ))
    for result in results:
        print(result)
    print('No Gym environment, training loop, rendering, MuJoCo dependency, download, or weight file was used.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except SmokeFailure as exc:
        print('continuous-agent smoke failed:', file=sys.stderr)
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print('continuous-agent smoke failed with an unexpected exception:', file=sys.stderr)
        print('{0}: {1}'.format(exc.__class__.__name__, exc), file=sys.stderr)
        if 'len' in str(exc) and 'symbolic' in str(exc).lower():
            print('Hint: this often indicates a legacy Keras/backend symbolic tensor compatibility issue.', file=sys.stderr)
        sys.exit(3)
