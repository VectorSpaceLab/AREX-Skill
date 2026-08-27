#!/usr/bin/env python3
"""Tiny smoke checks for tslearn forecasting workflows.

The helper adapts the repo forecasting example to deterministic random-walk
inputs with no plotting, downloads, or external data. It verifies that VARIMA
and AutoVARIMA can fit/predict small variable-length datasets and that the
minimum-length guard fails at both fit and predict time.
"""

from __future__ import annotations

import numpy as np

from tslearn.forecasting import AutoVARIMA, VARIMA
from tslearn.generators import random_walks


def _with_real_lengths(data: np.ndarray, lengths: list[int]) -> np.ndarray:
    """Pad trailing positions with NaN so one dense array has variable lengths."""
    if len(lengths) != data.shape[0]:
        raise ValueError("one real length is required per time series")
    data = data.copy()
    for i, length in enumerate(lengths):
        if not 0 <= length <= data.shape[1]:
            raise ValueError(f"invalid length {length} for series {i}")
        data[i, length:, :] = np.nan
    return data


def _expect_value_error(call, expected_substring: str) -> str:
    """Run call and return the ValueError text if it contains the substring."""
    try:
        call()
    except ValueError as exc:
        text = str(exc)
        if expected_substring not in text:
            raise AssertionError(
                f"expected ValueError containing {expected_substring!r}, got {text!r}"
            ) from exc
        return text
    raise AssertionError("expected ValueError but call succeeded")


def smoke_varima_constant_walk() -> None:
    """Fit VARIMA on one tiny variable-length dataset and predict a second one."""
    train = _with_real_lengths(
        random_walks(n_ts=3, sz=5, d=1, std=0.0, random_state=0),
        [4, 3, 2],
    )
    model = VARIMA(1, 0, 0, with_constant=False).fit(train)

    forecast_from_fit_data = model.predict(n=2)
    assert forecast_from_fit_data.shape == (3, 2, 1)
    np.testing.assert_allclose(forecast_from_fit_data, 0.0)

    fresh = _with_real_lengths(
        random_walks(n_ts=2, sz=4, d=1, std=0.0, random_state=1),
        [3, 2],
    )
    forecast_from_fresh_data = model.predict(fresh, n=2)
    assert forecast_from_fresh_data.shape == (2, 2, 1)
    np.testing.assert_allclose(forecast_from_fresh_data, 0.0)

    fit_error = _expect_value_error(
        lambda: VARIMA(1, 0, 0, with_constant=False).fit(
            random_walks(n_ts=2, sz=1, d=1, std=0.0, random_state=2)
        ),
        "timestamps are required per TS",
    )
    predict_error = _expect_value_error(
        lambda: model.predict(random_walks(n_ts=2, sz=1, d=1, std=0.0, random_state=3)),
        "timestamps are required per TS",
    )

    print("VARIMA fitted-data forecast shape:", forecast_from_fit_data.shape)
    print("VARIMA fresh-data forecast shape:", forecast_from_fresh_data.shape)
    print("Expected fit-time error:", fit_error)
    print("Expected predict-time error:", predict_error)


def smoke_auto_varima_low_noise_walk() -> None:
    """Exercise AutoVARIMA on non-constant random walks to avoid degenerate KPSS."""
    train = _with_real_lengths(
        random_walks(n_ts=3, sz=8, d=1, std=0.1, random_state=4),
        [7, 6, 5],
    )
    fresh = _with_real_lengths(
        random_walks(n_ts=2, sz=7, d=1, std=0.1, random_state=5),
        [6, 4],
    )

    model = AutoVARIMA(
        max_p=1,
        max_q=1,
        max_d=1,
        default_d_for_non_stationarity=0,
    ).fit(train)

    forecast_from_fit_data = model.predict(n=2)
    forecast_from_fresh_data = model.predict(fresh, n=2)
    assert forecast_from_fit_data.shape == (3, 2, 1)
    assert forecast_from_fresh_data.shape == (2, 2, 1)

    print("AutoVARIMA selected:", model.best_estimator_)
    print("AutoVARIMA fitted-data forecast shape:", forecast_from_fit_data.shape)
    print("AutoVARIMA fresh-data forecast shape:", forecast_from_fresh_data.shape)


def main() -> int:
    smoke_varima_constant_walk()
    smoke_auto_varima_low_noise_walk()
    print("forecasting smoke checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
