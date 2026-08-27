#!/usr/bin/env python3
"""Run tiny deterministic NeuralForecast loss checks.

Purpose:
- Confirm that the main loss classes import and behave as expected on tiny tensors.
- Keep the check safe, CPU-only, and free of training or downloads.

Prerequisites:
- Torch and NeuralForecast installed in the active environment.

Example:
    python scripts/check_losses.py
"""

from __future__ import annotations

import argparse
import warnings

import torch


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(description=__doc__)


def main() -> int:
    build_parser().parse_args()

    from neuralforecast.losses.pytorch import DistributionLoss, MAE, MQLoss, GMM

    y = torch.tensor([[[0.0], [0.0], [0.0]], [[0.0], [0.0], [0.0]]])
    y_hat = torch.tensor([[[0.0], [0.0], [1.0]], [[1.0], [0.0], [1.0]]])
    mask = torch.ones_like(y)

    mae = MAE(horizon_weight=torch.tensor([1.0, 1.0, 1.0]))
    mae_value = mae(y=y, y_hat=y_hat, mask=mask)
    assert torch.isclose(mae_value, torch.tensor(0.5)), mae_value

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        mq = MQLoss(level=[80, 80])
    assert len(caught) == 1
    assert len(mq.quantiles) == 3

    dloss = DistributionLoss(distribution="Normal", level=[80, 90])
    assert len(dloss.quantiles) == 5

    gmm = GMM(n_components=2, level=[80, 90])
    assert len(gmm.quantiles) == 5

    print("loss checks passed")
    print(f"MAE={mae_value.item():.4f} quantiles={mq.quantiles.tolist()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
