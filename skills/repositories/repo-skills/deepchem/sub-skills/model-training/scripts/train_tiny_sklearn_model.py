#!/usr/bin/env python
"""Train, evaluate, save, and reload a tiny DeepChem SklearnModel."""

import argparse
import json
import tempfile


def make_dataset(dc, np):
    x_values = np.array(
        [
            [0.0, 0.0, 1.0],
            [0.0, 1.0, 1.0],
            [1.0, 0.0, 1.0],
            [1.0, 1.0, 1.0],
            [2.0, 0.0, 1.0],
            [2.0, 1.0, 1.0],
        ],
        dtype=float,
    )
    y_values = 0.5 * x_values[:, 0] + 2.0 * x_values[:, 1] + 0.25
    weights = np.ones_like(y_values)
    ids = np.array([f"sample-{index}" for index in range(len(y_values))])
    return dc.data.NumpyDataset(x_values, y_values, weights, ids)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Train, evaluate, save, and reload a tiny DeepChem SklearnModel."
    )
    parser.add_argument(
        "--n-estimators",
        type=int,
        default=32,
        help="Number of trees for the tiny RandomForestRegressor smoke model.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        import deepchem as dc
        import numpy as np
        from sklearn.ensemble import RandomForestRegressor
    except ImportError as exc:
        raise SystemExit(
            "This helper requires deepchem, numpy, and scikit-learn. "
            "Install DeepChem base dependencies before running the smoke. "
            f"Missing import: {exc}"
        ) from exc

    dataset = make_dataset(dc, np)
    with tempfile.TemporaryDirectory() as model_dir:
        estimator = RandomForestRegressor(
            n_estimators=args.n_estimators,
            random_state=17,
            max_depth=3,
        )
        model = dc.models.SklearnModel(estimator, model_dir=model_dir)
        model.fit(dataset)

        metric = dc.metrics.Metric(dc.metrics.pearson_r2_score, mode="regression")
        scores = model.evaluate(dataset, [metric])
        predictions = model.predict(dataset)
        model.save()

        restored = dc.models.SklearnModel(None, model_dir=model_dir)
        restored.reload()
        restored_predictions = restored.predict(dataset)

        if not np.allclose(predictions, restored_predictions):
            raise AssertionError("Reloaded model predictions differ from saved model predictions")

        print(
            json.dumps(
                {
                    "score_key": metric.name,
                    "score": round(float(scores[metric.name]), 6),
                    "prediction_shape": list(predictions.shape),
                    "restored_prediction_shape": list(restored_predictions.shape),
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
