#!/usr/bin/env python3
"""Tiny statsmodels datasets/results/graphics smoke check."""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm


def main() -> int:
    parser = argparse.ArgumentParser(description="Run dataset/result/prediction/plot smoke checks.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for the temporary plot output.")
    args = parser.parse_args()
    data = sm.datasets.longley.load_pandas().data
    y = data["TOTEMP"]
    X = sm.add_constant(data[["GNP", "POP"]])
    res = sm.OLS(y, X, missing="raise").fit()
    pred = res.get_prediction(X.iloc[:2]).summary_frame()
    coef = pd.DataFrame({"coef": res.params, "std_err": res.bse, "pvalue": res.pvalues})
    out_dir = args.output_dir or Path(tempfile.mkdtemp(prefix="statsmodels-graphics-"))
    out_dir.mkdir(parents=True, exist_ok=True)
    fig = sm.graphics.qqplot(res.resid, line="45")
    plot_path = out_dir / "qqplot.png"
    fig.savefig(plot_path, dpi=80, bbox_inches="tight")
    plt.close(fig)
    ok = bool(np.isfinite(coef.to_numpy()).all() and pred.shape[0] == 2 and plot_path.exists() and plot_path.stat().st_size > 0)
    report = {"ok": ok, "coef_rows": int(coef.shape[0]), "prediction_rows": int(pred.shape[0]), "plot_written": str(plot_path)}
    print(json.dumps(report, indent=2, sort_keys=True) if args.json else report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
