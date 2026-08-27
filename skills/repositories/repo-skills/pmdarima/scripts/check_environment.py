#!/usr/bin/env python3
"""Run a safe, offline pmdarima installation and API smoke check.

The checker is runnable from any working directory. It does not download data,
open plots, deserialize artifacts, or mutate files. It exits non-zero when the
core import or tiny numerical contracts fail.
"""

from __future__ import annotations

import argparse
import importlib
from importlib.metadata import PackageNotFoundError, version
import json
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check pmdarima imports, metadata, and tiny CPU API contracts."
    )
    parser.add_argument(
        "--json", action="store_true", help="emit the result as JSON instead of text"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result: dict[str, object] = {
        "python": sys.version.split()[0],
        "distribution": None,
        "import": None,
        "checks": {},
        "errors": [],
    }
    try:
        result["distribution"] = version("pmdarima")
    except PackageNotFoundError as exc:
        result["errors"].append(f"distribution metadata missing: {exc}")
    try:
        import numpy as np
        import pmdarima as pm

        result["import"] = {"version": pm.__version__, "module": pm.__file__}
        from pmdarima.datasets import load_wineind
        from pmdarima.metrics import smape
        from pmdarima.model_selection import RollingForecastCV

        y = np.arange(1.0, 13.0)
        model = pm.ARIMA(order=(1, 0, 0), suppress_warnings=True).fit(y)
        forecast = model.predict(n_periods=2)
        dataset = load_wineind()
        fold = next(RollingForecastCV(h=2, initial=5, step=2).split(y))
        checks = {
            "arima_forecast_shape": list(forecast.shape),
            "dataset_length": int(len(dataset)),
            "cv_train_length": int(len(fold[0])),
            "cv_test_length": int(len(fold[1])),
            "smape_identical": float(smape(y[:2], y[:2])) == 0.0,
        }
        result["checks"] = checks
        if tuple(forecast.shape) != (2,):
            raise AssertionError(f"expected forecast shape (2,), got {forecast.shape}")
        if len(dataset) == 0 or len(fold[0]) != 5 or len(fold[1]) != 2:
            raise AssertionError("dataset or temporal split contract failed")
        if float(smape(y[:2], y[:2])) != 0.0:
            raise AssertionError("smape identical-series contract failed")
    except Exception as exc:  # noqa: BLE001 - diagnostic boundary
        result["errors"].append(f"API smoke failed: {type(exc).__name__}: {exc}")

    if args.json:
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"pmdarima metadata: {result['distribution']}")
        print(f"pmdarima import: {result['import']}")
        print(f"checks: {json.dumps(result['checks'], sort_keys=True)}")
        for error in result["errors"]:
            print(f"ERROR: {error}", file=sys.stderr)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
