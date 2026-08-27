#!/usr/bin/env python3
"""List sktime extension template mappings or write a tiny stub."""
from __future__ import annotations
import argparse

MAP = {
    "forecaster": ("sktime.forecasting.base", "BaseForecaster", "_fit(self, y, X=None, fh=None)", "_predict(self, fh=None, X=None)"),
    "transformer": ("sktime.transformations.base", "BaseTransformer", "_fit(self, X, y=None)", "_transform(self, X, y=None)"),
    "classifier": ("sktime.classification.base", "BaseClassifier", "_fit(self, X, y)", "_predict(self, X)"),
    "regressor": ("sktime.regression.base", "BaseRegressor", "_fit(self, X, y)", "_predict(self, X)"),
    "clusterer": ("sktime.clustering", "BaseClusterer", "_fit(self, X)", "_predict(self, X)"),
    "detector": ("sktime.detection.base", "BaseDetector", "_fit(self, X, y=None)", "_predict(self, X)"),
}


def stub(kind, cls):
    mod, base, m1, m2 = MAP[kind]
    return (
        f"from {mod} import {base}\n\n"
        f"class {cls}({base}):\n"
        "    _tags = {\"authors\": [\"your-github-handle\"], \"maintainers\": [\"your-github-handle\"]}\n"
        "    def __init__(self):\n"
        "        super().__init__()\n"
        f"    def {m1}:\n"
        "        raise NotImplementedError\n"
        f"    def {m2}:\n"
        "        raise NotImplementedError\n"
        "    @classmethod\n"
        "    def get_test_params(cls, parameter_set=\"default\"):\n"
        "        return {}\n"
    )


def main(argv=None):
    ap = argparse.ArgumentParser(description="List sktime template mappings or write a small stub.")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--scitype", choices=sorted(MAP))
    ap.add_argument("--class-name", default="MyEstimator")
    ap.add_argument("--output")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if args.list or not args.scitype:
        print("\n".join(f"{k}: {v[1]} hooks {v[2]}, {v[3]}" for k, v in sorted(MAP.items())))
        return 0
    s = stub(args.scitype, args.class_name)
    if args.dry_run or not args.output:
        print(s)
        return 0
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(s)
    print(args.output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
