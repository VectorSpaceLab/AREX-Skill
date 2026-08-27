#!/usr/bin/env python3
"""Quick DI-engine install smoke.

This helper checks that the installed package can be imported, reports the main
runtime versions, and compiles one representative config without starting a
training loop.
"""

from __future__ import annotations

from importlib.metadata import version

import gym
import gymnasium
import torch

from ding.config import compile_config
from dizoo.classic_control.cartpole.config.cartpole_dqn_config import (
    cartpole_dqn_config,
    cartpole_dqn_create_config,
)


def main() -> None:
    print(f"DI-engine: {version('DI-engine')}")
    print(f"torch: {torch.__version__}")
    print(f"torch.cuda: {torch.version.cuda}")
    print(f"torch.cuda.is_available: {torch.cuda.is_available()}")
    print(f"gym: {version('gym')}")
    print(f"gymnasium: {version('gymnasium')}")
    print(f"cartpole envs: {gym.__name__}, {gymnasium.__name__}")

    cfg = compile_config(
        cartpole_dqn_config,
        create_cfg=cartpole_dqn_create_config,
        auto=True,
        save_cfg=False,
    )
    print(f"compiled config: exp_name={cfg.exp_name}, stop_value={cfg.env.stop_value}, cuda={cfg.policy.cuda}")


if __name__ == '__main__':
    main()
