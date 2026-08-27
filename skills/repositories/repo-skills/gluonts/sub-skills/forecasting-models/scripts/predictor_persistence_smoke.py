#!/usr/bin/env python3
"""Checkout-independent GluonTS predictor persistence smoke."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Serialize and reload a small GluonTS local predictor in a temporary "
            "directory, then compare deterministic forecasts."
        )
    )
    parser.add_argument(
        "--prediction-length",
        type=int,
        default=4,
        help="Forecast horizon for the local predictor (default: 4).",
    )
    parser.add_argument(
        "--season-length",
        type=int,
        default=4,
        help="Season length for SeasonalNaivePredictor (default: 4).",
    )
    parser.add_argument(
        "--freq",
        default="D",
        help="Frequency string for the synthetic ListDataset (default: D).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print forecast arrays and serialized file names.",
    )
    return parser


def forecast_means(predictor, dataset):
    return [np.asarray(f.mean, dtype=float) for f in predictor.predict(dataset)]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.prediction_length <= 0:
        print("ERROR: --prediction-length must be positive", file=sys.stderr)
        return 2
    if args.season_length <= 0:
        print("ERROR: --season-length must be positive", file=sys.stderr)
        return 2

    try:
        from gluonts.dataset.common import ListDataset
        from gluonts.model.predictor import Predictor
        from gluonts.model.seasonal_naive import SeasonalNaivePredictor
    except ImportError as exc:
        print(f"ERROR: required GluonTS imports failed: {exc}", file=sys.stderr)
        return 2

    target = [10.0, 12.0, 11.0, 13.0, 10.0, 12.0, 11.0, 13.0]
    dataset = ListDataset(
        [{"start": "2024-01-01", "target": target, "item_id": "demo"}],
        freq=args.freq,
    )

    predictor = SeasonalNaivePredictor(
        prediction_length=args.prediction_length,
        season_length=args.season_length,
    )

    before = forecast_means(predictor, dataset)

    with TemporaryDirectory(prefix="gluonts-predictor-smoke-") as tmp:
        model_dir = Path(tmp)
        try:
            predictor.serialize(model_dir)
            reloaded = Predictor.deserialize(model_dir)
        except Exception as exc:  # noqa: BLE001 - report concrete serialization failure.
            print(
                "ERROR: predictor serialization/deserialization failed for "
                f"{type(predictor).__name__}: {exc}",
                file=sys.stderr,
            )
            return 2

        after = forecast_means(reloaded, dataset)
        files = sorted(path.name for path in model_dir.iterdir())

    if len(before) != len(after):
        print("ERROR: forecast count changed after reload", file=sys.stderr)
        return 2

    for idx, (lhs, rhs) in enumerate(zip(before, after)):
        if not np.array_equal(lhs, rhs):
            print(
                f"ERROR: forecast mean changed for item {idx}: "
                f"before={lhs.tolist()} after={rhs.tolist()}",
                file=sys.stderr,
            )
            return 2

    result = {
        "status": "ok",
        "predictor": type(predictor).__name__,
        "prediction_length": args.prediction_length,
        "season_length": args.season_length,
        "forecast_mean": [arr.tolist() for arr in before],
    }
    if args.verbose:
        result["serialized_files"] = files

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
