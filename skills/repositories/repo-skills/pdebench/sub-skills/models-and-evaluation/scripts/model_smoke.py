#!/usr/bin/env python3
"""Deterministic, no-data CPU construction checks for PDEBench models/metrics."""

from __future__ import annotations

import argparse

import torch

from pdebench.models import metrics as metrics_module
from pdebench.models.fno.fno import FNO1d, FNO2d, FNO3d
from pdebench.models.unet.unet import UNet1d, UNet2d, UNet3d


def _finite(tensor: torch.Tensor, label: str) -> None:
    assert torch.isfinite(tensor).all().item(), f"{label} contains non-finite values"


def check_fno() -> None:
    """Exercise all three FNO dimensionalities with tiny CPU tensors."""
    cases = [
        (
            FNO1d(num_channels=1, modes=2, width=2, initial_step=2),
            torch.randn(1, 8, 2),
            torch.linspace(0, 1, 8).reshape(1, 8, 1),
            (1, 8, 1, 1),
        ),
        (
            FNO2d(num_channels=1, modes1=2, modes2=2, width=2, initial_step=2),
            torch.randn(1, 8, 8, 2),
            torch.zeros(1, 8, 8, 2),
            (1, 8, 8, 1, 1),
        ),
        (
            FNO3d(
                num_channels=1,
                modes1=2,
                modes2=2,
                modes3=2,
                width=2,
                initial_step=2,
            ),
            torch.randn(1, 8, 8, 8, 2),
            torch.zeros(1, 8, 8, 8, 3),
            (1, 8, 8, 8, 1, 1),
        ),
    ]
    for model, x, grid, expected in cases:
        model = model.cpu().eval()
        with torch.no_grad():
            output = model(x, grid)
        assert output.shape == expected, (type(model).__name__, output.shape, expected)
        _finite(output, type(model).__name__)


def check_unet() -> None:
    """Exercise all three channel-first U-Net dimensionalities."""
    cases = [
        (UNet1d(in_channels=2, out_channels=1, init_features=2), (1, 2, 16), (1, 1, 16)),
        (
            UNet2d(in_channels=2, out_channels=1, init_features=2),
            (1, 2, 16, 16),
            (1, 1, 16, 16),
        ),
        (
            UNet3d(in_channels=2, out_channels=1, init_features=2),
            (1, 2, 16, 16, 16),
            (1, 1, 16, 16, 16),
        ),
    ]
    for model, input_shape, expected in cases:
        model = model.cpu().eval()
        with torch.no_grad():
            output = model(torch.randn(*input_shape))
        assert output.shape == expected, (type(model).__name__, output.shape, expected)
        _finite(output, type(model).__name__)


def check_metrics() -> None:
    """Check the six metric outputs without depending on CUDA availability."""
    # metric_func uses a module-level device in the source implementation.
    # Override it for this explicitly CPU-only smoke test.
    metrics_module.device = torch.device("cpu")
    target = torch.linspace(0.25, 1.25, 1 * 8 * 3).reshape(1, 8, 3, 1)
    pred = target + 0.01
    values = metrics_module.metric_func(
        pred,
        target,
        if_mean=True,
        iLow=1,
        iHigh=2,
        initial_step=1,
    )
    assert len(values) == 6
    # The Fourier metric intentionally retains its three frequency bands;
    # the other five values are scalar means for this one-channel fixture.
    expected_ndims = [0, 0, 0, 0, 0, 1]
    for index, (value, expected_ndim) in enumerate(zip(values, expected_ndims)):
        assert value.ndim == expected_ndim, (index, value.shape, expected_ndim)
        if index == 5:
            assert value.shape == (3,), value.shape
        _finite(value, f"metric[{index}]")

    loss = metrics_module.LpLoss(p=2, reduction="mean")(pred, target)
    fft_loss = metrics_module.FftLpLoss(p=2, reduction="mean")(pred, target)
    fft_mse = metrics_module.FftMseLoss(reduction="mean")(pred, target)
    for label, value in (("LpLoss", loss), ("FftLpLoss", fft_loss), ("FftMseLoss", fft_mse)):
        assert value.ndim == 0, (label, value.shape)
        _finite(value, label)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run deterministic tiny CPU checks for PDEBench FNO, U-Net, and metrics."
    )
    parser.add_argument("--seed", type=int, default=0, help="Torch seed (default: 0).")
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    torch.set_num_threads(1)

    check_fno()
    check_unet()
    check_metrics()
    print("model_smoke: PASS (FNO1d/2d/3d, UNet1d/2d/3d, metrics; CPU; no epochs)")


if __name__ == "__main__":
    main()
