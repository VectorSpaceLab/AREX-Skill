#!/usr/bin/env python3
"""CPU-safe forecasting smoke test for sktime."""
from __future__ import annotations
import argparse, json, math, sys

def run(strategy: str = "last", seasonal_period: int = 12, test_size: int = 12):
    import numpy as np
    import sktime
    from sktime.datasets import load_airline
    from sktime.forecasting.base import ForecastingHorizon
    from sktime.forecasting.model_evaluation import evaluate
    from sktime.forecasting.naive import NaiveForecaster
    from sktime.performance_metrics.forecasting import mean_absolute_percentage_error
    from sktime.split import ExpandingWindowSplitter, temporal_train_test_split
    y = load_airline(); y_train, y_test = temporal_train_test_split(y, test_size=test_size)
    fh = ForecastingHorizon(y_test.index, is_relative=False)
    model = NaiveForecaster(strategy=strategy, sp=seasonal_period).fit(y_train)
    y_pred = model.predict(fh=fh)
    assert len(y_pred) == len(y_test) and y_pred.index.equals(y_test.index)
    mape = float(mean_absolute_percentage_error(y_test, y_pred)); assert math.isfinite(mape)
    cv = ExpandingWindowSplitter(initial_window=24, step_length=12, fh=[1, 2, 3])
    backtest = evaluate(NaiveForecaster(strategy=strategy, sp=seasonal_period), cv=cv, y=y.iloc[:72], strategy="refit", error_score="raise")
    score_cols = [str(c) for c in backtest.columns if str(c).startswith("test_")]
    assert score_cols
    return {"status":"passed","sktime_version":sktime.__version__,"strategy":strategy,"n_train":len(y_train),"n_test":len(y_test),"mape":mape,"prediction_index_start":str(y_pred.index[0]),"prediction_index_end":str(y_pred.index[-1]),"backtest_rows":len(backtest),"backtest_score_columns":score_cols}

def main(argv=None):
    ap=argparse.ArgumentParser(description="Run a no-download sktime forecasting smoke test on airline data.")
    ap.add_argument("--seasonal-period", type=int, default=12)
    ap.add_argument("--strategy", choices=["last","mean","drift"], default="last")
    ap.add_argument("--test-size", type=int, default=12)
    ap.add_argument("--json", action="store_true")
    args=ap.parse_args(argv)
    try: out=run(args.strategy,args.seasonal_period,args.test_size)
    except Exception as exc:
        print(json.dumps({"status":"failed","error_type":type(exc).__name__,"error":str(exc)}), file=sys.stderr); return 1
    print(json.dumps(out, indent=None if args.json else 2, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
