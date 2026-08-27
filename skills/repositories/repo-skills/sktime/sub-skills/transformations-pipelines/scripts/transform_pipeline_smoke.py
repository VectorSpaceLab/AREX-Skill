#!/usr/bin/env python3
"""Offline transformer and pipeline smoke for sktime."""
from __future__ import annotations
import argparse, json, sys

def run(skip_forecast=False):
    import pandas as pd
    import sktime
    from sktime.transformations.series.summarize import SummaryTransformer
    from sktime.transformations.series.difference import Differencer
    y = pd.Series([float(i) for i in range(1, 25)], index=pd.period_range("2020-01", periods=24, freq="M"))
    feats = SummaryTransformer(summary_function=("mean","std","min","max"), quantiles=(0.25,0.5,0.75)).fit_transform(y)
    diff = Differencer(lags=1, na_handling="fill_zero").fit(y); yd = diff.transform(y)
    out = {"status":"passed","sktime_version":sktime.__version__,"summary_shape":list(feats.shape),"differenced_length":len(yd)}
    if not skip_forecast:
        from sktime.forecasting.compose import TransformedTargetForecaster
        from sktime.forecasting.naive import NaiveForecaster
        from sktime.transformations.series.difference import Differencer as D
        pipe = TransformedTargetForecaster([("diff", D(lags=1, na_handling="fill_zero")), ("naive", NaiveForecaster(strategy="last"))])
        pred = pipe.fit(y.iloc[:-3], fh=[1,2,3]).predict(); assert len(pred)==3
        out["forecast_prediction_len"] = len(pred)
    return out

def main(argv=None):
    ap=argparse.ArgumentParser(description="Run offline sktime transformer/pipeline smokes.")
    ap.add_argument("--skip-forecast", action="store_true")
    ap.add_argument("--json", action="store_true")
    args=ap.parse_args(argv)
    try: out=run(args.skip_forecast)
    except Exception as exc:
        print(json.dumps({"status":"failed","error_type":type(exc).__name__,"error":str(exc)}), file=sys.stderr); return 1
    print(json.dumps(out, indent=None if args.json else 2, sort_keys=True)); return 0
if __name__ == "__main__": raise SystemExit(main())
