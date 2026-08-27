#!/usr/bin/env python3
"""Check a Python environment for minimalRL-style examples.

This script verifies the shared dependencies used by the bundled minimalRL skill
references. It is safe by default and does not run training.
"""

from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify minimalRL dependencies and optional Gym environments.")
    parser.add_argument("--make-envs", action="store_true", help="Also create/reset CartPole-v1 and Pendulum-v1.")
    args = parser.parse_args()

    try:
        import numpy as np
        import torch
        import gym
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"dependency import failed: {exc}", file=sys.stderr)
        print('Install with: python -m pip install "torch" "gym==0.26.2" "numpy<2"', file=sys.stderr)
        return 1

    print(f"python={sys.version.split()[0]}")
    print(f"torch={torch.__version__} cuda_available={torch.cuda.is_available()}")
    print(f"gym={getattr(gym, '__version__', 'unknown')}")
    print(f"numpy={np.__version__}")
    print(f"torch_cpu_tensor_sum={torch.tensor([1.0, 2.0]).sum().item()}")

    if int(np.__version__.split('.')[0]) >= 2:
        print("warning: Gym 0.26 is known to be fragile with NumPy 2.x; prefer numpy<2", file=sys.stderr)

    if args.make_envs:
        for env_id in ["CartPole-v1", "Pendulum-v1"]:
            try:
                env = gym.make(env_id)
                reset = env.reset()
                obs = reset[0] if isinstance(reset, tuple) else reset
                print(f"{env_id}: observation_shape={getattr(env.observation_space, 'shape', None)} action_shape={getattr(env.action_space, 'shape', None)} reset_type={type(obs).__name__}")
                env.close()
            except Exception as exc:  # pragma: no cover - diagnostic path
                print(f"{env_id} check failed: {exc}", file=sys.stderr)
                return 2

    print("minimal-rl-env: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
