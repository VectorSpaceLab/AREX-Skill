# Troubleshooting Models and Flavors

## Signature or schema mismatch

Symptoms:

- `Failed to enforce schema` errors from pyfunc prediction or serving.
- Missing required columns, unexpected columns, wrong dtype, or nested JSON shape errors.
- Serving works with one payload format but fails with another.

Fixes:

1. Inspect `loaded_model.metadata.signature` or `mlflow.models.get_model_info(model_uri).signature`.
2. Recreate the input as the same type and shape used in `input_example`.
3. For tabular data, preserve column names and order; prefer `dataframe_split` for HTTP serving.
4. If the signature was inferred from the wrong object, relog the model with `infer_signature(correct_input, correct_output, params=correct_params)`.
5. If the model intentionally accepts flexible JSON, use a compatible explicit schema or accept that `AnyType` weakens runtime validation.

## Pyfunc predict signature changes

Symptoms:

- Warnings that `params` are ignored.
- Type errors involving `context`, `model_input`, or `params`.
- A model works before logging but fails after `mlflow.pyfunc.load_model`.

Fixes:

- Prefer `def predict(self, context, model_input, params=None)` for broad compatibility.
- Modern MLflow permits omitting unused `context`, but do not mix incompatible argument orderings.
- If you need inference params, include `params=None` in `predict` and infer/log a params schema.
- Test both direct class invocation and loaded pyfunc invocation; the loaded path adds schema enforcement and params routing.

## Dependency or environment file issues

Symptoms:

- Import errors when loading a flavor model.
- Warnings that model dependencies differ from the current environment.
- `mlflow models serve` fails during environment creation.

Fixes:

1. Inspect `requirements.txt`, `conda.yaml`, `python_env.yaml`, and flavor entries in `MLmodel`.
2. Use `mlflow.pyfunc.get_model_dependencies(model_uri)` to locate the model environment file.
3. Add missing pure-Python dependencies with `extra_pip_requirements` at log time or `mlflow models update-pip-requirements` afterward.
4. For optional heavy flavors, install the correct framework stack (`torch`, `transformers`, `langchain`, etc.) before loading native flavor modules.
5. Distinguish environment reconstruction problems from model bugs by trying `mlflow.pyfunc.load_model(...).predict(...)` in the current environment.

## Input example validation failures

Symptoms:

- Logging fails while validating `input_example`.
- Signature inferred from scalar/list data does not match serving payloads.
- Input examples serialize but cannot be reloaded as expected.

Fixes:

- Make `input_example` a small but representative sample of the intended request shape.
- For models with params, use a signature with `params=`; for some flavor APIs, an `(input_data, params)` example pattern is supported.
- Keep examples tiny and JSON/pandas friendly.
- If automatic signature inference from input examples is wrong, pass `signature=False` only as a temporary diagnostic; relog with an explicit signature for production use.

## Missing optional flavor packages

Symptoms:

- `ModuleNotFoundError` for framework packages.
- Native `mlflow.<flavor>.load_model` fails but pyfunc metadata inspection works.
- Evaluation imports SHAP, text, Torch, Transformers, or other metric dependencies unexpectedly.

Fixes:

- Use pyfunc loading for generic prediction when native flavor loading is not required.
- Install the optional flavor stack matching the model artifact.
- For `mlflow.evaluate`, use a simpler `model_type` or disable optional evaluator behaviors when possible; otherwise install metric dependencies.
- Document heavyweight optional dependencies in project docs rather than bundling them into smoke scripts.

## Model URI resolution

Symptoms:

- `runs:/...` URI cannot find a run artifact.
- `models:/...` URI cannot resolve without registry configuration.
- Local path works but remote URI fails.

Fixes:

1. Confirm `mlflow.get_tracking_uri()` and artifact store access.
2. For `runs:/<run_id>/<path>`, verify the run ID and model artifact name from the run artifacts.
3. For `models:/...`, route registry lifecycle and alias/version investigation to `tracking-and-registry`.
4. Download remote artifacts locally only for inspection; keep generated skills and scripts independent of source checkout paths.

## Serving payload format problems

Symptoms:

- HTTP 400 responses from `/invocations`.
- Local `predict` succeeds but server request fails.
- Params are ignored or rejected by the serving server.

Fixes:

- Convert the request to a local Python object and call `loaded_model.predict(...)`; then serialize the same shape.
- Use `dataframe_split` for named tabular inputs: `{"dataframe_split": {"columns": [...], "data": [...]}}`.
- Use `instances` for row-oriented JSON/dict models.
- Include `params` only when supported by the model and signature.
- Compare server logs with schema metadata in `MLmodel`.

## Evaluation target or prediction mistakes

Symptoms:

- `mlflow.evaluate` says target or prediction columns are missing.
- Built-in metrics are nonsensical or fail with dtype errors.
- A callable receives target columns and returns unexpected predictions.

Fixes:

1. Ensure `targets="target_column"` points to a real ground-truth column.
2. If `model=None`, ensure `predictions="prediction_column"` points to precomputed predictions.
3. If `model` is callable, drop target/prediction columns before invoking the underlying estimator.
4. Choose a compatible `model_type`; do not evaluate numeric regression outputs as classifier labels.
5. Start with `env_manager="local"` and no custom metrics, then add isolation and extra metrics after the base call succeeds.
