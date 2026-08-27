#!/usr/bin/env python3
"""Run a focused sktime check_estimator smoke or print its signature."""
from __future__ import annotations
import argparse, importlib, inspect, json, sys
from importlib import metadata

BUILTINS = {
    "naive-forecaster": "sktime.forecasting.naive:NaiveForecaster",
    "exponent-transformer": "sktime.transformations.exponent:ExponentTransformer",
    "dummy-classifier": "sktime.classification.dummy:DummyClassifier",
    "dummy-regressor": "sktime.regression.dummy:DummyRegressor",
}


def import_object(spec):
    modname, objname = spec.split(":", 1) if ":" in spec else spec.rsplit(".", 1)
    obj = importlib.import_module(modname)
    for part in objname.split("."):
        obj = getattr(obj, part)
    return obj


def parse(v):
    if not v:
        return None
    parts = [p.strip() for p in v.split(",") if p.strip()]
    return parts[0] if len(parts) == 1 else parts


def sktime_version():
    try:
        return metadata.version("sktime")
    except Exception:
        return "unknown"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Print check_estimator signature or run a focused estimator smoke.")
    ap.add_argument("--signature", action="store_true")
    ap.add_argument("--list-builtins", action="store_true")
    ap.add_argument("--builtin", choices=sorted(BUILTINS), default="naive-forecaster")
    ap.add_argument("--estimator")
    ap.add_argument("--tests-to-run", default="test_constructor")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    if args.list_builtins:
        print("\n".join(f"{k}: {v}" for k, v in sorted(BUILTINS.items())))
        return 0
    try:
        from sktime.utils.estimator_checks import check_estimator
    except Exception as exc:
        print(json.dumps({"status": "failed", "sktime_version": sktime_version(), "error_type": type(exc).__name__, "error": str(exc)}))
        return 2
    if args.signature:
        print(json.dumps({"sktime_version": sktime_version(), "check_estimator_signature": f"check_estimator{inspect.signature(check_estimator)}"}))
        return 0
    try:
        est = import_object(args.estimator or BUILTINS[args.builtin])
        res = check_estimator(est, tests_to_run=parse(args.tests_to_run), verbose=False)
        failed = {k: str(v) for k, v in res.items() if v != "PASSED"}
        out = {"total": len(res), "passed": len(res) - len(failed), "failed": failed}
        print(json.dumps(out, indent=None if args.json else 2, sort_keys=True))
        return 1 if failed else 0
    except Exception as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__, "error": str(exc)}))
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
