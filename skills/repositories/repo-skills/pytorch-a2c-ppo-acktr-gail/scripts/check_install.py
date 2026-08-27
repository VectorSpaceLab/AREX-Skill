#!/usr/bin/env python3
"""Safe installation/API smoke check for pytorch-a2c-ppo-acktr-gail.

The script imports selected package modules, reports key dependency versions,
and runs a tiny CPU Policy/RolloutStorage check. It does not create Gym
environments, download data, render, or train.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from importlib.metadata import PackageNotFoundError, version


def dist_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "not-installed"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run safe import and tiny API checks.")
    parser.add_argument("--check-cuda", action="store_true", help="Report torch CUDA availability; does not require CUDA to pass")
    parser.add_argument("--skip-model-smoke", action="store_true", help="Only import modules and print versions")
    args = parser.parse_args(argv)

    print("versions:")
    for dist in ["a2c-ppo-acktr", "torch", "gym", "stable-baselines3", "pybullet", "h5py"]:
        print(f"  {dist}: {dist_version(dist)}")

    modules = [
        "a2c_ppo_acktr",
        "a2c_ppo_acktr.arguments",
        "a2c_ppo_acktr.model",
        "a2c_ppo_acktr.storage",
        "a2c_ppo_acktr.distributions",
        "a2c_ppo_acktr.utils",
        "a2c_ppo_acktr.envs",
        "a2c_ppo_acktr.algo.a2c_acktr",
        "a2c_ppo_acktr.algo.ppo",
        "a2c_ppo_acktr.algo.gail",
    ]
    for name in modules:
        try:
            importlib.import_module(name)
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            print(f"FAIL import {name}: {type(exc).__name__}: {exc}", file=sys.stderr)
            print("Hint: check Gym/PyBullet compatibility, h5py for GAIL, and installed package versions.", file=sys.stderr)
            return 1
    print("imports: ok")

    import torch

    if args.check_cuda:
        print(f"torch_cuda_available: {torch.cuda.is_available()} device_count={torch.cuda.device_count()}")

    if not args.skip_model_smoke:
        from gym.spaces import Discrete
        from a2c_ppo_acktr.model import Policy
        from a2c_ppo_acktr.storage import RolloutStorage

        policy = Policy((4,), Discrete(2))
        obs = torch.zeros(2, 4)
        rnn = torch.zeros(2, policy.recurrent_hidden_state_size)
        masks = torch.ones(2, 1)
        value, action, logp, rnn2 = policy.act(obs, rnn, masks)
        rollout = RolloutStorage(2, 2, (4,), Discrete(2), policy.recurrent_hidden_state_size)
        rollout.rewards.fill_(1.0)
        rollout.compute_returns(torch.zeros(2, 1), use_gae=False, gamma=0.99, gae_lambda=0.95)
        print("model_smoke:", tuple(value.shape), tuple(action.shape), tuple(logp.shape), tuple(rnn2.shape), tuple(rollout.returns.shape))

    print("PASS check_install")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
