# Evaluation and Local Serving

## `mlflow.evaluate` decision table

| Situation | Recommended call shape |
| --- | --- |
| Evaluate a logged model URI | `mlflow.evaluate(model=model_info.model_uri, data=df, targets="label", model_type="classifier")` |
| Evaluate a callable | `mlflow.evaluate(model=predict_fn, data=df, targets="target", model_type="regressor")` |
| Evaluate precomputed predictions | `mlflow.evaluate(data=df, predictions="prediction", targets="target", model_type="regressor")` |
| Evaluate with params | `mlflow.evaluate(model=uri_or_callable, data=df, targets="target", inference_params={...})` |
| Add custom metrics | `mlflow.evaluate(..., extra_metrics=[metric])` |
| Add artifacts | `mlflow.evaluate(..., custom_artifacts=[artifact_fn])` |

## Evaluation repair workflow

1. Confirm whether `model` is present. If absent, `predictions` must name a column in `data`.
2. Confirm `targets` is a column name in `data` or an aligned target vector.
3. Confirm `model_type` matches the prediction task; classifier metrics expect class/probability-compatible outputs, while regressor metrics expect numeric continuous outputs.
4. If a callable receives target columns, wrap it to drop target/prediction columns before calling the underlying model.
5. If evaluation fails in an isolated environment, retry with `env_manager="local"` to distinguish dependency reconstruction problems from metric/data problems.
6. For GenAI/text evaluators, check optional package and judge-model requirements; route tracing and prompt issues to `genai-observability`.

## Tiny callable evaluation pattern

```python
import pandas as pd
import mlflow


def predict(features):
    return features["x"] * 2 + 1


data = pd.DataFrame({"x": [0, 1, 2], "target": [1, 3, 5]})
result = mlflow.evaluate(
    model=predict,
    data=data,
    targets="target",
    model_type="regressor",
    env_manager="local",
)
print(result.metrics)
```

## Precomputed prediction evaluation

```python
data = pd.DataFrame({
    "prediction": [1.0, 3.1, 4.9],
    "target": [1.0, 3.0, 5.0],
})
result = mlflow.evaluate(
    data=data,
    predictions="prediction",
    targets="target",
    model_type="regressor",
)
```

Use precomputed mode when model inference is expensive, impossible in the current environment, or already performed by a serving system.

## Local serving with `mlflow models serve`

```bash
mlflow models serve -m runs:/<run_id>/model -p 5000 --env-manager local
```

Key endpoints for the local inference server:

- `POST /invocations` for predictions.
- `GET /ping` for liveness.
- `GET /health` for health checks.
- `GET /version` for server version metadata.

Prefer `--env-manager local` for quick smoke tests in the current environment. Use `virtualenv`, `conda`, or `uv` when you need to reconstruct the model environment.

## Serving payload formats

Common JSON payloads for `/invocations`:

```json
{"dataframe_split": {"columns": ["x"], "data": [[1.0], [2.0]]}}
```

```json
{"instances": [{"x": 1.0}, {"x": 2.0}], "params": {"scale": 3.0}}
```

Guidance:

- Use `dataframe_split` for tabular models where column order matters.
- Avoid relying on dataframe records orientation for column-sensitive models unless you have verified behavior.
- Include `params` only when the model signature declares parameter schema or the pyfunc model tolerates params.
- Match the logged signature exactly: names, dtypes, optional fields, nested structures, and params.

## Local batch prediction with CLI

```bash
mlflow models predict \
  -m runs:/<run_id>/model \
  -i input.json \
  -o output.json \
  --content-type json \
  --env-manager local
```

Use this to debug serialization and schema enforcement without running an HTTP server. If CLI prediction fails but `loaded_model.predict(data)` works, compare the serialized input file with the pyfunc input object.

## Docker and environment commands

- `mlflow models prepare-env -m <model_uri> --env-manager virtualenv|conda|uv` pre-creates the environment used for serving or prediction.
- `mlflow models generate-dockerfile -m <model_uri> -d <output_dir>` writes a Docker build context.
- `mlflow models build-docker -m <model_uri> -n <image_name>` builds an image for serving.
- `mlflow models update-pip-requirements -m <model_uri> --operation add|remove|overwrite <requirements...>` edits model pip requirements.

Use Docker commands only when Docker is available and local policy allows image builds. Keep skill smoke tests on local pyfunc/evaluate paths to avoid external services.
