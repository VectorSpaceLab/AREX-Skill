"""Copyable template for a PyTorch Forecasting custom multi-horizon metric.

Usage:
1. Copy this file into your project or package.
2. Rename ``AsymmetricMAE`` and update its docstring/parameters.
3. Keep ``loss()`` unreduced; ``MultiHorizonMetric`` handles masking,
   optional weights, packed targets, and reduction.
4. Import optional dependencies only inside the methods that need them.
"""

from __future__ import annotations

import torch

from pytorch_forecasting.metrics import MultiHorizonMetric


class AsymmetricMAE(MultiHorizonMetric):
    """Mean absolute error with different under/over-forecast penalties.

    Parameters
    ----------
    underforecast_weight : float, default=2.0
        Multiplier used when ``prediction < target``.
    overforecast_weight : float, default=1.0
        Multiplier used when ``prediction >= target``.
    reduction : {"mean", "sqrt-mean", "none"}, default="mean"
        Reduction strategy delegated to ``MultiHorizonMetric``.
    **kwargs
        Additional keyword arguments accepted by ``MultiHorizonMetric``.
    """

    def __init__(
        self,
        underforecast_weight: float = 2.0,
        overforecast_weight: float = 1.0,
        reduction: str = "mean",
        **kwargs,
    ) -> None:
        if underforecast_weight <= 0:
            raise ValueError("underforecast_weight must be positive")
        if overforecast_weight <= 0:
            raise ValueError("overforecast_weight must be positive")

        super().__init__(reduction=reduction, **kwargs)
        self.underforecast_weight = float(underforecast_weight)
        self.overforecast_weight = float(overforecast_weight)

    def loss(self, y_pred: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """Return unreduced asymmetric absolute error.

        ``y_pred`` can be shaped ``(batch, horizon)`` or
        ``(batch, horizon, 1)`` for point forecasts. ``target`` should be
        shaped ``(batch, horizon)``. The base class handles masks, weights,
        packed targets, and final reduction.
        """
        prediction = self.to_prediction(y_pred)
        error = prediction - target
        under = torch.as_tensor(
            self.underforecast_weight,
            dtype=error.dtype,
            device=error.device,
        )
        over = torch.as_tensor(
            self.overforecast_weight,
            dtype=error.dtype,
            device=error.device,
        )
        weights = torch.where(error < 0, under, over)
        return weights * error.abs()


def _demo() -> None:
    """Small CPU self-check for the template."""
    metric = AsymmetricMAE(underforecast_weight=2.0, overforecast_weight=1.0)
    y_pred = torch.tensor(
        [
            [[1.0], [2.0], [4.0]],
            [[2.0], [2.5], [3.0]],
        ]
    )
    target = torch.tensor(
        [
            [2.0, 2.0, 3.0],
            [1.5, 3.0, 3.0],
        ]
    )

    unreduced = metric.loss(y_pred, target)
    assert unreduced.shape == target.shape
    assert torch.isfinite(unreduced).all()

    metric.update(y_pred, target)
    value = metric.compute()
    assert value.ndim == 0
    assert torch.isfinite(value)
    print(f"AsymmetricMAE demo value: {value.item():.6f}")


if __name__ == "__main__":
    _demo()
