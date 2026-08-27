#!/usr/bin/env python
"""Tiny CPU Lightning smoke test with synthetic tensors.

This script is adapted from Lightning's basic autoencoder example patterns, but it
uses generated tensors instead of downloads and avoids dependencies on the source
repository checkout.
"""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a tiny CPU Lightning training smoke test on synthetic tensors.")
    parser.add_argument("--max-steps", type=int, default=2, help="Maximum training steps for the smoke fit.")
    parser.add_argument("--fast-dev-run", action="store_true", help="Use Lightning fast_dev_run for a one-batch wiring check.")
    parser.add_argument("--batch-size", type=int, default=8, help="Synthetic dataloader batch size.")
    parser.add_argument("--samples", type=int, default=64, help="Number of synthetic samples to generate.")
    parser.add_argument("--input-dim", type=int, default=16, help="Synthetic feature dimension.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for Lightning and synthetic data generation.")
    parser.add_argument(
        "--default-root-dir",
        type=Path,
        default=None,
        help="Writable output directory for logs/checkpoints. Defaults to a temporary directory.",
    )
    return parser.parse_args()


def run_smoke(args: argparse.Namespace) -> None:
    try:
        import torch
        import torch.nn.functional as F
        from torch import nn
        from torch.utils.data import DataLoader, TensorDataset, random_split

        import lightning as L
        from lightning.pytorch.callbacks import EarlyStopping, LearningRateMonitor, ModelCheckpoint
        from lightning.pytorch.loggers import CSVLogger
    except ModuleNotFoundError as error:  # pragma: no cover - depends on user environment
        raise SystemExit(
            "Unable to import Lightning/Torch dependencies. Install the public `lightning` package and PyTorch "
            "in this Python environment."
        ) from error

    class LitTinyAutoEncoder(L.LightningModule):
        def __init__(self, input_dim: int = 16, hidden_dim: int = 8, latent_dim: int = 3, lr: float = 1e-3) -> None:
            super().__init__()
            self.save_hyperparameters()
            self.encoder = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, latent_dim))
            self.decoder = nn.Sequential(nn.Linear(latent_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, input_dim))

        def forward(self, inputs: torch.Tensor) -> torch.Tensor:
            return self.decoder(self.encoder(inputs))

        def training_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
            return self._shared_step(batch, "train")

        def validation_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> None:
            self._shared_step(batch, "val")

        def test_step(self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> None:
            self._shared_step(batch, "test")

        def predict_step(
            self, batch: tuple[torch.Tensor, torch.Tensor], batch_idx: int, dataloader_idx: int = 0
        ) -> torch.Tensor:
            inputs, _ = batch
            return self(inputs)

        def configure_optimizers(self) -> torch.optim.Optimizer:
            return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)

        def _shared_step(self, batch: tuple[torch.Tensor, torch.Tensor], stage: str) -> torch.Tensor:
            inputs, _ = batch
            reconstruction = self(inputs)
            loss = F.mse_loss(reconstruction, inputs)
            self.log(f"{stage}_loss", loss, on_step=stage == "train", on_epoch=True, prog_bar=True, logger=True)
            return loss

    class SyntheticDataModule(L.LightningDataModule):
        def __init__(self, samples: int = 64, input_dim: int = 16, batch_size: int = 8, seed: int = 42) -> None:
            super().__init__()
            self.samples = samples
            self.input_dim = input_dim
            self.batch_size = batch_size
            self.seed = seed

        def setup(self, stage: str | None = None) -> None:
            generator = torch.Generator().manual_seed(self.seed)
            features = torch.randn(self.samples, self.input_dim, generator=generator)
            labels = torch.zeros(self.samples, dtype=torch.long)
            dataset = TensorDataset(features, labels)
            train_size = max(1, int(self.samples * 0.75))
            val_size = self.samples - train_size
            self.train_set, self.val_set = random_split(dataset, [train_size, val_size], generator=generator)
            self.test_set = self.val_set
            self.predict_set = self.val_set

        def train_dataloader(self) -> DataLoader:
            return DataLoader(self.train_set, batch_size=self.batch_size, shuffle=True)

        def val_dataloader(self) -> DataLoader:
            return DataLoader(self.val_set, batch_size=self.batch_size)

        def test_dataloader(self) -> DataLoader:
            return DataLoader(self.test_set, batch_size=self.batch_size)

        def predict_dataloader(self) -> DataLoader:
            return DataLoader(self.predict_set, batch_size=self.batch_size)

    if args.samples < 4:
        raise SystemExit("--samples must be at least 4 so train/validation splits are non-empty.")
    if args.max_steps < 1:
        raise SystemExit("--max-steps must be at least 1.")

    root_dir = args.default_root_dir or Path(tempfile.mkdtemp(prefix="lightning-smoke-"))
    L.seed_everything(args.seed, workers=True)

    data = SyntheticDataModule(samples=args.samples, input_dim=args.input_dim, batch_size=args.batch_size, seed=args.seed)
    model = LitTinyAutoEncoder(input_dim=args.input_dim)
    checkpoint = ModelCheckpoint(monitor="val_loss", mode="min", save_top_k=1, save_last=True)
    callbacks = [checkpoint, EarlyStopping(monitor="val_loss", mode="min", patience=3), LearningRateMonitor()]
    logger = CSVLogger(save_dir=str(root_dir), name="lightning_smoke")

    trainer = L.Trainer(
        accelerator="cpu",
        devices=1,
        max_steps=args.max_steps,
        max_epochs=3,
        fast_dev_run=args.fast_dev_run,
        limit_val_batches=1,
        callbacks=callbacks,
        logger=logger,
        default_root_dir=root_dir,
        enable_model_summary=False,
        enable_progress_bar=False,
        deterministic=True,
    )
    trainer.fit(model, datamodule=data)
    metrics = {key: float(value.detach().cpu()) for key, value in trainer.callback_metrics.items() if value.numel() == 1}
    print(
        "LIGHTNING_SMOKE_OK "
        f"version={L.__version__} global_step={trainer.global_step} "
        f"root_dir={root_dir} best_model_path={checkpoint.best_model_path!r} metrics={metrics}"
    )


def main() -> None:
    run_smoke(parse_args())


if __name__ == "__main__":
    main()
