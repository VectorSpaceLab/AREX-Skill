#!/usr/bin/env python3
"""No-cluster StatsForecast distributed execution smoke test.

Compares explicit MultiprocessBackend output against normal StatsForecast output
on a tiny synthetic pandas panel. This script does not start Dask, Ray, Spark,
or any external scheduler.
"""

from __future__ import annotations

import argparse
import sys
from importlib.metadata import PackageNotFoundError, version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare local MultiprocessBackend forecasts and cross-validation "
            "against normal StatsForecast output on synthetic data."
        )
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        choices=(1, 2),
        default=1,
        help="Local MultiprocessBackend jobs to use. Keep this at 1 or 2 for a safe smoke test.",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=2,
        help="Forecast horizon for forecast and cross-validation checks. Default: 2.",
    )
    parser.add_argument(
        "--n-series",
        type=int,
        default=3,
        help="Number of synthetic string-id series. Default: 3.",
    )
    parser.add_argument(
        "--length",
        type=int,
        default=12,
        help="Observations per series. Must exceed horizon. Default: 12.",
    )
    return parser.parse_args()


def require_positive(name: str, value: int) -> None:
    if value <= 0:
        raise SystemExit(f"{name} must be positive; got {value}")


def make_panel(n_series: int, length: int):
    import pandas as pd

    dates = pd.date_range("2024-01-01", periods=length, freq="D")
    rows = []
    for series_idx in range(n_series):
        base = 10.0 * (series_idx + 1)
        for t, ds in enumerate(dates):
            rows.append(
                {
                    "unique_id": f"series_{series_idx}",
                    "ds": ds,
                    "y": base + float(t) + (0.25 if t % 2 else 0.0),
                }
            )
    return pd.DataFrame(rows)


def sort_forecast(df):
    return df.sort_values(["unique_id", "ds"]).reset_index(drop=True)


def sort_cv(df):
    return df.sort_values(["unique_id", "cutoff", "ds"]).reset_index(drop=True)


def main() -> int:
    args = parse_args()
    require_positive("--horizon", args.horizon)
    require_positive("--n-series", args.n_series)
    require_positive("--length", args.length)
    if args.length <= args.horizon:
        raise SystemExit("--length must be greater than --horizon")

    try:
        import pandas as pd
        from statsforecast import StatsForecast
        from statsforecast.distributed.multiprocess import MultiprocessBackend
        from statsforecast.models import Naive
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(
            "ERROR: failed to import pandas/statsforecast requirements: " f"{exc}",
            file=sys.stderr,
        )
        return 2

    panel = make_panel(n_series=args.n_series, length=args.length)

    normal_forecast = StatsForecast(models=[Naive()], freq="D", n_jobs=1).forecast(
        df=panel,
        h=args.horizon,
    )
    backend_forecast = MultiprocessBackend(n_jobs=args.n_jobs).forecast(
        df=panel,
        models=[Naive()],
        freq="D",
        h=args.horizon,
    )
    pd.testing.assert_frame_equal(
        sort_forecast(backend_forecast),
        sort_forecast(normal_forecast),
        check_exact=True,
    )

    normal_cv = StatsForecast(models=[Naive()], freq="D", n_jobs=1).cross_validation(
        df=panel,
        h=args.horizon,
        n_windows=1,
    )
    backend_cv = MultiprocessBackend(n_jobs=args.n_jobs).cross_validation(
        df=panel,
        models=[Naive()],
        freq="D",
        h=args.horizon,
        n_windows=1,
    )
    pd.testing.assert_frame_equal(
        sort_cv(backend_cv),
        sort_cv(normal_cv),
        check_exact=True,
    )

    try:
        dist_version = version("statsforecast")
    except PackageNotFoundError:
        dist_version = "unknown"

    print(
        "distributed smoke success: "
        f"statsforecast={dist_version}, n_jobs={args.n_jobs}, "
        f"series={args.n_series}, length={args.length}, horizon={args.horizon}, "
        f"forecast_rows={len(backend_forecast)}, cv_rows={len(backend_cv)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
