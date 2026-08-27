#!/usr/bin/env python3
"""Run a bounded, offline pmdarima dataset and diagnostics smoke check.

The default path uses one package-local dataset and tiny deterministic arrays.
It performs no network access, model fitting, plotting, or file writes. Pass
``--plot`` only to exercise the optional Matplotlib APIs headlessly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Callable, Type


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Check installed pmdarima dataset, validation, differencing, "
            "decomposition, and numeric diagnostic contracts."
        )
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help=(
            "also exercise plot_acf, plot_pacf, tsdisplay, and "
            "decomposed_plot with a headless backend"
        ),
    )
    return parser


def _import_pmdarima():
    # pmdarima chooses a compatible pyplot handle while importing. Select a
    # non-interactive backend first even though plotting is opt-in.
    os.environ.setdefault("MPLBACKEND", "Agg")
    try:
        import pmdarima as pm
    except ImportError as exc:
        detail = str(exc)
        if "__check_build" in detail or "_arima" in detail or "_array" in detail:
            raise RuntimeError(
                "pmdarima compiled extensions could not import. Run this "
                "script with a successfully built installed distribution; "
                "do not add a source checkout to PYTHONPATH."
            ) from exc
        raise RuntimeError(
            "pmdarima could not import. Verify the installed package and its "
            "dependency environment before running diagnostics."
        ) from exc
    return pm


def _expect_error(
    label: str,
    function: Callable[[], object],
    expected: Type[BaseException],
) -> str:
    try:
        function()
    except expected as exc:
        return type(exc).__name__
    except Exception as exc:  # pragma: no cover - diagnostic message path
        raise AssertionError(
            f"{label} raised {type(exc).__name__}, expected {expected.__name__}"
        ) from exc
    raise AssertionError(f"{label} did not raise {expected.__name__}")


def _run(plot: bool) -> dict:
    import numpy as np

    pm = _import_pmdarima()
    from pmdarima.arima import decompose, ndiffs, nsdiffs
    from pmdarima.utils import (
        acf,
        as_series,
        c,
        check_endog,
        check_exog,
        diff,
        diff_inv,
        pacf,
    )

    # AirPassengers is in-memory/package-local and deterministic. In
    # particular, this script never calls the network-backed gasoline loader.
    raw = pm.datasets.load_airpassengers(as_series=False)
    series = pm.datasets.load_airpassengers(as_series=True)
    assert isinstance(raw, np.ndarray)
    assert raw.shape == (144,) and raw.dtype.kind == "f"
    assert np.isfinite(raw).all()
    assert series.shape == (144,) and series.dtype.kind == "f"
    assert type(series).__name__ == "Series"

    y = check_endog(
        series,
        dtype=np.float64,
        copy=True,
        force_all_finite=True,
        preserve_series=True,
    )
    assert type(y).__name__ == "Series"
    assert y.shape == (144,) and int(y.isna().sum()) == 0
    assert y.index.equals(series.index)

    nan_error = _expect_error(
        "non-finite endogenous input",
        lambda: check_endog(
            [1.0, np.nan, 2.0],
            force_all_finite=True,
            preserve_series=False,
        ),
        ValueError,
    )
    _expect_error(
        "non-finite stationarity input",
        lambda: ndiffs([1.0, np.nan, 2.0], max_d=1),
        ValueError,
    )

    # Tiny deterministic signal: eight complete periods at m=4.
    tiny = np.tile(np.array([10.0, 12.0, 9.0, 11.0]), 8)
    tiny += np.arange(tiny.size, dtype=float) * 0.1
    assert tiny.shape == (32,) and np.isfinite(tiny).all()

    # Constant input gives deterministic bounded differencing recommendations.
    constant = np.ones(32, dtype=float)
    d = ndiffs(constant, alpha=0.05, test="kpss", max_d=1)
    seasonal_d = nsdiffs(constant, m=4, max_D=1, test="ocsb")
    assert d == 0 and seasonal_d == 0

    seasonal_diff = diff(tiny, lag=4, differences=1)
    assert seasonal_diff.shape == (28,)
    assert np.allclose(seasonal_diff, np.full(28, 0.4))
    assert diff(tiny[:3], lag=5, differences=1).shape == (0,)

    # diff_inv is zero-initialized in this release. A zero-origin ramp is a
    # safe roundtrip; a nonzero-origin series must not be called lossless.
    ramp = np.arange(8, dtype=float)
    assert np.array_equal(diff_inv(diff(ramp)), ramp)
    assert not np.array_equal(diff_inv(diff(tiny)), tiny)

    matrix = np.arange(12, dtype=float).reshape(6, 2)
    matrix_diff = diff(matrix, lag=1, differences=1)
    assert matrix_diff.shape == (5, 2)
    assert np.array_equal(matrix_diff, np.full((5, 2), 2.0))

    # Public array conveniences and exogenous validation.
    assert np.array_equal(c(1, [2, 3]), np.array([1, 2, 3]))
    assert c() is None
    assert as_series([1, 2, 3]).shape == (3,)
    assert check_exog([[1.0], [2.0]]).shape == (2, 1)
    _expect_error(
        "one-dimensional exogenous input",
        lambda: check_exog([1.0, 2.0]),
        ValueError,
    )

    # m is a calendar contract. These checks validate bad-frequency and short
    # inputs without trying to infer a period from the array length.
    _expect_error(
        "m <= 1 for nsdiffs",
        lambda: nsdiffs(constant, m=1, max_D=1),
        ValueError,
    )
    _expect_error(
        "non-integer decomposition m",
        lambda: decompose(tiny, "additive", 4.0),
        ValueError,
    )
    short_error = _expect_error(
        "fewer than two decomposition periods",
        lambda: decompose(np.ones(7), "additive", 4),
        ValueError,
    )
    _expect_error(
        "invalid decomposition type",
        lambda: decompose(tiny, "unknown", 4),
        ValueError,
    )
    _expect_error(
        "invalid differencing lag",
        lambda: diff(tiny, lag=0),
        ValueError,
    )

    parts = decompose(tiny, "additive", 4)
    components = {
        name: np.asarray(getattr(parts, name), dtype=float)
        for name in ("x", "trend", "seasonal", "random")
    }
    assert all(value.shape == tiny.shape for value in components.values())
    assert np.isnan(components["trend"]).any()
    finite = np.isfinite(components["trend"]) & np.isfinite(components["random"])
    reconstructed = (
        components["trend"] + components["seasonal"] + components["random"]
    )
    assert finite.any() and np.allclose(components["x"][finite], reconstructed[finite])

    acf_values = np.asarray(
        acf(tiny, nlags=6, fft=False, missing="none", adjusted=False),
        dtype=float,
    )
    pacf_values = np.asarray(
        pacf(tiny, nlags=6, method="ywadjusted"),
        dtype=float,
    )
    assert acf_values.shape == (7,) and np.isclose(acf_values[0], 1.0)
    assert pacf_values.shape == (7,) and np.isclose(pacf_values[0], 1.0)
    assert np.isfinite(acf_values).all() and np.isfinite(pacf_values).all()

    plot_status = "not-requested"
    if plot:
        try:
            import matplotlib.pyplot as plt
            from pmdarima.utils import (
                decomposed_plot,
                plot_acf,
                plot_pacf,
                tsdisplay,
            )
        except ImportError as exc:
            raise RuntimeError(
                "--plot requested but Matplotlib is unavailable; numeric "
                "diagnostics passed independently of this optional dependency."
            ) from exc

        try:
            assert plot_acf(tiny, lags=6, show=False) is not None
            assert plot_pacf(tiny, lags=6, method="yw", show=False) is not None
            assert tsdisplay(tiny, lag_max=6, show=False) is not None
            # v2.1.1 forwards figure_kwargs with ``**`` and therefore needs
            # an explicit empty mapping; omitting it is a source-level bug.
            assert decomposed_plot(parts, figure_kwargs={}, show=False) is not None
            _expect_error(
                "tsdisplay lag_max >= series length",
                lambda: tsdisplay(tiny[:6], lag_max=6, show=False),
                ValueError,
            )
            plot_status = "headless-passed"
        finally:
            plt.close("all")
        assert not plt.get_fignums()

    return {
        "package": "pmdarima",
        "package_file": str(Path(pm.__file__).resolve()),
        "package_version": str(getattr(pm, "__version__", "unknown")),
        "loader": "load_airpassengers",
        "raw_type": type(raw).__name__,
        "raw_shape": list(raw.shape),
        "series_type": type(series).__name__,
        "series_shape": list(series.shape),
        "series_missing": int(series.isna().sum()),
        "m": 12,
        "tiny_m": 4,
        "d": int(d),
        "D": int(seasonal_d),
        "seasonal_diff_length": int(seasonal_diff.size),
        "acf_length": int(acf_values.size),
        "pacf_length": int(pacf_values.size),
        "nan_error": nan_error,
        "short_error": short_error,
        "plot": plot_status,
    }


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = _run(plot=args.plot)
    except (AssertionError, RuntimeError, ValueError) as exc:
        detail = str(exc) or type(exc).__name__
        print(f"datasets-diagnostics check failed: {detail}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
