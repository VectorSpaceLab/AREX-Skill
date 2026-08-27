#!/usr/bin/env python3
"""Tiny statsmodels linear/formula smoke check with no network access."""
from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


def main() -> int:
    parser = argparse.ArgumentParser(description="Run OLS/GLM/robust-covariance smoke checks.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = parser.parse_args()
    df = pd.DataFrame({
        "y": [1.1, 1.9, 3.2, 4.1, 5.2, 5.9, 7.1, 8.0],
        "x": list(range(8)),
        "group": ["a", "a", "b", "b", "a", "b", "a", "b"],
    })
    ols = smf.ols("y ~ x + C(group)", data=df, missing="raise").fit()
    hc3 = ols.get_robustcov_results(cov_type="HC3")
    exog = sm.add_constant(df[["x"]])
    glm = sm.GLM(df["y"], exog, family=sm.families.Gaussian(), missing="raise").fit()
    ok = bool(np.isfinite(ols.params).all() and np.isfinite(hc3.bse).all() and np.isfinite(glm.params).all())
    report = {
        "ok": ok,
        "ols_params": {str(k): float(v) for k, v in ols.params.items()},
        "hc3_bse_finite": bool(np.isfinite(hc3.bse).all()),
        "glm_params": [float(v) for v in glm.params],
        "exog_names": list(ols.model.exog_names),
    }
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
