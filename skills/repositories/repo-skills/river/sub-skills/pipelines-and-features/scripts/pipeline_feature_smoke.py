#!/usr/bin/env python3
"""Run small River pipeline and feature-engineering smoke checks."""

from __future__ import annotations

import argparse
import datetime as dt
import numbers
import sys
from pathlib import Path

repo_root = str(Path(__file__).resolve().parents[6])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from river import compose, feature_extraction, linear_model, preprocessing, stats, utils


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def prefixed(prefix: str):
    def _prefix(x: dict) -> dict:
        return {f"{prefix}{k}": v for k, v in x.items()}

    _prefix.__name__ = f"{prefix.rstrip('_')}_prefix"
    return _prefix


class RecordingLinearRegression(linear_model.LinearRegression):
    def learn_one(self, x, y, w=1.0):
        self.last_weight = w
        return super().learn_one(x, y, w=w)


def build_mixed_model() -> compose.Pipeline:
    numeric = compose.SelectType(numbers.Number) | preprocessing.StandardScaler()
    tfidf = feature_extraction.TFIDF(on="text") | compose.FuncTransformer(prefixed("tfidf_"))
    bow = feature_extraction.BagOfWords(on="text") | compose.FuncTransformer(prefixed("count_"))
    text = compose.Select("text") | (tfidf + bow)
    features = compose.TransformerUnion(("numeric", numeric), ("text", text))
    return compose.Pipeline(("features", features), ("model", linear_model.LogisticRegression()))


def smoke_mixed_features(show_types: bool, n_decimals: int, debug: bool) -> None:
    rows = [
        ({"text": "fast blue bike", "speed": 3.0, "weight": 4.0}, True),
        ({"text": "slow red bike", "speed": 1.5, "weight": 2.0}, False),
        ({"text": "fast green bike", "speed": 2.5, "weight": 3.0}, True),
    ]

    product = compose.Select("speed") * compose.Select("weight")
    product_out = product.transform_one(rows[0][0])
    check(
        abs(product_out["speed*weight"] - 12.0) < 1e-9,
        "TransformerProduct did not create the expected interaction",
    )

    grouped = preprocessing.StatImputer(("temperature", stats.Mean())) * "weather"
    grouped.learn_one({"weather": "sunny", "temperature": 8})
    grouped.learn_one({"weather": "sunny", "temperature": None})
    grouped.learn_one({"weather": "rainy", "temperature": 4})
    sunny = grouped.transform_one({"weather": "sunny", "temperature": None})
    check(
        abs(float(sunny["temperature"]) - 8.0) < 1e-9,
        "Grouper did not keep a separate per-group state",
    )

    model = build_mixed_model()
    for x, y in rows:
        model.learn_one(x, y)

    features = model["features"].transform_one(rows[-1][0])
    check("speed" in features and "weight" in features, "numeric features went missing")
    check(any(k.startswith("tfidf_") for k in features), "TFIDF features went missing")
    check(any(k.startswith("count_") for k in features), "Bag-of-words features went missing")

    pred = model.predict_one(rows[-1][0])
    check(pred in {True, False}, "classifier did not produce a label")

    if debug:
        print(model.debug_one(rows[-1][0], show_types=show_types, n_decimals=n_decimals))


def build_agg_model() -> compose.Pipeline:
    agg = feature_extraction.Agg(
        on="value",
        by="group",
        how=utils.TimeRolling(stats.Mean, period=dt.timedelta(days=7)),
    )
    return compose.Pipeline(("agg", agg), ("scale", preprocessing.StandardScaler()), ("reg", RecordingLinearRegression()))


def build_target_model() -> compose.Pipeline:
    target = feature_extraction.TargetAgg(
        by="group",
        how=utils.TimeRolling(stats.Mean, period=dt.timedelta(days=7)),
    )
    return compose.Pipeline(
        ("target", target),
        ("scale", preprocessing.StandardScaler()),
        ("reg", RecordingLinearRegression()),
    )


def smoke_timestamp_routing(show_types: bool, n_decimals: int, debug: bool) -> None:
    rows = [
        ({"group": "a", "value": 10.0}, 10.0, dt.datetime(2024, 1, 1)),
        ({"group": "a", "value": 20.0}, 20.0, dt.datetime(2024, 1, 2)),
    ]

    agg_model = build_agg_model()
    with compose.learn_during_predict():
        for x, y, t in rows:
            agg_model.predict_one(x, t=t)
            agg_model.learn_one(x, y, t=t, w=2.0)

    check(
        abs(agg_model["agg"]._groups[("a",)].get() - 15.0) < 1e-9,
        "Agg did not receive the timestamp route",
    )
    check(
        getattr(agg_model["reg"], "last_weight", None) == 2.0,
        "final estimator did not receive the sample weight",
    )

    target_model = build_target_model()
    for x, y, t in rows:
        target_model.learn_one(x, y, t=t, w=3.0)

    check(
        abs(target_model["target"]._groups[("a",)].get() - 15.0) < 1e-9,
        "TargetAgg did not receive the timestamp route",
    )
    check(
        getattr(target_model["reg"], "last_weight", None) == 3.0,
        "target pipeline did not forward the sample weight",
    )

    if debug:
        print(agg_model.debug_one(rows[-1][0], show_types=show_types, n_decimals=n_decimals))
        print(target_model.debug_one(rows[-1][0], show_types=show_types, n_decimals=n_decimals))


def smoke_batch() -> None:
    try:
        import pandas as pd
    except ImportError:
        print("mini-batch smoke skipped: pandas is unavailable")
        return

    frame = pd.DataFrame(
        {
            "text": ["fast bike", "slow bike"],
            "value": [1.0, 2.0],
        }
    )

    bow = feature_extraction.BagOfWords(on="text")
    bow_frame = bow.transform_many(frame)
    check(bow_frame.index.equals(frame.index), "BagOfWords.transform_many did not preserve index")

    tfidf = feature_extraction.TFIDF(on="text")
    tfidf.learn_many(frame)
    tfidf_frame = tfidf.transform_many(frame)
    check(tfidf_frame.index.equals(frame.index), "TFIDF.transform_many did not preserve index")

    select_frame = compose.Select("value").transform_many(frame)
    check(list(select_frame.columns) == ["value"], "Select.transform_many returned the wrong columns")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run small River pipeline and feature smoke checks.")
    parser.add_argument("--debug", "--show-debug", action="store_true", help="Print debug_one output for the smoke models.")
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Also run a tiny mini-batch smoke check when pandas is available.",
    )
    parser.add_argument(
        "--no-types",
        action="store_true",
        help="Hide type annotations in debug_one output.",
    )
    parser.add_argument(
        "--n-decimals",
        type=int,
        default=5,
        help="Number of decimal places to show in debug_one output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    show_types = not args.no_types

    smoke_mixed_features(show_types=show_types, n_decimals=args.n_decimals, debug=args.debug)
    smoke_timestamp_routing(show_types=show_types, n_decimals=args.n_decimals, debug=args.debug)
    if args.batch:
        smoke_batch()

    print("pipeline_feature_smoke_ok=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
