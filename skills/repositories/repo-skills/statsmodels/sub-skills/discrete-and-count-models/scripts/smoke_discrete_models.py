#!/usr/bin/env python3
"""Tiny statsmodels discrete/count smoke check."""
from __future__ import annotations

import argparse
import json
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Logit and Poisson smoke checks on deterministic data.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    df = pd.DataFrame({
        "x": [-3, -2, -1, -0.5, 0.5, 1, 2, 3, 4, -4, 1.5, -1.5],
        "y": [0, 0, 1, 0, 1, 0, 1, 1, 1, 0, 0, 1],
        "count": [0, 0, 1, 1, 2, 2, 3, 4, 5, 0, 3, 1],
    })
    logit = smf.logit("y ~ x", data=df).fit(disp=False, maxiter=100)
    exog = sm.add_constant(df[["x"]])
    pois = sm.Poisson(df["count"], exog, missing="raise").fit(disp=False, maxiter=100)
    pred = logit.predict(pd.DataFrame({"x": [0.0, 2.0]}))
    ok = bool(np.isfinite(logit.params).all() and np.isfinite(pois.params).all() and pred.iloc[1] > pred.iloc[0])
    report = {
        "ok": ok,
        "logit_params": {str(k): float(v) for k, v in logit.params.items()},
        "poisson_params": [float(v) for v in pois.params],
        "probability_increases": bool(pred.iloc[1] > pred.iloc[0]),
    }
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
