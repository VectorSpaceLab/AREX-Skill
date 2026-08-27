# API Reference: Models and Flavors

## Core model metadata

- `mlflow.models.Model(...)` represents an MLflow Model with one or more flavors. The constructor accepts metadata such as `signature`, `metadata`, `resources`, `env_vars`, `auth_policy`, `model_id`, and `prompts` in addition to flavor and run fields.
- `MLmodel` is the YAML metadata file stored in every MLflow Model directory. Inspect it when debugging flavor names, loader modules, environment files, signature serialization, input examples, model size, or model IDs.
- `mlflow.models.get_model_info(model_uri)` returns model metadata without necessarily loading the model implementation.
- Common model URI schemes include local paths, `runs:/<run_id>/<artifact_or_model_name>`, `models:/<name>/<version-or-alias>`, and artifact-store URIs supported by the tracking configuration.

## Signature APIs

```python
from mlflow.models import infer_signature

signature = infer_signature(model_input=None, model_output=None, params=None)
```

- Supported input examples include pandas DataFrames/Series, NumPy arrays, dicts of arrays, SciPy sparse matrices, Spark DataFrames, and JSON-compatible dict/list structures.
- Pass representative `model_output` so both input and output schemas are recorded.
- Pass `params` to declare inference parameters accepted by pyfunc `predict(..., params=...)` and local serving payloads.
- If schema inference cannot infer a precise schema, MLflow may fall back to `AnyType`; treat that as a warning to provide clearer examples or an explicit `ModelSignature`.

## Pyfunc APIs

```python
import mlflow

class MyModel(mlflow.pyfunc.PythonModel):
    def load_context(self, context):
        self.lookup_path = context.artifacts.get("lookup")

    def predict(self, context, model_input, params=None):
        scale = (params or {}).get("scale", 1.0)
        return model_input.assign(score=model_input["x"] * scale)
```

- `PythonModel.predict(self, context, model_input, params=None)` is the stable custom-model hook. Newer MLflow versions also allow omitting unused `context`: `predict(self, model_input, params=None)`.
- `PythonModel.predict_stream(self, context, model_input, params=None)` is for streamable models.
- `mlflow.pyfunc.save_model(path=..., python_model=..., signature=..., input_example=..., pip_requirements=..., extra_pip_requirements=..., artifacts=..., model_config=..., resources=..., auth_policy=...)` saves to a local path.
- `mlflow.pyfunc.log_model(name=..., python_model=..., signature=..., input_example=..., pip_requirements=..., extra_pip_requirements=..., artifacts=..., model_config=..., params=..., tags=..., model_type=..., model_id=..., prompts=...)` logs to the active run.
- `mlflow.pyfunc.load_model(model_uri, model_config=...)` loads any model with a `python_function` flavor and returns a pyfunc wrapper with `predict(data, params=None)`.
- Model-as-code passes a Python file path as `python_model`; that file should call `mlflow.models.set_model(model_instance_or_callable)`.

## Flavor APIs

Typical flavor pattern:

```python
from mlflow.models import infer_signature

predictions = trained_model.predict(train_features)
signature = infer_signature(train_features, predictions)
model_info = mlflow.sklearn.log_model(
    trained_model,
    name="model",
    signature=signature,
    input_example=train_features.head(3),
)
loaded_pyfunc = mlflow.pyfunc.load_model(model_info.model_uri)
```

- `mlflow.sklearn.log_model` / `save_model` / `load_model` package sklearn estimators and also expose `python_function` when supported.
- `mlflow.pytorch.log_model` / `save_model` / `load_model` require PyTorch installed and usually need representative tensor/array examples for useful signatures.
- `mlflow.transformers.log_model` / `save_model` / `load_model` require Transformers stack dependencies and often need task/pipeline metadata; reference heavyweight examples instead of making them default smoke tests.
- `mlflow.langchain.log_model` / `save_model` / `load_model` package chains/runnables; route tracing, prompts, and GenAI scoring details to `genai-observability`.

## Evaluation API

```python
result = mlflow.evaluate(
    model=None,
    data=None,
    *,
    model_type=None,
    targets=None,
    predictions=None,
    evaluators=None,
    evaluator_config=None,
    extra_metrics=None,
    custom_artifacts=None,
    env_manager="local",
    model_config=None,
    inference_params=None,
    model_id=None,
)
```

- `model` can be a model URI, a pyfunc model, or a callable. Omit it only when `data` already contains predictions and `predictions=` names the prediction column.
- `data` is commonly a pandas DataFrame containing feature columns and a target column.
- `model_type` selects built-in evaluator behavior, e.g. `"regressor"`, `"classifier"`, `"question-answering"`, `"text"`, `"text-summarization"`, or `"retriever"`.
- `targets` names the ground-truth column or supplies target values; `predictions` names a prediction column when using precomputed predictions.
- `env_manager="local"` evaluates in the current process; isolated environment modes can expose dependency mismatches but are heavier.

## `mlflow models` CLI

Relevant commands include:

- `mlflow models serve -m <model_uri> -p <port> --env-manager local|virtualenv|conda|uv`
- `mlflow models predict -m <model_uri> -i <input_path> -o <output_path> --content-type json|csv`
- `mlflow models prepare-env -m <model_uri> --env-manager <manager>`
- `mlflow models generate-dockerfile -m <model_uri> -d <output_dir>`
- `mlflow models build-docker -m <model_uri> -n <image_name>`
- `mlflow models update-pip-requirements -m <model_uri> --operation add|remove|overwrite <requirements...>`

Use `mlflow models --help` and per-command `--help` for the exact option set in the installed MLflow version.
