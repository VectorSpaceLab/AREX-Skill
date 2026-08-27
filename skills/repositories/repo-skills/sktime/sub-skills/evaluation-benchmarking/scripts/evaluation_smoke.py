#!/usr/bin/env python3
"""Safe CPU smoke checks for sktime evaluation and benchmarking APIs."""
from __future__ import annotations
import argparse, json, math, sys


def run(include_benchmark=True):
    import pandas as pd
    from sktime.forecasting.naive import NaiveForecaster
    from sktime.forecasting.model_evaluation import evaluate
    from sktime.performance_metrics.forecasting import MeanAbsolutePercentageError, mean_absolute_percentage_error
    from sktime.split import SlidingWindowSplitter, ExpandingWindowSplitter, temporal_train_test_split

    y = pd.Series([10., 11., 13., 12., 15., 18., 21., 22., 25., 27., 30., 29.])
    y_train, y_test = temporal_train_test_split(y, test_size=3)
    f = NaiveForecaster(strategy="last").fit(y_train, fh=[1, 2, 3])
    pred = f.predict()
    mape = float(mean_absolute_percentage_error(y_test, pred))
    assert math.isfinite(mape)
    metric = MeanAbsolutePercentageError(symmetric=True)
    cv = SlidingWindowSplitter(fh=[1, 2], window_length=6, step_length=2)
    bt = evaluate(NaiveForecaster(strategy="last"), cv=cv, y=y, scoring=metric, strategy="refit", error_score="raise")
    out = {"status": "passed", "direct_mape": mape, "evaluate_rows": len(bt), "evaluate_columns": list(map(str, bt.columns))}
    if include_benchmark:
        from sktime.benchmarking.forecasting import ForecastingBenchmark
        def loader():
            return pd.Series([2., 2., 3., 4., 5., 7.])
        b = ForecastingBenchmark(backend=None, return_data=False)
        b.add_estimator(NaiveForecaster(strategy="last"), estimator_id="naive-last")
        b.add_task(loader, ExpandingWindowSplitter(initial_window=3, step_length=1, fh=1), [MeanAbsolutePercentageError()], task_id="tiny", error_score="raise", strategy="refit")
        df = b.run(output_file=None)
        assert len(df) == 1
        out["benchmark_rows"] = len(df)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Run tiny CPU-only sktime split/metric/evaluate smoke checks.")
    ap.add_argument("--skip-benchmark", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        out = run(not args.skip_benchmark)
    except Exception as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(out, indent=None if args.json else 2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
