#!/usr/bin/env python3
"""Run deterministic TorchMetrics basic-domain smoke checks without downloads."""

from __future__ import annotations

import json
import sys
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
    try:
        import torch
        from torchmetrics.classification import Accuracy, BinaryF1Score, MulticlassPrecision, MultilabelRecall
        from torchmetrics.clustering import ClusterAccuracy
        from torchmetrics.nominal import CramersV, FleissKappa
        from torchmetrics.regression import ContinuousRankedProbabilityScore, MeanSquaredError, R2Score
        from torchmetrics.retrieval import RetrievalNormalizedDCG, RetrievalPrecision
    except Exception as exc:  # pragma: no cover - user-facing import guard
        print(f"IMPORT_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        torch.manual_seed(1234)

        outputs: dict[str, Any] = {}

        outputs["binary_f1"] = BinaryF1Score()(torch.tensor([0.2, 0.7, 0.6, 0.1]), torch.tensor([0, 1, 1, 0]))

        multiclass_preds = torch.tensor([[0.1, 0.8, 0.1], [0.7, 0.2, 0.1]])
        multiclass_target = torch.tensor([1, 0])
        outputs["multiclass_accuracy"] = Accuracy(task="multiclass", num_classes=3)(multiclass_preds, multiclass_target)
        outputs["multiclass_precision"] = MulticlassPrecision(num_classes=3, average="macro")(
            multiclass_preds, multiclass_target
        )

        multilabel_preds = torch.tensor([[0.2, 0.9, 0.1], [0.8, 0.2, 0.7]])
        multilabel_target = torch.tensor([[0, 1, 0], [1, 0, 1]])
        outputs["multilabel_recall"] = MultilabelRecall(num_labels=3, threshold=0.5)(multilabel_preds, multilabel_target)

        outputs["mse"] = MeanSquaredError()(torch.tensor([1.0, 2.0, 4.0]), torch.tensor([1.0, 0.0, 3.0]))
        outputs["r2"] = R2Score()(torch.tensor([1.0, 2.0, 4.0]), torch.tensor([1.0, 0.0, 3.0]))
        outputs["crps"] = ContinuousRankedProbabilityScore()(torch.tensor([[0.1, 0.2, 0.3], [0.3, 0.5, 0.7]]), torch.tensor([0.2, 0.6]))

        indexes = torch.tensor([0, 0, 0, 1, 1, 1, 1])
        preds = torch.tensor([0.2, 0.3, 0.5, 0.1, 0.3, 0.5, 0.2])
        target = torch.tensor([0, 0, 1, 0, 1, 0, 1])
        outputs["ndcg"] = RetrievalNormalizedDCG()(preds, target, indexes=indexes)
        outputs["retrieval_precision"] = RetrievalPrecision(top_k=2)(preds, target, indexes=indexes)

        outputs["cluster_accuracy"] = ClusterAccuracy(num_classes=2)(torch.tensor([0, 0, 1, 1]), torch.tensor([1, 1, 0, 0]))

        outputs["cramers_v"] = CramersV(num_classes=2)(torch.tensor([0, 1, 0, 1]), torch.tensor([0, 1, 0, 1]))
        outputs["fleiss_kappa"] = FleissKappa(mode="counts")(torch.tensor([[3, 0, 0], [0, 3, 0], [0, 0, 3]]))

        summary = {"status": "ok", **{name: as_python(value) for name, value in outputs.items()}}
        print(json.dumps(summary, indent=2, sort_keys=True))
    except Exception as exc:  # pragma: no cover - user-facing failure report
        print(f"SMOKE_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
