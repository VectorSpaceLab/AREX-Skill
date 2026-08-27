#!/usr/bin/env python3
"""Run a tiny Chainer training loop on synthetic data.

The default path is CPU-only and deterministic enough for smoke testing.
Use `--device` if you want to try a GPU path in an environment where CuPy is
available.
"""

from __future__ import annotations

import argparse
import tempfile

import numpy as np

import chainer
import chainer.functions as F
import chainer.links as L
from chainer import datasets
from chainer import iterators
from chainer import optimizers
from chainer import training
from chainer.training import extensions


class TinyMLP(chainer.Chain):
    def __init__(self) -> None:
        super().__init__()
        with self.init_scope():
            self.l1 = L.Linear(4, 3)
            self.l2 = L.Linear(3, 2)

    def __call__(self, x):
        return self.l2(F.relu(self.l1(x)))


def build_dataset() -> datasets.TupleDataset:
    x = np.array(
        [[0, 1, 2, 3], [3, 2, 1, 0], [1, 1, 1, 1], [2, 2, 2, 2]],
        dtype=np.float32,
    )
    y = np.array([0, 1, 0, 1], dtype=np.int32)
    return datasets.TupleDataset(x, y)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", type=int, default=-1,
                        help="GPU device id, or -1 for CPU")
    parser.add_argument("--iterations", type=int, default=2,
                        help="Number of iterations to run")
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Mini-batch size for the synthetic dataset")
    args = parser.parse_args()

    if args.device >= 0 and not chainer.backends.cuda.available:
        raise SystemExit("CUDA is not available in this environment")

    model = L.Classifier(TinyMLP())
    if args.device >= 0:
        model.to_gpu(args.device)

    train = build_dataset()
    train_iter = iterators.SerialIterator(
        train, batch_size=args.batch_size, repeat=False, shuffle=False)
    optimizer = optimizers.SGD(lr=0.1)
    optimizer.setup(model)
    updater = training.StandardUpdater(train_iter, optimizer, device=args.device)
    out_dir = tempfile.mkdtemp(prefix="chainer-training-smoke-")
    trainer = training.Trainer(updater, (args.iterations, "iteration"), out=out_dir)
    trainer.extend(extensions.LogReport(trigger=(1, "iteration")))
    trainer.extend(extensions.PrintReport([
        "iteration", "main/loss", "main/accuracy"
    ]))
    trainer.run()

    print(f"iterations={updater.iteration}")
    print(f"output_dir={out_dir}")
    print(f"loss={trainer.observation.get('main/loss')}")
    print(f"accuracy={trainer.observation.get('main/accuracy')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
