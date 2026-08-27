#!/usr/bin/env python3
"""Run a safe MDSS bias-scan smoke check with tiny synthetic data."""
from __future__ import annotations

import argparse
import json
import logging
from contextlib import contextmanager


@contextmanager
def quiet_optional_warnings(enabled: bool = True):
    if not enabled:
        yield
        return
    logging.disable(logging.WARNING)
    try:
        yield
    finally:
        logging.disable(logging.NOTSET)


def run_scan(show_import_warnings: bool = False) -> dict:
    import pandas as pd

    with quiet_optional_warnings(not show_import_warnings):
        from aif360.sklearn.detectors import bias_scan

    X = pd.DataFrame(
        {
            "region": ["north", "north", "south", "south", "south", "north"],
            "channel": ["web", "store", "web", "store", "web", "store"],
        }
    )
    y_true = pd.Series([1, 1, 1, 0, 0, 1], name="actual")
    expectations = pd.Series([0.9, 0.8, 0.2, 0.5, 0.2, 0.8], name="expected")
    subset, score = bias_scan(
        X,
        y_true,
        expectations,
        pos_label=1,
        overpredicted=False,
        scoring="Bernoulli",
        num_iters=5,
        penalty=1e-17,
        mode="binary",
    )
    return {
        "status": "ok",
        "subset": {key: sorted(list(value)) for key, value in subset.items()},
        "score": round(float(score), 6),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a deterministic AIF360 MDSS bias scan smoke check.")
    parser.add_argument("--json", action="store_true", help="Emit JSON output instead of key=value lines.")
    parser.add_argument("--show-import-warnings", action="store_true", help="Show optional FACTS import warnings.")
    args = parser.parse_args()
    result = run_scan(show_import_warnings=args.show_import_warnings)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print(f"subset: {result['subset']}")
        print(f"score: {result['score']}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
