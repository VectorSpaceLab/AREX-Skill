#!/usr/bin/env python3
"""Check that River imports and a minimal online-learning loop works."""

from __future__ import annotations

import argparse
import importlib
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a safe River environment smoke check.")
    parser.add_argument("--samples", type=int, default=20, help="Number of Phishing samples to use.")
    parser.add_argument(
        "--skip-rust",
        action="store_true",
        help="Skip importing River's Rust extension modules.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    import river
    from river import compose, datasets, linear_model, metrics, preprocessing

    print(f"river_version={river.__version__}")
    modules = [
        "river.base",
        "river.compose",
        "river.datasets",
        "river.evaluate",
        "river.linear_model",
        "river.metrics",
        "river.preprocessing",
        "river.stream",
        "river.tree",
        "river.drift",
    ]
    for module in modules:
        importlib.import_module(module)
        print(f"import_ok={module}")

    if not args.skip_rust:
        for module in ["river._river_rust.stats", "river._river_rust.drift"]:
            importlib.import_module(module)
            print(f"import_ok={module}")

    model = compose.Pipeline(preprocessing.StandardScaler(), linear_model.LogisticRegression())
    metric = metrics.Accuracy()
    seen = 0
    for x, y in datasets.Phishing().take(args.samples):
        y_pred = model.predict_one(x)
        metric.update(y, y_pred)
        model.learn_one(x, y)
        seen += 1

    if seen != args.samples:
        raise RuntimeError(f"expected {args.samples} samples, saw {seen}")
    print(f"quickstart_samples={seen}")
    print(f"quickstart_accuracy={metric.get():.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
