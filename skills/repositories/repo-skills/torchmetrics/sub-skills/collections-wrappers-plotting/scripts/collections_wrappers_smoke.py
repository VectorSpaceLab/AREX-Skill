#!/usr/bin/env python3
"""Run deterministic TorchMetrics collection, wrapper, tracker, and plotting checks."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def as_python(value: Any) -> Any:
    import torch

    if isinstance(value, torch.Tensor):
        value = value.detach().cpu()
        if value.numel() == 1:
            return value.item()
        return value.tolist()
    if isinstance(value, dict):
        return {key: as_python(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_python(val) for val in value]
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plot", type=Path, default=None, help="Optional path where an Agg plot should be saved.")
    args = parser.parse_args(argv)

    try:
        import torch
        from torchmetrics import MetricCollection
        from torchmetrics.classification import BinaryAccuracy, MulticlassAccuracy, MulticlassRecall
        from torchmetrics.regression import MeanSquaredError
        from torchmetrics.wrappers import ClasswiseWrapper, MetricTracker, MinMaxMetric, MultioutputWrapper
    except Exception as exc:  # pragma: no cover - user-facing import guard
        print(f"IMPORT_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        torch.manual_seed(1234)
        preds = torch.tensor([[0.1, 0.8, 0.1], [0.7, 0.2, 0.1], [0.2, 0.1, 0.7]])
        target = torch.tensor([1, 0, 2])

        base = MetricCollection(
            {
                "acc": MulticlassAccuracy(num_classes=3),
                "recall": MulticlassRecall(num_classes=3, average="macro"),
            }
        )
        train_metrics = base.clone(prefix="train_")
        val_metrics = base.clone(prefix="val_")
        train_values = train_metrics(preds, target)
        val_metrics.update(preds, target)
        val_values = val_metrics.compute()
        val_metrics.reset()

        classwise = ClasswiseWrapper(
            MulticlassAccuracy(num_classes=3, average=None),
            labels=["class0", "class1", "class2"],
            prefix="acc_",
        )
        classwise_values = classwise(preds, target)

        tracker = MetricTracker(MulticlassAccuracy(num_classes=3), maximize=True)
        tracker.increment()
        tracker.update(preds, target)
        tracker.increment()
        tracker.update(torch.flip(preds, dims=[0]), target)
        best_value, best_step = tracker.best_metric(return_step=True)

        minmax = MinMaxMetric(BinaryAccuracy())
        minmax(torch.tensor([0.9, 0.8, 0.1]), torch.tensor([1, 1, 0]))
        minmax.update(torch.tensor([0.2, 0.2, 0.8]), torch.tensor([1, 0, 1]))
        minmax_values = minmax.compute()

        multioutput = MultioutputWrapper(MeanSquaredError(), num_outputs=2, output_dim=-1)
        mo_values = multioutput(
            torch.tensor([[1.0, 2.0], [2.0, 4.0]]),
            torch.tensor([[1.0, 1.0], [3.0, 2.0]]),
        )

        plot_path = None
        if args.plot is not None:
            import matplotlib
            import torchmetrics.utilities.plot as tm_plot

            matplotlib.use("Agg")
            matplotlib.rcParams["text.usetex"] = False
            if isinstance(getattr(tm_plot, "_style", None), list):
                tm_plot._style[:] = ["default"]
            metric_for_plot = BinaryAccuracy()
            metric_for_plot.update(torch.tensor([0.9, 0.8, 0.1]), torch.tensor([1, 1, 0]))
            fig, _ax = metric_for_plot.plot()
            args.plot.parent.mkdir(parents=True, exist_ok=True)
            fig.savefig(args.plot)
            plot_path = str(args.plot)

        summary = {
            "status": "ok",
            "train_collection": as_python(train_values),
            "val_collection": as_python(val_values),
            "classwise": as_python(classwise_values),
            "tracker_best_value": as_python(best_value),
            "tracker_best_step": as_python(best_step),
            "minmax": as_python(minmax_values),
            "multioutput": as_python(mo_values),
            "plot_path": plot_path,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
    except Exception as exc:  # pragma: no cover - user-facing failure report
        print(f"SMOKE_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
