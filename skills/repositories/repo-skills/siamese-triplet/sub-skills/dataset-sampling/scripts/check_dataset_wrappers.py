#!/usr/bin/env python3
"""Smoke the pair/triplet dataset wrappers and balanced batch sampler.

This script uses tiny in-memory MNIST-like fixtures so it does not download
MNIST/FashionMNIST. It validates the legacy torchvision-style attributes that
this repository expects.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch


def add_module_dir(module_dir: str) -> None:
    path = str(Path(module_dir).resolve())
    if path not in sys.path:
        sys.path.insert(0, path)


class FakeVisionDataset:
    def __init__(self, train: bool = True):
        self.train = train
        self.transform = None
        self.train_data = torch.arange(6 * 28 * 28, dtype=torch.uint8).reshape(6, 28, 28)
        self.train_labels = torch.tensor([0, 0, 1, 1, 2, 2], dtype=torch.long)
        self.test_data = torch.arange(6 * 28 * 28, dtype=torch.uint8).reshape(6, 28, 28)
        self.test_labels = torch.tensor([0, 1, 0, 2, 1, 2], dtype=torch.long)

    def __len__(self) -> int:
        return len(self.train_data if self.train else self.test_data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module-dir",
        default=str(Path.cwd()),
        help="Directory containing the repo's top-level modules; defaults to the current working directory.",
    )
    args = parser.parse_args()

    add_module_dir(args.module_dir)

    from datasets import BalancedBatchSampler, SiameseMNIST, TripletMNIST

    train = FakeVisionDataset(train=True)
    test = FakeVisionDataset(train=False)

    siamese = SiameseMNIST(train)
    (img1, img2), target = siamese[0]
    assert img1.size == (28, 28)
    assert img2.size == (28, 28)
    assert target in (0, 1)

    triplet = TripletMNIST(test)
    (anchor, positive, negative), triplet_target = triplet[0]
    assert anchor.size == positive.size == negative.size == (28, 28)
    assert triplet_target == []

    sampler = BalancedBatchSampler(train.train_labels, n_classes=2, n_samples=2)
    batch = next(iter(sampler))
    assert len(batch) == 4

    print("dataset smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
