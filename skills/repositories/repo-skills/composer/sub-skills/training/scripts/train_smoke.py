#!/usr/bin/env python3
"""CPU-safe Composer Trainer smoke test with random classification data.

The script uses only public Composer APIs and synthetic tensors. It performs a
short train/eval/predict workflow without downloads.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

try:
    from composer import Trainer
    from composer.models import ComposerClassifier
except ModuleNotFoundError as exc:
    if exc.name == "composer":
        raise SystemExit("Unable to import composer. Install the public package with: pip install mosaicml") from exc
    raise


def build_loader(samples: int, features: int, classes: int, batch_size: int, seed: int) -> DataLoader:
    """Create a deterministic random classification dataloader."""
    generator = torch.Generator().manual_seed(seed)
    inputs = torch.randn(samples, features, generator=generator)
    targets = torch.randint(low=0, high=classes, size=(samples,), generator=generator)
    return DataLoader(TensorDataset(inputs, targets), batch_size=batch_size, shuffle=False)


def build_model(features: int, hidden: int, classes: int) -> ComposerClassifier:
    """Wrap a tiny PyTorch module in ComposerClassifier."""
    module = nn.Sequential(
        nn.Linear(features, hidden),
        nn.ReLU(),
        nn.Linear(hidden, classes),
    )
    return ComposerClassifier(module=module, num_classes=classes)


def metric_to_float(value: Any) -> float:
    """Convert a TorchMetric compute result or scalar-like value to float."""
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=32, help="Number of synthetic samples per split.")
    parser.add_argument("--features", type=int, default=8, help="Input feature dimension.")
    parser.add_argument("--hidden", type=int, default=16, help="Hidden layer width.")
    parser.add_argument("--classes", type=int, default=3, help="Number of classification classes.")
    parser.add_argument("--batch-size", type=int, default=8, help="Per-device dataloader batch size.")
    parser.add_argument("--batches", type=int, default=2, help="Number of training batches to run.")
    parser.add_argument("--eval-batches", type=int, default=1, help="Number of eval batches for standalone eval.")
    parser.add_argument("--lr", type=float, default=0.05, help="SGD learning rate.")
    parser.add_argument("--seed", type=int, default=17, help="Random seed for data and model initialization.")
    parser.add_argument("--run-name", default="composer-train-smoke", help="Stable Composer run name.")
    parser.add_argument("--predict", action="store_true", help="Also run one prediction batch and report output shape.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.samples < args.batch_size * args.batches:
        raise ValueError("--samples must be at least --batch-size * --batches for this smoke test.")
    if args.classes < 2:
        raise ValueError("--classes must be at least 2 for classification metrics.")

    torch.manual_seed(args.seed)
    train_loader = build_loader(args.samples, args.features, args.classes, args.batch_size, args.seed)
    eval_loader = build_loader(args.samples, args.features, args.classes, args.batch_size, args.seed + 1)

    model = build_model(args.features, args.hidden, args.classes)
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr)

    trainer = Trainer(
        model=model,
        train_dataloader=train_loader,
        eval_dataloader=eval_loader,
        optimizers=optimizer,
        max_duration=f"{args.batches}ba",
        train_subset_num_batches=args.batches,
        eval_subset_num_batches=args.eval_batches,
        eval_interval=0,
        device="cpu",
        precision="fp32",
        run_name=args.run_name,
        progress_bar=False,
        log_to_console=False,
    )
    trainer.fit()
    trainer.eval(subset_num_batches=args.eval_batches)

    prediction_shape: list[int] | None = None
    if args.predict:
        predictions = trainer.predict(eval_loader, subset_num_batches=1, return_outputs=True)
        if predictions:
            prediction_shape = list(predictions[0].shape)

    train_metrics = {
        name: metric_to_float(metric.compute())
        for name, metric in (trainer.state.train_metrics or {}).items()
    }
    eval_metrics = {
        label: {name: metric_to_float(metric.compute()) for name, metric in metrics.items()}
        for label, metrics in trainer.state.eval_metrics.items()
    }

    result = {
        "run_name": trainer.state.run_name,
        "timestamp": {
            "batch": int(trainer.state.timestamp.batch),
            "sample": int(trainer.state.timestamp.sample),
            "token": int(trainer.state.timestamp.token),
        },
        "train_metrics": train_metrics,
        "eval_metrics": eval_metrics,
        "prediction_shape": prediction_shape,
    }

    if result["timestamp"]["batch"] != args.batches:
        raise RuntimeError(f"Expected {args.batches} batches, got {result['timestamp']['batch']}.")
    if "eval" not in result["eval_metrics"]:
        raise RuntimeError("Expected standalone eval metrics under label 'eval'.")

    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
