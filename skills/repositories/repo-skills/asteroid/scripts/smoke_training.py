#!/usr/bin/env python3
"""Tiny Asteroid training smoke from the generated skill output.

This script exercises the installed runtime package, the `System` Lightning
wrapper, and a PIT loss on a fully synthetic waveform dataset.
"""

from __future__ import annotations

import argparse
import tempfile

import torch
from torch import nn, optim
from torch.utils.data import DataLoader, Dataset
from pytorch_lightning import Trainer
from pytorch_lightning.loggers import CSVLogger

from asteroid.engine.system import System
from asteroid.losses import PITLossWrapper, pairwise_neg_sisdr


class TinyWaveformDataset(Dataset):
    def __init__(self, total: int = 8, n_src: int = 2, length: int = 400):
        self.total = total
        self.n_src = n_src
        self.length = length

    def __len__(self) -> int:
        return self.total

    def __getitem__(self, idx: int):  # noqa: D401 - synthetic sample only
        mix = torch.randn(1, self.length)
        target = torch.randn(self.n_src, self.length)
        return mix, target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Device to run the smoke on.",
    )
    args = parser.parse_args()

    if args.device == "auto":
        accelerator = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        accelerator = args.device

    n_src = 2
    model = nn.Conv1d(1, n_src, kernel_size=1)
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    loss_func = PITLossWrapper(pairwise_neg_sisdr, pit_from="pw_mtx")
    dataset = TinyWaveformDataset(total=8, n_src=n_src, length=400)
    loader = DataLoader(dataset, batch_size=2, num_workers=0)

    system = System(
        model=model,
        optimizer=optimizer,
        loss_func=loss_func,
        train_loader=loader,
        val_loader=loader,
        config={"smoke": True},
    )

    # Asteroid's System logs `hp_metric` at validation epoch end, so use a
    # temporary logger instead of `logger=False`.
    logger = CSVLogger(save_dir=tempfile.mkdtemp(prefix="asteroid-smoke-"), name="lightning")

    trainer = Trainer(
        max_epochs=1,
        fast_dev_run=True,
        accelerator=accelerator,
        devices=1 if accelerator == "cuda" else "auto",
        logger=logger,
        enable_checkpointing=False,
        enable_model_summary=False,
    )
    trainer.fit(system)
    print(f"training-smoke: passed on {accelerator}")


if __name__ == "__main__":
    main()
