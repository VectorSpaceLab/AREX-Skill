#!/usr/bin/env python3
"""Minimal Chemprop Python API smoke test.

Runs a tiny CPU-only regression workflow that exercises public data, model,
Lightning, prediction, save/load, and output-column APIs. It is intended for
quick environment checks, not model-quality benchmarking.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import tempfile

import numpy as np
import torch
from lightning import pytorch as pl

from chemprop import data, models, nn
from chemprop.models.utils import load_output_columns


def build_dataset() -> data.MoleculeDataset:
    smiles = ["CCO", "CCN", "CCC", "CCCl"]
    targets = np.array([[0.10], [0.20], [0.25], [0.35]], dtype=float)
    datapoints = [
        data.MoleculeDatapoint.from_smi(smiles_value, y=target)
        for smiles_value, target in zip(smiles, targets)
    ]
    return data.MoleculeDataset(datapoints)


def build_model() -> models.MPNN:
    message_passing = nn.BondMessagePassing(d_h=32, depth=2)
    aggregation = nn.MeanAggregation()
    predictor = nn.RegressionFFN(input_dim=message_passing.output_dim, hidden_dim=32, n_tasks=1)
    return models.MPNN(message_passing, aggregation, predictor, metrics=[nn.RMSE(), nn.MAE()])


def run_smoke(output_dir: Path | None = None, max_epochs: int = 1) -> Path:
    torch.set_num_threads(1)
    dataset = build_dataset()
    train_loader = data.build_dataloader(dataset, batch_size=2, shuffle=True, seed=0)
    predict_loader = data.build_dataloader(dataset, batch_size=2, shuffle=False)
    model = build_model()

    batch = next(iter(predict_loader))
    bmg, atom_descriptors, molecule_descriptors, *_ = batch
    with torch.no_grad():
        fingerprint = model.fingerprint(bmg, atom_descriptors, molecule_descriptors)
    assert fingerprint.shape == (2, model.predictor.input_dim), fingerprint.shape

    trainer = pl.Trainer(
        accelerator="cpu",
        devices=1,
        logger=False,
        enable_checkpointing=False,
        max_epochs=max_epochs,
        log_every_n_steps=1,
    )
    trainer.fit(model, train_loader)

    predictions = torch.cat(trainer.predict(model, predict_loader), dim=0)
    assert predictions.shape == (len(dataset), 1), predictions.shape
    assert torch.isfinite(predictions).all(), predictions

    if output_dir is None:
        temp_dir = tempfile.TemporaryDirectory()
        output_root = Path(temp_dir.name)
    else:
        temp_dir = None
        output_root = output_dir
        output_root.mkdir(parents=True, exist_ok=True)

    try:
        model_path = output_root / "chemprop-api-smoke.pt"
        models.save_model(model_path, model, output_columns=["smoke_target"])
        loaded = models.load_model(model_path)
        columns = load_output_columns(model_path)
        assert columns == ["smoke_target"], columns

        loaded_predictions = torch.cat(trainer.predict(loaded, predict_loader), dim=0)
        assert loaded_predictions.shape == predictions.shape, loaded_predictions.shape
        assert torch.isfinite(loaded_predictions).all(), loaded_predictions
        print(f"OK chemprop_api_smoke predictions_shape={tuple(predictions.shape)} model_path={model_path}")
        result_path = model_path if temp_dir is None else Path("<temporary model removed>")
        return result_path
    finally:
        if temp_dir is not None:
            temp_dir.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal Chemprop Python API smoke test.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Optional directory for the saved model.")
    parser.add_argument("--max-epochs", type=int, default=1, help="Lightning max_epochs for the smoke fit.")
    args = parser.parse_args()
    run_smoke(args.output_dir, args.max_epochs)


if __name__ == "__main__":
    main()
