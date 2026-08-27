#!/usr/bin/env python3
"""Run a deterministic TorchMetrics core API smoke check.

This script imports an installed torchmetrics package and executes small CPU/CUDA
examples for Accuracy, MeanSquaredError, MetricCollection, and a custom Metric.
It performs no downloads, no network access, no credential access, and no native
repository tests.

Example:
    python scripts/core_metric_smoke.py --device auto
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def _choose_device(requested: str):
    import torch

    if requested == "cpu":
        return torch.device("cpu")
    if requested == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("--device cuda was requested, but torch.cuda.is_available() is False")
        return torch.device("cuda")
    if requested == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    raise ValueError(f"unsupported device choice: {requested}")


def _as_float(value: Any) -> float:
    import torch

    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Smoke-test TorchMetrics core APIs without downloads.")
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device for tiny tensors. 'auto' uses CUDA only when torch reports it as available.",
    )
    args = parser.parse_args(argv)

    try:
        import torch
        import torchmetrics
        from torch import Tensor
        from torchmetrics import Metric, MetricCollection
        from torchmetrics.classification import Accuracy
        from torchmetrics.regression import MeanSquaredError
        from torchmetrics.utilities.data import dim_zero_cat
    except Exception as exc:  # pragma: no cover - intended user-facing import guard
        print(f"IMPORT_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        device = _choose_device(args.device)
    except Exception as exc:
        print(f"DEVICE_UNAVAILABLE: {exc}", file=sys.stderr)
        return 2

    torch.manual_seed(1234)

    class MeanAbsoluteErrorListMetric(Metric):
        """Small custom Metric demonstrating add_state with a list state."""

        is_differentiable = False
        higher_is_better = False
        full_state_update = False

        def __init__(self, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self.add_state("errors", default=[], dist_reduce_fx="cat")

        def update(self, preds: Tensor, target: Tensor) -> None:
            if preds.shape != target.shape:
                raise ValueError("preds and target must have identical shapes")
            self.errors.append((preds - target).detach().reshape(-1))

        def compute(self) -> Tensor:
            if isinstance(self.errors, list):
                if not self.errors:
                    return torch.tensor(0.0, device=self.device)
                errors = dim_zero_cat(self.errors)
            else:
                errors = self.errors
            return errors.abs().mean()

    try:
        logits0 = torch.tensor(
            [[0.1, 0.8, 0.1], [0.2, 0.1, 0.7], [0.9, 0.1, 0.0], [0.1, 0.7, 0.2]],
            device=device,
        )
        target0 = torch.tensor([1, 2, 0, 0], device=device)
        logits1 = torch.tensor([[0.0, 0.6, 0.4], [0.2, 0.7, 0.1]], device=device)
        target1 = torch.tensor([1, 2], device=device)

        acc = Accuracy(task="multiclass", num_classes=3).to(device)
        batch_acc = acc(logits0, target0)
        acc.update(logits1, target1)
        accumulated_acc = acc.compute()
        expected_batch_acc = torch.tensor(0.75, device=device)
        expected_accumulated_acc = torch.tensor(4.0 / 6.0, device=device)
        if not torch.allclose(batch_acc, expected_batch_acc):
            raise AssertionError(f"Accuracy batch value mismatch: got {batch_acc}, expected {expected_batch_acc}")
        if not torch.allclose(accumulated_acc, expected_accumulated_acc):
            raise AssertionError(
                f"Accuracy accumulated value mismatch: got {accumulated_acc}, expected {expected_accumulated_acc}"
            )

        mse = MeanSquaredError().to(device)
        mse.update(torch.tensor([1.0, 2.0, 4.0], device=device), torch.tensor([1.0, 0.0, 3.0], device=device))
        mse_value = mse.compute()
        expected_mse = torch.tensor(5.0 / 3.0, device=device)
        if not torch.allclose(mse_value, expected_mse):
            raise AssertionError(f"MSE mismatch: got {mse_value}, expected {expected_mse}")

        class_preds = torch.tensor([1, 0, 0, 2], device=device)
        class_target = torch.tensor([1, 2, 0, 2], device=device)
        collection = MetricCollection(
            {
                "accuracy": Accuracy(task="multiclass", num_classes=3),
                "class_id_mse": MeanSquaredError(),
            }
        ).to(device)
        collection_values = collection(class_preds, class_target)
        if set(collection_values) != {"accuracy", "class_id_mse"}:
            raise AssertionError(f"MetricCollection returned unexpected keys: {sorted(collection_values)}")
        if not torch.allclose(collection_values["accuracy"], torch.tensor(0.75, device=device)):
            raise AssertionError(f"MetricCollection accuracy mismatch: {collection_values['accuracy']}")
        if not torch.allclose(collection_values["class_id_mse"], torch.tensor(1.0, device=device)):
            raise AssertionError(f"MetricCollection MSE mismatch: {collection_values['class_id_mse']}")

        custom = MeanAbsoluteErrorListMetric().to(device)
        batch_mae = custom(torch.tensor([1.0, 3.0], device=device), torch.tensor([2.0, 1.0], device=device))
        custom.update(torch.tensor([0.0, 4.0], device=device), torch.tensor([0.5, 1.0], device=device))
        accumulated_mae = custom.compute()
        if not torch.allclose(batch_mae, torch.tensor(1.5, device=device)):
            raise AssertionError(f"Custom batch MAE mismatch: {batch_mae}")
        if not torch.allclose(accumulated_mae, torch.tensor(1.625, device=device)):
            raise AssertionError(f"Custom accumulated MAE mismatch: {accumulated_mae}")
        custom.reset()
        if custom.update_count != 0 or len(custom.errors) != 0:
            raise AssertionError("Custom metric reset did not clear update_count and list state")

    except Exception as exc:  # pragma: no cover - intended user-facing failure report
        print(f"SMOKE_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 3

    summary = {
        "status": "ok",
        "torch_version": torch.__version__,
        "torchmetrics_version": getattr(torchmetrics, "__version__", "unknown"),
        "device": str(device),
        "accuracy_batch": _as_float(batch_acc),
        "accuracy_accumulated": _as_float(accumulated_acc),
        "mean_squared_error": _as_float(mse_value),
        "collection": {key: _as_float(val) for key, val in collection_values.items()},
        "custom_batch_mae": _as_float(batch_mae),
        "custom_accumulated_mae": _as_float(accumulated_mae),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
