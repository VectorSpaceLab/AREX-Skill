#!/usr/bin/env python3
"""Tiny CUDA smoke test for the shared LibMTL API."""

from __future__ import annotations

import argparse

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

from LibMTL import Trainer
from LibMTL.loss import CELoss
from LibMTL.metrics import AccMetric


class TinyDataset(Dataset):
    def __len__(self) -> int:
        return 2

    def __getitem__(self, idx: int):
        x = torch.randn(3, 4, 4)
        y = torch.tensor(idx % 2, dtype=torch.long)
        return x, {"task": y}


class Encoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Flatten(), nn.Linear(3 * 4 * 4, 8), nn.ReLU())

    def forward(self, inputs):
        return self.net(inputs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a tiny LibMTL Trainer smoke test")
    parser.add_argument("--epochs", type=int, default=1)
    args = parser.parse_args()

    if not torch.cuda.is_available():
        raise SystemExit("CUDA is required for this smoke test")

    task_dict = {
        "task": {
            "metrics": ["Acc"],
            "metrics_fn": AccMetric(),
            "loss_fn": CELoss(),
            "weight": [1],
        }
    }
    decoders = nn.ModuleDict({"task": nn.Linear(8, 2)})
    loader = DataLoader(TinyDataset(), batch_size=2, shuffle=False)

    trainer = Trainer(
        task_dict=task_dict,
        weighting="EW",
        architecture="HPS",
        encoder_class=Encoder,
        decoders=decoders,
        rep_grad=False,
        multi_input=False,
        optim_param={"optim": "adam", "lr": 1e-3, "weight_decay": 0.0},
        scheduler_param=None,
        weight_args={},
        arch_args={},
    )
    trainer.train(loader, loader, epochs=args.epochs)
    print("core-api smoke: ok")


if __name__ == "__main__":
    main()
