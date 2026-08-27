#!/usr/bin/env python3
"""Tiny TensorLayer reinforcement-learning smoke test.

Checks the reward-discount helper and a deterministic action-selection path on
synthetic inputs.
"""

from __future__ import annotations

import argparse

import numpy as np
import tensorlayer as tl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    rewards = np.asarray([0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], dtype=np.float32)
    expected = np.asarray([0.729, 0.81, 0.9, 1.0, 0.729, 0.81, 0.9, 1.0, 0.729, 0.81, 0.9, 1.0], dtype=np.float32)
    discounted = np.asarray(tl.rein.discount_episode_rewards(rewards, gamma=0.9), dtype=np.float32)
    if not np.allclose(discounted, expected, atol=1e-4):
        raise AssertionError(f'discounted rewards mismatch: {discounted} != {expected}')

    action = tl.rein.choice_action_by_probs((0.0, 1.0), action_list=['left', 'right'])
    if action != 'right':
        raise AssertionError(f'unexpected deterministic action: {action}')

    print('rl-ok', discounted.tolist(), action)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
