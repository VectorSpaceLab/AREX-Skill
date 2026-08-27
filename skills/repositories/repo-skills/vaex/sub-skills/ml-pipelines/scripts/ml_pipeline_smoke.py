#!/usr/bin/env python3
"""Tiny Vaex ML pipeline smoke test.

Checks installed public APIs only:
- imports vaex.ml and vaex.ml.sklearn explicitly;
- fits a StandardScaler on a tiny train split;
- fits a scikit-learn LinearRegression via vaex.ml.sklearn.Predictor;
- verifies lazy prediction virtual columns;
- saves and loads a vaex.ml.Pipeline with state transfer and predictor.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np


def run_smoke() -> dict:
    import vaex
    import vaex.ml
    import vaex.ml.sklearn  # required explicit import for sklearn wrappers
    from sklearn.linear_model import LinearRegression
    from vaex.ml.sklearn import Predictor

    df = vaex.from_arrays(
        x=np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0]),
        y=np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0]),
        target=np.array([1.0, 3.0, 5.0, 7.0, 9.0, 11.0]),
    )

    train, test = df.ml.train_test_split(test_size=1 / 3, verbose=False)
    assert len(train) == 4, f"expected 4 train rows, got {len(train)}"
    assert len(test) == 2, f"expected 2 test rows, got {len(test)}"

    scaler = vaex.ml.StandardScaler(features=["x", "y"], prefix="scaled_")
    train_scaled = scaler.fit_transform(train)
    assert scaler.features == ["x", "y"]
    assert len(scaler.mean_) == 2 and len(scaler.std_) == 2

    scaled_columns = set(train_scaled.get_column_names(regex="^scaled_"))
    assert scaled_columns == {"scaled_x", "scaled_y"}, sorted(scaled_columns)

    state_transfer = train_scaled.ml.state_transfer()
    test_scaled = state_transfer.transform(test)
    assert {"scaled_x", "scaled_y"}.issubset(test_scaled.get_column_names())

    model = Predictor(
        model=LinearRegression(),
        features=["scaled_x", "scaled_y"],
        target="target",
        prediction_name="pred",
    )
    model.fit(train_scaled)

    pred_array = np.asarray(model.predict(test_scaled))
    predicted = model.transform(test_scaled)
    assert "pred" in predicted.get_column_names(virtual=True)
    np.testing.assert_allclose(predicted.pred.values, pred_array)

    pipeline = vaex.ml.Pipeline([state_transfer, model])
    with tempfile.TemporaryDirectory(prefix="vaex-ml-smoke-") as tmpdir:
        path = Path(tmpdir) / "pipeline.json"
        pipeline.save(str(path))
        assert path.exists() and path.stat().st_size > 0

        loaded = vaex.ml.Pipeline()
        loaded.load(str(path))
        transformed = loaded.transform(test)
        np.testing.assert_allclose(transformed.pred.values, pred_array)
        pipeline_bytes = path.stat().st_size

    return {
        "status": "ok",
        "rows": len(df),
        "train_rows": len(train),
        "test_rows": len(test),
        "scaled_columns": sorted(scaled_columns),
        "prediction_shape": list(pred_array.shape),
        "pipeline_bytes": pipeline_bytes,
        "virtual_columns_checked": ["scaled_x", "scaled_y", "pred"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny Vaex ML StandardScaler + sklearn Predictor + Pipeline smoke test."
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON summary instead of one compact line.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_smoke()
    if args.pretty:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
