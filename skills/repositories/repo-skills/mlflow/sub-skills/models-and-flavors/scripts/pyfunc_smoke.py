#!/usr/bin/env python3
"""Standalone smoke test for custom MLflow pyfunc packaging."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a tiny local custom pyfunc log/load/predict smoke test with params and signature.",
    )
    parser.add_argument(
        "--experiment-name",
        default="pyfunc-smoke",
        help="Experiment name to create or reuse in the temporary local tracking store.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        import mlflow
        import pandas as pd
        from mlflow.models import infer_signature
    except ModuleNotFoundError as exc:
        missing = exc.name or "dependency"
        raise SystemExit(
            f"Required package {missing!r} is not importable. Install MLflow with its runtime "
            "dependencies in the active Python environment, then rerun this smoke script."
        ) from exc

    class LinearPyfunc(mlflow.pyfunc.PythonModel):
        def predict(self, context, model_input, params=None):
            params = params or {}
            slope = params.get("slope", 2.0)
            intercept = params.get("intercept", 1.0)
            return pd.DataFrame({"prediction": model_input["x"] * slope + intercept})

    input_example = pd.DataFrame({"x": [0.0, 1.5, 3.0]})
    default_params = {"slope": 2.0, "intercept": 1.0}
    output_example = LinearPyfunc().predict(None, input_example, default_params)
    signature = infer_signature(input_example, output_example, params=default_params)

    with tempfile.TemporaryDirectory(prefix="mlflow-pyfunc-smoke-") as temp_dir:
        tracking_db = Path(temp_dir) / "mlflow.db"
        mlflow.set_tracking_uri(f"sqlite:///{tracking_db}")
        mlflow.set_experiment(args.experiment_name)

        with mlflow.start_run():
            model_info = mlflow.pyfunc.log_model(
                name="linear_pyfunc",
                python_model=LinearPyfunc(),
                input_example=input_example,
                signature=signature,
                pip_requirements=["mlflow", "pandas"],
            )

        loaded_model = mlflow.pyfunc.load_model(model_info.model_uri)
        predictions = loaded_model.predict(
            pd.DataFrame({"x": [2.0, 4.0]}),
            params={"slope": 3.0, "intercept": -1.0},
        )
        expected = [5.0, 11.0]
        actual = predictions["prediction"].tolist()
        if actual != expected:
            raise AssertionError(f"Unexpected predictions: {actual} != {expected}")

        metadata = loaded_model.metadata
        if metadata.signature is None or metadata.signature.params is None:
            raise AssertionError("Expected model signature with params schema")

        print(
            json.dumps(
                {
                    "ok": True,
                    "model_uri_scheme": model_info.model_uri.split(":", 1)[0],
                    "predictions": actual,
                    "has_signature": metadata.signature is not None,
                    "has_params_schema": metadata.signature.params is not None,
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
