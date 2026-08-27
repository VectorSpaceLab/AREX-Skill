#!/usr/bin/env python3
"""Tiny statsmodels statistical diagnostics smoke check."""
from __future__ import annotations

import argparse
import json
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.outliers_influence import OLSInfluence


def main() -> int:
    parser = argparse.ArgumentParser(description="Run residual diagnostics and multiple-testing smoke checks.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    x = np.arange(1, 13, dtype=float)
    y = 1.0 + 0.8 * x + np.array([0.1, -0.2, 0.1, 0.2, -0.1, 0.3, -0.2, 0.1, 0.0, 0.2, -0.1, 0.1])
    X = sm.add_constant(x)
    res = sm.OLS(y, X).fit()
    bp = het_breuschpagan(res.resid, res.model.exog)
    infl = OLSInfluence(res)
    reject, p_adj, _, _ = multipletests([0.001, 0.02, 0.20], method="fdr_bh")
    ok = bool(np.isfinite(bp).all() and np.isfinite(infl.hat_matrix_diag).all() and len(p_adj) == 3)
    report = {"ok": ok, "bp_pvalue": float(bp[1]), "max_leverage": float(infl.hat_matrix_diag.max()), "adjusted_pvalues": [float(v) for v in p_adj], "reject": [bool(v) for v in reject]}
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
