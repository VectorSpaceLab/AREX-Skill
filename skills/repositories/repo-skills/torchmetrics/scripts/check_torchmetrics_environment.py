#!/usr/bin/env python3
"""Check the installed TorchMetrics environment without downloads."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def choose_device(choice: str):
    import torch

    if choice == "cpu":
        return torch.device("cpu")
    if choice == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("--device cuda was requested, but torch.cuda.is_available() is False")
        return torch.device("cuda")
    if choice == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    raise ValueError(f"unsupported device choice: {choice}")


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
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "cuda"),
        default="auto",
        help="Device for the tiny smoke tensors.",
    )
    args = parser.parse_args(argv)

    try:
        import torch
        import torchmetrics
        from torchmetrics import MetricCollection
        from torchmetrics.classification import Accuracy
        from torchmetrics.regression import MeanSquaredError
        from torchmetrics.utilities import imports as tm_imports
    except Exception as exc:  # pragma: no cover - user-facing import guard
        print(f"IMPORT_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        device = choose_device(args.device)
    except Exception as exc:
        print(f"DEVICE_UNAVAILABLE: {exc}", file=sys.stderr)
        return 2

    try:
        preds = torch.tensor([[0.1, 0.8, 0.1], [0.7, 0.2, 0.1]], device=device)
        target = torch.tensor([1, 2], device=device)
        acc = Accuracy(task="multiclass", num_classes=3).to(device)
        mse = MeanSquaredError().to(device)
        acc_collection = MetricCollection({"acc": Accuracy(task="multiclass", num_classes=3)}).to(device)
        mse_collection = MetricCollection({"mse": MeanSquaredError()}).to(device)

        acc_value = acc(preds, target)
        mse_value = mse(torch.tensor([1.0, 2.0], device=device), torch.tensor([0.0, 1.0], device=device))
        collection_acc_values = acc_collection(preds, target)
        collection_mse_values = mse_collection(
            torch.tensor([1.0, 2.0], device=device), torch.tensor([0.0, 1.0], device=device)
        )

        if not torch.isclose(acc_value, torch.tensor(0.5, device=device)):
            raise RuntimeError(f"Accuracy smoke returned {acc_value}")
        if not torch.isfinite(mse_value):
            raise RuntimeError(f"MeanSquaredError smoke returned {mse_value}")
        if set(collection_acc_values) != {"acc"}:
            raise RuntimeError(f"MetricCollection classification smoke returned unexpected keys: {sorted(collection_acc_values)}")
        if set(collection_mse_values) != {"mse"}:
            raise RuntimeError(f"MetricCollection regression smoke returned unexpected keys: {sorted(collection_mse_values)}")

        optional_flags = {
            "matplotlib": bool(tm_imports._MATPLOTLIB_AVAILABLE),
            "torchvision": bool(tm_imports._TORCHVISION_AVAILABLE),
            "torchaudio": bool(tm_imports._TORCHAUDIO_AVAILABLE),
            "transformers": bool(tm_imports._TRANSFORMERS_AVAILABLE),
            "torch_fidelity": bool(tm_imports._TORCH_FIDELITY_AVAILABLE),
            "pycocotools": bool(tm_imports._PYCOCOTOOLS_AVAILABLE),
            "fast_bss_eval": bool(tm_imports._FAST_BSS_EVAL_AVAILABLE),
            "librosa": bool(tm_imports._LIBROSA_AVAILABLE),
            "onnxruntime": bool(tm_imports._ONNXRUNTIME_AVAILABLE),
            "nltk": bool(tm_imports._NLTK_AVAILABLE),
            "regex": bool(tm_imports._REGEX_AVAILABLE),
            "sentencepiece": bool(tm_imports._SENTENCEPIECE_AVAILABLE),
            "torch_linear_assignment": bool(tm_imports._TORCH_LINEAR_ASSIGNMENT_AVAILABLE),
            "piq>=0.8": bool(tm_imports._PIQ_GREATER_EQUAL_0_8),
            "vmaf_torch": bool(tm_imports._TORCH_VMAF_AVAILABLE),
        }

        summary = {
            "status": "ok",
            "torch_version": torch.__version__,
            "torchmetrics_version": getattr(torchmetrics, "__version__", "unknown"),
            "device": str(device),
            "cuda_available": bool(torch.cuda.is_available()),
            "core_metrics": {
                "accuracy": as_python(acc_value),
                "mean_squared_error": as_python(mse_value),
                "collection_accuracy": as_python(collection_acc_values),
                "collection_mean_squared_error": as_python(collection_mse_values),
            },
            "optional_dependencies": optional_flags,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
    except Exception as exc:  # pragma: no cover - user-facing failure report
        print(f"SMOKE_FAILED: {exc.__class__.__name__}: {exc}", file=sys.stderr)
        return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
