#!/usr/bin/env python3
"""Run a tiny deterministic fixed or automatic pmdarima forecast.

The script intentionally uses generated data, has no network or plotting
requirements, and can be invoked from any working directory where pmdarima is
installed, for example:

    python /path/to/simple_forecast.py --mode fixed --horizon 3
    python /path/to/simple_forecast.py --mode auto --horizon 3
"""

from __future__ import annotations

import argparse

import numpy as np


def make_series() -> np.ndarray:
    """Return a short, deterministic series with a four-step cycle."""
    t = np.arange(24, dtype=float)
    return 10.0 + 0.08 * t + 0.7 * np.sin(2.0 * np.pi * t / 4.0) + 0.15 * np.cos(
        2.0 * np.pi * t / 7.0
    )


def fit_model(y: np.ndarray, mode: str):
    # Keep imports inside the execution path so ``--help`` remains available
    # even when the caller is diagnosing an unavailable compiled extension.
    from pmdarima import ARIMA, StepwiseContext, auto_arima

    if mode == "fixed":
        return ARIMA(
            order=(1, 0, 0),
            seasonal_order=(0, 1, 0, 4),
            maxiter=50,
            suppress_warnings=True,
        ).fit(y)

    # Keep automatic search deterministic and bounded for a smoke test.
    with StepwiseContext(max_steps=12, max_dur=10):
        return auto_arima(
            y,
            seasonal=True,
            m=4,
            start_p=0,
            start_q=0,
            max_p=1,
            max_q=1,
            start_P=0,
            start_Q=0,
            max_P=1,
            max_Q=1,
            max_d=1,
            max_D=1,
            max_order=3,
            stepwise=True,
            error_action="ignore",
            suppress_warnings=True,
            maxiter=30,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fit a deterministic tiny ARIMA forecast without network or plots."
    )
    parser.add_argument(
        "--mode",
        choices=("fixed", "auto"),
        default="fixed",
        help="use a fixed seasonal ARIMA or bounded auto_arima (default: fixed)",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=3,
        help="number of future periods to forecast (default: 3)",
    )
    args = parser.parse_args()
    if args.horizon < 1:
        parser.error("--horizon must be a positive integer")
    return args


def main() -> int:
    args = parse_args()
    y = make_series()
    try:
        model = fit_model(y, args.mode)
        forecast, conf_int = model.predict(
            n_periods=args.horizon,
            return_conf_int=True,
            alpha=0.05,
        )
        forecast = np.asarray(forecast)
        conf_int = np.asarray(conf_int)

        # Assertions make this a smoke check rather than a print-only demo:
        # a broken fit, backend change, or malformed return must exit nonzero.
        assert isinstance(model.order, tuple) and len(model.order) == 3
        assert isinstance(model.seasonal_order, tuple)
        assert forecast.shape == (args.horizon,)
        assert conf_int.shape == (args.horizon, 2)
        assert np.isfinite(forecast).all()
        assert np.isfinite(conf_int).all()
    except Exception as exc:  # pragma: no cover - environment-dependent
        print(f"forecast smoke failed: {type(exc).__name__}: {exc}")
        return 1

    print(f"mode={args.mode}")
    print(f"order={model.order}")
    print(f"seasonal_order={model.seasonal_order}")
    print(f"forecast_shape={forecast.shape}")
    print(f"confidence_interval_shape={conf_int.shape}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
