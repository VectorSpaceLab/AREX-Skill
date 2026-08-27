#!/usr/bin/env python3
"""Run a safe CPU/NumPy Foolbox smoke test.

The check needs the public package plus Pillow and Matplotlib. It does not
load an external model, clone a repository, or download data.
"""
from __future__ import annotations

import argparse
import os

import numpy as np


def toy_model(inputs: np.ndarray) -> np.ndarray:
    x = np.asarray(inputs)
    mean = x.reshape((x.shape[0], -1)).mean(axis=1)
    return np.stack([1.0 - mean, mean], axis=-1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default="mnist", help="bundled sample dataset")
    parser.add_argument("--batch-size", type=int, default=2)
    args = parser.parse_args()

    os.environ.setdefault("MPLBACKEND", "Agg")
    import eagerpy as ep
    import foolbox as fb

    fmodel = fb.NumPyModel(toy_model, bounds=(0, 1), data_format="channels_first")
    x = np.array(
        [[[[0.0, 0.0], [0.0, 0.0]]], [[[1.0, 1.0], [1.0, 1.0]]]],
        dtype=np.float32,
    )
    y = np.array([0, 1], dtype=np.int64)
    accuracy = fb.accuracy(fmodel, x, y)
    images, labels = fb.samples(
        fmodel,
        dataset=args.dataset,
        batchsize=args.batch_size,
        data_format="channels_first",
    )
    fb.plot.images(ep.astensor(images), n=min(2, len(images)), data_format="channels_first")
    _, clipped, success = fb.attacks.LinfAdditiveUniformNoiseAttack()(
        fmodel, ep.astensor(x), ep.astensor(y), epsilons=0.1
    )
    print(f"foolbox={fb.__version__}")
    print(f"accuracy={accuracy:.3f}")
    print(f"samples={images.shape}, labels={labels.shape}")
    print(f"clipped={clipped.shape}, success={success.shape}")
    assert clipped.shape == x.shape
    assert success.shape == (len(x),)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
