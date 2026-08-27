#!/usr/bin/env python3
"""Check a statsmodels environment without network or source checkout assumptions."""
from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from typing import Any


def _optional_import(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # pragma: no cover - diagnostic script
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"available": True, "version": getattr(module, "__version__", "unknown")}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify statsmodels imports and a tiny model fit.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args()

    report: dict[str, Any] = {"python": sys.version.split()[0], "ok": False, "checks": {}}
    try:
        import numpy as np
        import pandas as pd
        import statsmodels
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
        import statsmodels.tsa.api as tsa
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        print(json.dumps(report, indent=2) if args.json else report["error"])
        return 1

    report["statsmodels_version"] = getattr(statsmodels, "__version__", "unknown")
    report["checks"]["api_objects"] = all(hasattr(sm, name) for name in ["OLS", "GLM", "Logit", "Poisson", "datasets", "stats", "tsa"])
    report["checks"]["formula_objects"] = all(hasattr(smf, name) for name in ["ols", "glm", "logit", "poisson"])
    report["checks"]["tsa_objects"] = all(hasattr(tsa, name) for name in ["ARIMA", "SARIMAX", "acf", "adfuller"])
    report["optional"] = {"matplotlib": _optional_import("matplotlib"), "pytest": _optional_import("pytest")}

    df = pd.DataFrame({"y": [1.0, 2.1, 2.9, 4.2, 5.1, 5.9], "x": [0, 1, 2, 3, 4, 5]})
    res = smf.ols("y ~ x", data=df).fit()
    finite = np.isfinite(res.params).all() and np.isfinite(res.bse).all()
    report["checks"]["tiny_ols_fit"] = bool(finite and math.isfinite(float(res.rsquared)))
    report["ols_params"] = {str(k): float(v) for k, v in res.params.items()}
    report["ok"] = bool(all(report["checks"].values()))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"statsmodels {report['statsmodels_version']} on Python {report['python']}")
        for key, value in report["checks"].items():
            print(f"{key}: {'PASS' if value else 'FAIL'}")
        for key, value in report["optional"].items():
            status = "available" if value["available"] else f"missing ({value['error']})"
            print(f"optional {key}: {status}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
