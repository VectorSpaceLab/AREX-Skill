#!/usr/bin/env python3
"""Inspect the BasicTS pipeline contract and optionally run tiny synthetic checks.

This helper is read-only by default. It prints the taskflow, callback, metric,
and scaler contracts from the installed BasicTS package and can optionally run
small synthetic validations that do not depend on the original repository
checkout.

Examples:
    python scripts/inspect_pipeline_contract.py
    python scripts/inspect_pipeline_contract.py --validate
"""

from __future__ import annotations

import argparse
import inspect
from types import SimpleNamespace

import numpy as np
import torch

from basicts.metrics import ALL_METRICS, accuracy, masked_mse
from basicts.runners.basicts_runner import BasicTSRunner
from basicts.runners.callback import (
    AddAuxiliaryLoss,
    BasicTSCallback,
    BasicTSCallbackHandler,
    CurriculumLearning,
    EarlyStopping,
    GradAccumulation,
    GradientClipping,
    NoBP,
    SelectiveLearning,
)
from basicts.runners.taskflow import (
    BasicTSClassificationTaskFlow,
    BasicTSForecastingTaskFlow,
    BasicTSImputationTaskFlow,
    BasicTSTaskFlow,
)
from basicts.scaler import BasicTSScaler, MinMaxScaler, ZScoreScaler
from basicts.utils.mask import null_val_mask, reconstruction_mask


def describe_signature(name: str, obj) -> None:
    print(f"{name}={inspect.signature(obj)}")


def summarize_contract() -> None:
    print(f"taskflow_base={BasicTSTaskFlow.__name__}")
    describe_signature("taskflow_preprocess", BasicTSTaskFlow.preprocess)
    describe_signature("taskflow_postprocess", BasicTSTaskFlow.postprocess)
    describe_signature("taskflow_get_weight", BasicTSTaskFlow.get_weight)

    print(f"callbacks={', '.join([cls.__name__ for cls in [BasicTSCallback, BasicTSCallbackHandler, AddAuxiliaryLoss, GradientClipping, EarlyStopping, GradAccumulation, NoBP, SelectiveLearning, CurriculumLearning]])}")
    for cls in [BasicTSCallback, AddAuxiliaryLoss, GradientClipping, EarlyStopping, GradAccumulation, NoBP, SelectiveLearning, CurriculumLearning]:
        describe_signature(cls.__name__, cls.__init__)

    print(f"scalers={', '.join([cls.__name__ for cls in [BasicTSScaler, ZScoreScaler, MinMaxScaler]])}")
    for cls in [BasicTSScaler, ZScoreScaler, MinMaxScaler]:
        describe_signature(cls.__name__, cls.__init__)
        describe_signature(f"{cls.__name__}.fit", cls.fit)
        describe_signature(f"{cls.__name__}.transform", cls.transform)
        describe_signature(f"{cls.__name__}.inverse_transform", cls.inverse_transform)

    print(f"metrics={', '.join(sorted(ALL_METRICS))}")
    describe_signature("masked_mse", masked_mse)
    describe_signature("accuracy", accuracy)

    for cls in [BasicTSForecastingTaskFlow, BasicTSClassificationTaskFlow, BasicTSImputationTaskFlow]:
        print(f"{cls.__name__}={cls.__name__}")
        describe_signature(f"{cls.__name__}.preprocess", cls.preprocess)
        describe_signature(f"{cls.__name__}.postprocess", cls.postprocess)
        describe_signature(f"{cls.__name__}.get_weight", cls.get_weight)

    describe_signature("BasicTSRunner.__init__", BasicTSRunner.__init__)
    describe_signature("BasicTSRunner._forward", BasicTSRunner._forward)
    describe_signature("BasicTSRunner._metric_forward", BasicTSRunner._metric_forward)


def run_validate() -> int:
    print("-- synthetic validation --")

    base = torch.tensor([[1.0, 2.0], [3.0, 4.0]], dtype=torch.float32)
    mask = null_val_mask(base, np.nan)
    print(f"null_val_mask_sum={int(mask.sum().item())}")

    recon_mask = reconstruction_mask(base, 0.25)
    print(f"reconstruction_mask_sum={int(recon_mask.sum().item())}")

    scaler = ZScoreScaler(norm_each_channel=True, rescale=False)
    scaler.fit(base.numpy())
    transformed = scaler.transform(base, mask=torch.ones_like(base, dtype=torch.bool))
    recovered = scaler.inverse_transform(transformed, mask=torch.ones_like(base, dtype=torch.bool))
    print(f"zscore_transformed_shape={tuple(transformed.shape)}")
    print(f"zscore_recovered_close={torch.allclose(base, recovered, atol=1e-5)}")

    minmax = MinMaxScaler(norm_each_channel=True, rescale=False)
    minmax.fit(base.numpy())
    mm = minmax.transform(base)
    mm_back = minmax.inverse_transform(mm)
    print(f"minmax_recovered_close={torch.allclose(base, mm_back, atol=1e-5)}")

    prediction = torch.ones((2, 2), dtype=torch.float32)
    targets = torch.zeros((2, 2), dtype=torch.float32)
    targets_mask = torch.tensor([[True, False], [True, True]])
    print(f"masked_mse={masked_mse(prediction=prediction, targets=targets, targets_mask=targets_mask).item():.4f}")

    logits = torch.tensor([[0.1, 0.9], [0.7, 0.3]], dtype=torch.float32)
    labels = torch.tensor([1, 0], dtype=torch.int64)
    print(f"accuracy={accuracy(prediction=logits.argmax(dim=-1), targets=labels).item():.4f}")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect the BasicTS pipeline contract.")
    parser.add_argument("--validate", action="store_true", help="Run tiny synthetic validation checks.")
    args = parser.parse_args()

    summarize_contract()
    if args.validate:
        return run_validate()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
