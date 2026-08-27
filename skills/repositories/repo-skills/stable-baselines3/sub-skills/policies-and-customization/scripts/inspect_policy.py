#!/usr/bin/env python3
"""Instantiate a tiny Stable-Baselines3 model and print policy details.

This script does not train by default. It is intended for safe policy_kwargs,
Dict-observation, action-noise, and gSDE inspection. ``--help`` works without
importing Stable-Baselines3 so agents can inspect usage before dependencies are
available.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def parse_net_arch(value: str | None):
    if value is None or value == "default":
        return None
    if value == "tiny":
        return [16]
    parsed = json.loads(value)
    if not isinstance(parsed, (list, dict)):
        raise argparse.ArgumentTypeError("--net-arch must decode to a JSON list or object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--algorithm", choices=["PPO", "DQN", "SAC"], default="PPO", help="SB3 algorithm to instantiate")
    parser.add_argument("--policy", default=None, help="Policy alias. Defaults to MultiInputPolicy for --dict-env, otherwise MlpPolicy")
    parser.add_argument("--dict-env", action="store_true", help="Use a tiny Dict observation env with image and vector keys")
    parser.add_argument("--net-arch", default="tiny", help='Use "tiny", "default", or a JSON list/object such as "[32]"')
    parser.add_argument("--activation", choices=["relu", "tanh"], default="relu", help="Activation function for policy_kwargs")
    parser.add_argument("--cnn-output-dim", type=int, default=16, help="CombinedExtractor CNN output dimension for Dict envs")
    parser.add_argument("--action-noise", choices=["none", "normal", "ou"], default="none", help="Continuous off-policy action noise")
    parser.add_argument("--use-sde", action="store_true", help="Enable generalized State-Dependent Exploration when supported")
    parser.add_argument("--train-steps", type=int, default=0, help="Optional training timesteps; default is zero for inspection only")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")
    return parser


def load_dependencies():
    try:
        import gymnasium as gym
        import numpy as np
        import torch as th
        from gymnasium import spaces
        from stable_baselines3 import DQN, PPO, SAC
        from stable_baselines3.common.noise import NormalActionNoise, OrnsteinUhlenbeckActionNoise
    except ImportError as exc:
        raise SystemExit(
            "Missing runtime dependency while instantiating a model. Install/import Stable-Baselines3, "
            "Gymnasium, NumPy, and PyTorch in the current Python environment, or run with --help only.\n"
            f"Original import error: {exc}"
        ) from exc
    return gym, np, th, spaces, DQN, PPO, SAC, NormalActionNoise, OrnsteinUhlenbeckActionNoise


def make_env(algorithm: str, dict_env: bool, deps) -> Any:
    gym, np, _th, spaces, *_ = deps
    continuous = algorithm == "SAC"

    class TinyVectorEnv(gym.Env):
        metadata = {"render_modes": []}

        def __init__(self) -> None:
            self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(4,), dtype=np.float32)
            if continuous:
                self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
            else:
                self.action_space = spaces.Discrete(2)

        def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
            super().reset(seed=seed)
            return np.zeros(self.observation_space.shape, dtype=np.float32), {}

        def step(self, action):
            return np.zeros(self.observation_space.shape, dtype=np.float32), 0.0, False, False, {}

    class TinyDictEnv(gym.Env):
        metadata = {"render_modes": []}

        def __init__(self) -> None:
            self.observation_space = spaces.Dict(
                {
                    "image": spaces.Box(low=0, high=255, shape=(1, 36, 36), dtype=np.uint8),
                    "vector": spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32),
                }
            )
            if continuous:
                self.action_space = spaces.Box(low=-1.0, high=1.0, shape=(2,), dtype=np.float32)
            else:
                self.action_space = spaces.Discrete(2)

        def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
            super().reset(seed=seed)
            return self.observation_space.sample(), {}

        def step(self, action):
            return self.observation_space.sample(), 0.0, False, False, {}

    return TinyDictEnv() if dict_env else TinyVectorEnv()


def make_policy_kwargs(args: argparse.Namespace, deps) -> dict[str, Any]:
    _gym, _np, th, *_ = deps
    policy_kwargs: dict[str, Any] = {}
    net_arch = parse_net_arch(args.net_arch)
    if net_arch is not None:
        policy_kwargs["net_arch"] = net_arch
    policy_kwargs["activation_fn"] = th.nn.ReLU if args.activation == "relu" else th.nn.Tanh
    if args.dict_env:
        policy_kwargs["features_extractor_kwargs"] = {"cnn_output_dim": args.cnn_output_dim}
    return policy_kwargs


def make_action_noise(args: argparse.Namespace, env: Any, deps):
    _gym, np, _th, spaces, _dqn, _ppo, _sac, NormalActionNoise, OrnsteinUhlenbeckActionNoise = deps
    if args.action_noise == "none":
        return None
    if not isinstance(env.action_space, spaces.Box):
        raise ValueError("Action noise requires a continuous Box action space")
    n_actions = env.action_space.shape[-1]
    mean = np.zeros(n_actions, dtype=np.float32)
    sigma = 0.1 * np.ones(n_actions, dtype=np.float32)
    if args.action_noise == "normal":
        return NormalActionNoise(mean=mean, sigma=sigma)
    return OrnsteinUhlenbeckActionNoise(mean=mean, sigma=sigma)


def make_model(args: argparse.Namespace, env: Any, policy: str, policy_kwargs: dict[str, Any], deps):
    _gym, _np, _th, _spaces, DQN, PPO, SAC, *_ = deps
    common_kwargs: dict[str, Any] = {"policy_kwargs": policy_kwargs, "seed": args.seed, "verbose": 0}
    if args.algorithm == "PPO":
        return PPO(policy, env, n_steps=8, batch_size=4, n_epochs=1, use_sde=args.use_sde, **common_kwargs)
    if args.algorithm == "DQN":
        if args.use_sde:
            raise ValueError("DQN does not support gSDE")
        if args.action_noise != "none":
            raise ValueError("DQN uses discrete actions here; action noise is not applicable")
        return DQN(policy, env, buffer_size=32, learning_starts=0, train_freq=1, gradient_steps=1, **common_kwargs)
    action_noise = make_action_noise(args, env, deps)
    return SAC(
        policy,
        env,
        buffer_size=32,
        learning_starts=0,
        train_freq=1,
        gradient_steps=1,
        use_sde=args.use_sde,
        action_noise=action_noise,
        **common_kwargs,
    )


def summarize_model(model, args: argparse.Namespace, policy_kwargs: dict[str, Any]) -> None:
    print(f"algorithm: {args.algorithm}")
    print(f"policy_class: {model.policy.__class__.__module__}.{model.policy.__class__.__name__}")
    print(f"device: {model.policy.device}")
    print(f"observation_space: {model.observation_space}")
    print(f"action_space: {model.action_space}")
    print(f"policy_kwargs_keys: {sorted(policy_kwargs.keys())}")
    if "net_arch" in policy_kwargs:
        print(f"net_arch: {policy_kwargs['net_arch']}")
    if hasattr(model.policy, "features_extractor") and model.policy.features_extractor is not None:
        extractor = model.policy.features_extractor
        print(f"features_extractor: {extractor.__class__.__name__}")
        print(f"features_dim: {getattr(extractor, 'features_dim', 'unknown')}")
        if hasattr(extractor, "extractors"):
            print(f"extractor_keys: {list(extractor.extractors.keys())}")
    if hasattr(model.policy, "mlp_extractor"):
        extractor = model.policy.mlp_extractor
        print(f"latent_dim_pi: {getattr(extractor, 'latent_dim_pi', 'unknown')}")
        print(f"latent_dim_vf: {getattr(extractor, 'latent_dim_vf', 'unknown')}")
    if hasattr(model, "action_noise"):
        print(f"action_noise: {model.action_noise!r}")
    print("policy_summary:")
    print(model.policy)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    deps = load_dependencies()
    env = make_env(args.algorithm, args.dict_env, deps)
    policy = args.policy or ("MultiInputPolicy" if args.dict_env else "MlpPolicy")
    policy_kwargs = make_policy_kwargs(args, deps)
    model = make_model(args, env, policy, policy_kwargs, deps)
    if args.train_steps > 0:
        model.learn(total_timesteps=args.train_steps)
    summarize_model(model, args, policy_kwargs)
    env.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
