#!/usr/bin/env python
"""CPU-safe LightningCLI smoke script with synthetic data and no downloads.

Examples:
    python lightning_cli_smoke.py --help
    python lightning_cli_smoke.py fit --print_config
    PL_FIT__TRAINER__MAX_EPOCHS=1 python lightning_cli_smoke.py fit --trainer.fast_dev_run=1
"""

from __future__ import annotations

import sys

if any(arg in {"-h", "--help"} for arg in sys.argv[1:]):
    print(
        """usage: lightning_cli_smoke.py [-h] {fit,validate,test,predict} ...\n\n"
        "Synthetic LightningCLI smoke script. Install `jsonargparse[jsonnet,signatures]>=4.39`, "
        "Lightning, and Torch before running parse/fit checks.\n\n"
        "examples:\n"
        "  python lightning_cli_smoke.py --help\n"
        "  python lightning_cli_smoke.py fit --print_config\n"
        "  PL_FIT__TRAINER__MAX_EPOCHS=1 python lightning_cli_smoke.py fit --trainer.fast_dev_run=1\n"
        """
    )
    raise SystemExit(0)

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from lightning.pytorch import LightningDataModule, LightningModule
from lightning.pytorch.cli import LightningCLI


class TinyClassifier(LightningModule):
    """Small classifier used only for CLI parsing and fast smoke execution.

    Args:
        input_dim: Number of synthetic input features.
        hidden_dim: Hidden layer width.
        num_classes: Number of target classes.
        learning_rate: Optimizer learning rate.
    """

    def __init__(self, input_dim: int = 4, hidden_dim: int = 8, num_classes: int = 2, learning_rate: float = 0.01):
        super().__init__()
        self.save_hyperparameters()
        self.net = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, num_classes))
        self.loss = nn.CrossEntropyLoss()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def training_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        x, y = batch
        loss = self.loss(self(x), y)
        self.log("train_loss", loss, on_step=True, on_epoch=True)
        return loss

    def validation_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> None:
        x, y = batch
        loss = self.loss(self(x), y)
        self.log("val_loss", loss, on_epoch=True)

    def configure_optimizers(self):
        return torch.optim.SGD(self.parameters(), lr=self.hparams.learning_rate)


class TinyDataModule(LightningDataModule):
    """Synthetic DataModule for CPU-only CLI validation.

    Args:
        batch_size: Batch size for train and validation loaders.
        num_samples: Number of deterministic synthetic examples.
        input_dim: Number of input features; keep aligned with TinyClassifier.input_dim.
        num_classes: Number of classes; keep aligned with TinyClassifier.num_classes.
    """

    def __init__(self, batch_size: int = 4, num_samples: int = 16, input_dim: int = 4, num_classes: int = 2):
        super().__init__()
        self.batch_size = batch_size
        self.num_samples = num_samples
        self.input_dim = input_dim
        self.num_classes = num_classes

    def setup(self, stage: str | None = None) -> None:
        generator = torch.Generator().manual_seed(1234)
        features = torch.randn(self.num_samples, self.input_dim, generator=generator)
        labels = torch.arange(self.num_samples) % self.num_classes
        dataset = TensorDataset(features, labels.long())
        split = max(1, int(0.75 * self.num_samples))
        self.train_dataset = torch.utils.data.Subset(dataset, range(split))
        self.val_dataset = torch.utils.data.Subset(dataset, range(split, self.num_samples))

    def train_dataloader(self) -> DataLoader:
        return DataLoader(self.train_dataset, batch_size=self.batch_size)

    def val_dataloader(self) -> DataLoader:
        return DataLoader(self.val_dataset, batch_size=self.batch_size)


class TinyCLI(LightningCLI):
    def add_arguments_to_parser(self, parser):
        parser.link_arguments("data.input_dim", "model.input_dim", apply_on="instantiate")
        parser.link_arguments("data.num_classes", "model.num_classes", apply_on="instantiate")


def cli_main() -> None:
    TinyCLI(
        TinyClassifier,
        TinyDataModule,
        seed_everything_default=1234,
        save_config_callback=None,
        parser_kwargs={"default_env": True},
        trainer_defaults={
            "accelerator": "cpu",
            "devices": 1,
            "logger": False,
            "enable_checkpointing": False,
            "enable_model_summary": False,
            "max_epochs": 1,
            "limit_train_batches": 1,
            "limit_val_batches": 1,
            "num_sanity_val_steps": 0,
        },
    )


if __name__ == "__main__":
    try:
        cli_main()
    except ModuleNotFoundError as exc:
        if "jsonargparse" in str(exc):
            raise SystemExit(
                "LightningCLI optional requirements are missing. Install "
                "`jsonargparse[jsonnet,signatures]>=4.39` or `lightning[pytorch-extra]`, "
                "then rerun this smoke script."
            ) from exc
        raise
