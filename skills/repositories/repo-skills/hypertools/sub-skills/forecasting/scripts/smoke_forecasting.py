#!/usr/bin/env python3
"""Tiny forecast and impute smoke test for the forecasting sub-skill."""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    import hypertools as hyp
except Exception as exc:  # pragma: no cover - exercised in runtime envs
    raise SystemExit(f'unable to import hypertools: {exc}') from exc


def sine_forecast_smoke() -> None:
    t = np.linspace(0.0, 4.0 * np.pi, 48)
    series = pd.DataFrame({'signal': np.sin(t)})
    forecast = hyp.predict(series, model='Kalman', t=5)
    assert isinstance(forecast, pd.DataFrame)
    assert forecast.shape == (5, 1)
    assert list(forecast.columns) == ['signal']
    assert np.isfinite(forecast.to_numpy()).all()


def low_rank_impute_smoke() -> None:
    rng = np.random.default_rng(0)
    grid = np.linspace(-1.0, 1.0, 40)
    latents = np.column_stack([
        np.sin(grid),
        np.cos(0.7 * grid),
        np.sin(1.3 * grid),
    ])
    weights = np.array([
        [1.0, 0.3, -0.7, 0.2],
        [0.5, -1.1, 0.2, 0.8],
        [-0.4, 0.6, 0.9, -0.3],
    ])
    data = pd.DataFrame(
        latents @ weights + 0.02 * rng.standard_normal((40, 4)),
        columns=list('abcd'),
    )
    data.loc[5, 'b'] = np.nan
    data.loc[12, 'c'] = np.nan
    data.loc[25, 'a'] = np.nan
    filled = hyp.impute(data, model='PPCA', random_state=0)
    assert isinstance(filled, pd.DataFrame)
    assert filled.shape == data.shape
    assert not filled.isna().any().any()
    assert np.isfinite(filled.to_numpy()).all()


def main() -> int:
    sine_forecast_smoke()
    low_rank_impute_smoke()
    print('forecasting smoke passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
