#!/usr/bin/env python3
"""Standalone smoke test for mlflow.evaluate with tiny local fixtures."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny local mlflow.evaluate smoke test for callable and precomputed predictions.",
    )
    parser.add_argument(
        "--experiment-name",
        default="evaluate-smoke",
        help="Experiment name to create or reuse in the temporary local tracking store.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        import mlflow
        import pandas as pd
    except ModuleNotFoundError as exc:
        missing = exc.name or "dependency"
        raise SystemExit(
            f"Required package {missing!r} is not importable. Install MLflow with its runtime "
            "dependencies in the active Python environment, then rerun this smoke script."
        ) from exc

    def predict(features: pd.DataFrame) -> pd.Series:
        return features["x"] * 2.0 + 1.0

    eval_data = pd.DataFrame(
        {
            "x": [0.0, 1.0, 2.0, 3.0],
            "target": [1.0, 3.0, 5.0, 7.0],
        }
    )

    with tempfile.TemporaryDirectory(prefix="mlflow-evaluate-smoke-") as temp_dir:
        tracking_db = Path(temp_dir) / "mlflow.db"
        mlflow.set_tracking_uri(f"sqlite:///{tracking_db}")
        mlflow.set_experiment(args.experiment_name)

        with mlflow.start_run():
            callable_result = mlflow.evaluate(
                model=predict,
                data=eval_data,
                targets="target",
                model_type="regressor",
                env_manager="local",
            )

            precomputed_data = eval_data.copy()
            precomputed_data["prediction"] = predict(eval_data)
            precomputed_result = mlflow.evaluate(
                data=precomputed_data,
                predictions="prediction",
                targets="target",
                model_type="regressor",
                env_manager="local",
            )

        callable_rmse = callable_result.metrics.get("root_mean_squared_error")
        precomputed_rmse = precomputed_result.metrics.get("root_mean_squared_error")
        if callable_rmse != 0 or precomputed_rmse != 0:
            raise AssertionError(
                "Expected perfect regression smoke metrics, got "
                f"callable={callable_rmse}, precomputed={precomputed_rmse}"
            )

        print(
            json.dumps(
                {
                    "ok": True,
                    "callable_rmse": callable_rmse,
                    "precomputed_rmse": precomputed_rmse,
                    "callable_metric_count": len(callable_result.metrics),
                    "precomputed_metric_count": len(precomputed_result.metrics),
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
