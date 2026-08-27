#!/usr/bin/env python3
"""Run tiny Stable-Baselines3 custom-env validation examples.

The script is intentionally self-contained: it defines one valid env and one
invalid env, then runs SB3's check_env. Use --mode invalid to confirm failure
handling in automation.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def build_env_classes():
    import gymnasium as gym
    import numpy as np
    from gymnasium import spaces

    class TinyValidEnv(gym.Env):
        """A minimal Gymnasium env compatible with SB3's checker."""

        metadata = {"render_modes": []}

        def __init__(self) -> None:
            super().__init__()
            self.observation_space = spaces.Box(low=-1.0, high=1.0, shape=(3,), dtype=np.float32)
            self.action_space = spaces.Discrete(2)
            self._step_count = 0

        def reset(self, *, seed: int | None = None, options: dict[str, Any] | None = None):
            super().reset(seed=seed)
            self._step_count = 0
            return np.zeros(3, dtype=np.float32), {"options_used": options or {}}

        def step(self, action: int):
            self._step_count += 1
            observation = np.full(3, 0.5 if action else -0.5, dtype=np.float32)
            reward = 1.0 if action else 0.0
            terminated = self._step_count >= 2
            truncated = False
            return observation, reward, terminated, truncated, {}

    class TinyInvalidResetEnv(TinyValidEnv):
        """Invalid because reset does not accept seed/options and returns no info."""

        def reset(self):
            self._step_count = 0
            return np.zeros(3, dtype=np.float32)

    return TinyValidEnv, TinyInvalidResetEnv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run SB3 check_env on tiny built-in custom env examples.",
    )
    parser.add_argument(
        "--mode",
        choices=("valid", "invalid"),
        default="valid",
        help="Choose the built-in environment to validate. 'invalid' exits nonzero by design.",
    )
    parser.add_argument(
        "--render-check",
        action="store_true",
        help="Also run check_env render checks. Disabled by default for safe headless use.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        from stable_baselines3.common.env_checker import check_env
    except ImportError as exc:
        print(f"missing dependency for SB3 env validation: {exc}", file=sys.stderr)
        return 2

    TinyValidEnv, TinyInvalidResetEnv = build_env_classes()
    env = TinyValidEnv() if args.mode == "valid" else TinyInvalidResetEnv()

    try:
        check_env(env, warn=True, skip_render_check=not args.render_check)
    except Exception as exc:
        print(f"check_env failed for {args.mode} env: {exc}", file=sys.stderr)
        return 1

    if args.mode == "invalid":
        print("invalid mode unexpectedly passed check_env", file=sys.stderr)
        return 1

    print("valid env passed check_env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
