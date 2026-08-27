#!/usr/bin/env python3
"""
Tiny Tensorforce action-masking smoke test.

Purpose:
  Validate that an installed Tensorforce package respects the singleton integer
  action-mask convention: state key "action_mask" masks action options for the
  default singleton action name "action".

Example:
  python scripts/action_masking_smoke.py --trials 20

The script is self-contained and does not read the original Tensorforce checkout.
"""

import argparse
import os
import sys
from typing import Sequence

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np


def _import_agent():
    try:
        from tensorforce import Agent
    except Exception as exc:  # pragma: no cover - diagnostic user interface
        print(
            "Failed to import Tensorforce Agent. Use a Tensorforce 0.6.x-compatible "
            "Python/TensorFlow/Gym/NumPy environment before debugging masks.\n"
            f"Import error: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return None
    return Agent


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate Tensorforce singleton integer action masking."
    )
    parser.add_argument(
        "--trials", type=int, default=20,
        help="Number of independent masked act() calls to run (default: 20).",
    )
    parser.add_argument(
        "--seed", type=int, default=13,
        help="Random seed passed to Tensorforce config and NumPy (default: 13).",
    )
    parser.add_argument(
        "--invalid-index", type=int, default=1, choices=(0, 1, 2),
        help="Action index to mask out for the 3-option smoke action (default: 1).",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Print every sampled action instead of only the summary.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] = tuple()) -> int:
    args = parse_args(argv)
    if args.trials <= 0:
        print("--trials must be positive", file=sys.stderr)
        return 2

    Agent = _import_agent()
    if Agent is None:
        return 2

    np.random.seed(args.seed)
    mask = np.ones(shape=(3,), dtype=bool)
    mask[args.invalid_index] = False

    agent = None
    try:
        agent = Agent.create(
            agent="random",
            states=dict(type="float", shape=(2,), min_value=0.0, max_value=1.0),
            actions=dict(type="int", shape=(), num_values=3),
            config=dict(device="CPU", seed=args.seed, tf_log_level=40),
        )

        seen = []
        for trial in range(args.trials):
            state_value = np.asarray([trial / float(args.trials), 1.0], dtype=np.float32)
            states = dict(state=state_value, action_mask=mask)
            action = int(agent.act(states=states, independent=True))
            seen.append(action)
            if args.verbose:
                print(f"trial={trial} action={action} mask={mask.tolist()}")
            if action == args.invalid_index:
                print(
                    "FAILED: Tensorforce returned masked action "
                    f"{action} with mask {mask.tolist()}",
                    file=sys.stderr,
                )
                return 1

        print(
            "PASSED action masking smoke: "
            f"trials={args.trials} invalid_index={args.invalid_index} "
            f"seen={sorted(set(seen))} mask={mask.tolist()}"
        )
        return 0

    finally:
        if agent is not None:
            agent.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
