#!/usr/bin/env python3
"""Run safe NumPy noise and DatasetAttack checks without external models."""
from __future__ import annotations

import argparse
import numpy as np
import eagerpy as ep
import foolbox as fb


def model(inputs: np.ndarray) -> np.ndarray:
    x = np.asarray(inputs)
    mean = x.reshape((len(x), -1)).mean(axis=1)
    return np.stack([1 - mean, mean], axis=-1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epsilon", type=float, default=0.1)
    args = parser.parse_args()
    fmodel = fb.NumPyModel(model, bounds=(0, 1), data_format="channels_first")
    x = ep.astensor(
        np.array(
            [
                [[[0.0, 0.0], [0.0, 0.0]]],
                [[[1.0, 1.0], [1.0, 1.0]]],
            ],
            dtype=np.float32,
        )
    )
    labels = ep.astensor(np.array([0, 1], dtype=np.int64))
    attack = fb.attacks.LinfAdditiveUniformNoiseAttack()
    _, clipped, success = attack(fmodel, x, labels, epsilons=args.epsilon)
    dataset = fb.attacks.DatasetAttack(distance=fb.distances.l2)
    dataset.feed(fmodel, x)
    _, _, dataset_success = dataset(fmodel, x, labels, epsilons=None)
    print(f"noise_clipped={clipped.shape} noise_success={success.shape}")
    print(f"dataset_success={dataset_success.shape}")
    assert clipped.shape == x.shape
    assert success.shape == (len(x),)
    assert dataset_success.shape == (len(x),)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
