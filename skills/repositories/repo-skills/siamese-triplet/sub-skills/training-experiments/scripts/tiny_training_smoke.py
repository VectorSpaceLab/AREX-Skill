#!/usr/bin/env python3
"""Smoke the shared trainer and metric helpers with tiny synthetic fixtures."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset


def add_module_dir(module_dir: str) -> None:
    path = str(Path(module_dir).resolve())
    if path not in sys.path:
        sys.path.insert(0, path)


class FakeClassificationDataset(Dataset):
    def __init__(self):
        self.images = torch.arange(4 * 28 * 28, dtype=torch.float32).reshape(4, 1, 28, 28) / 255.0
        self.labels = torch.tensor([0, 1, 0, 1], dtype=torch.long)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx):
        return self.images[idx], self.labels[idx]


class FakeOnlineDataset(Dataset):
    def __init__(self):
        self.images = torch.arange(8 * 28 * 28, dtype=torch.float32).reshape(8, 1, 28, 28) / 255.0
        self.labels = torch.tensor([0, 0, 1, 1, 2, 2, 3, 3], dtype=torch.long)

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx):
        return self.images[idx], self.labels[idx]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--module-dir",
        default=str(Path.cwd()),
        help="Directory containing the repo's top-level modules; defaults to the current working directory.",
    )
    args = parser.parse_args()

    add_module_dir(args.module_dir)

    from datasets import BalancedBatchSampler
    from losses import OnlineTripletLoss
    from metrics import AccumulatedAccuracyMetric, AverageNonzeroTripletsMetric
    from networks import ClassificationNet, EmbeddingNet
    from trainer import fit
    from utils import RandomNegativeTripletSelector

    # Baseline classification smoke.
    train_loader = DataLoader(FakeClassificationDataset(), batch_size=2, shuffle=False)
    val_loader = DataLoader(FakeClassificationDataset(), batch_size=2, shuffle=False)
    model = ClassificationNet(EmbeddingNet(), n_classes=2)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, 1, gamma=0.1)
    fit(
        train_loader,
        val_loader,
        model,
        torch.nn.NLLLoss(),
        optimizer,
        scheduler,
        n_epochs=1,
        cuda=False,
        log_interval=1,
        metrics=[AccumulatedAccuracyMetric()],
    )

    # Online triplet smoke.
    online_ds = FakeOnlineDataset()
    sampler = BalancedBatchSampler(online_ds.labels, n_classes=2, n_samples=2)
    online_loader = DataLoader(online_ds, batch_sampler=sampler)
    online_model = EmbeddingNet()
    online_optimizer = torch.optim.Adam(online_model.parameters(), lr=1e-3)
    online_scheduler = torch.optim.lr_scheduler.StepLR(online_optimizer, 1, gamma=0.1)
    online_loss = OnlineTripletLoss(1.0, RandomNegativeTripletSelector(1.0))
    fit(
        online_loader,
        online_loader,
        online_model,
        online_loss,
        online_optimizer,
        online_scheduler,
        n_epochs=1,
        cuda=False,
        log_interval=1,
        metrics=[AverageNonzeroTripletsMetric()],
    )

    print("training smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
