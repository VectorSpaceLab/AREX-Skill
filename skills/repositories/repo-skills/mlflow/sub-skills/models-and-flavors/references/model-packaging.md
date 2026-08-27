# Model Packaging Recipes

## Choose the right packaging path

- Use native flavor logging (`mlflow.sklearn.log_model`, `mlflow.pytorch.log_model`, etc.) when the framework flavor supports the trained object and you want framework-specific loading plus pyfunc inference.
- Use `mlflow.pyfunc.PythonModel` when inference needs custom preprocessing, postprocessing, artifacts, nonstandard inputs, or params.
- Use model-as-code for pyfunc models that should avoid pickling live `__main__` objects. Put the model class/function in a Python file and call `mlflow.models.set_model(...)` in that file.
- Use a callable pyfunc for tiny pure-Python transformations, but prefer `PythonModel` for artifact access, config, params, and future extension.

## Minimal custom pyfunc checklist

1. Implement `predict(self, context, model_input, params=None)` or, if `context` is unused in a modern MLflow version, `predict(self, model_input, params=None)`.
2. Use pandas, NumPy, or JSON-compatible inputs that match intended serving payloads.
3. Infer or define a signature using the same shape and column names expected at inference.
4. Include `input_example` to exercise validation during logging and document request shape.
5. Pin lightweight dependencies with `pip_requirements` or add only deltas with `extra_pip_requirements`.
6. Keep external files in `artifacts={...}` and load them through `context.artifacts`.
7. Load the saved/logged model with `mlflow.pyfunc.load_model` and call `predict` before considering the package complete.

## Pyfunc with params and input example

```python
import pandas as pd
import mlflow
from mlflow.models import infer_signature

class ThresholdModel(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input, params=None):
        threshold = (params or {}).get("threshold", 0.5)
        return (model_input["score"] >= threshold).astype(int)

example = pd.DataFrame({"score": [0.2, 0.8]})
params = {"threshold": 0.6}
signature = infer_signature(example, ThresholdModel().predict(None, example, params), params=params)

with mlflow.start_run():
    model_info = mlflow.pyfunc.log_model(
        name="threshold_model",
        python_model=ThresholdModel(),
        input_example=example,
        signature=signature,
        pip_requirements=["mlflow", "pandas"],
    )

loaded = mlflow.pyfunc.load_model(model_info.model_uri)
loaded.predict(example, params={"threshold": 0.7})
```

## Model-as-code pattern

`model_code.py`:

```python
import mlflow

class UppercaseModel(mlflow.pyfunc.PythonModel):
    def predict(self, context, model_input, params=None):
        return [str(value).upper() for value in model_input]

mlflow.models.set_model(UppercaseModel())
```

Logging:

```python
with mlflow.start_run():
    model_info = mlflow.pyfunc.log_model(name="uppercase", python_model="model_code.py")
```

Use this pattern when you want source-code packaging rather than cloudpickle serialization. Keep helper modules importable through normal package dependencies or `code_paths`.

## Flavor logging pattern

```python
from mlflow.models import infer_signature

predictions = model.predict(X_train)
signature = infer_signature(X_train, predictions)
model_info = mlflow.sklearn.log_model(
    sk_model=model,
    name="model",
    signature=signature,
    input_example=X_train.head(5),
    registered_model_name=None,
)
```

- For sklearn, log `serialization_format` only when you need a specific pickle/cloudpickle behavior.
- For PyTorch, Transformers, and LangChain, keep optional dependency versions explicit and test load/predict in a clean environment when possible.
- For all flavors, verify the pyfunc flavor with `mlflow.pyfunc.load_model(model_info.model_uri)` unless the model is intentionally framework-only.

## Dependencies and environment files

- MLflow model directories may include `conda.yaml`, `python_env.yaml`, `requirements.txt`, and/or `constraints.txt` depending on flavor and environment manager.
- Use `pip_requirements=[...]` to replace inferred pip requirements with explicit requirements.
- Use `extra_pip_requirements=[...]` to append requirements to MLflow inference.
- Use `mlflow.pyfunc.get_model_dependencies(model_uri)` when MLflow warns that logged dependencies differ from the current environment.
- Use `mlflow models update-pip-requirements` to safely add, remove, or overwrite pip requirements in an existing model package.
- Avoid relying on source checkout-relative imports. Package helper code through model-as-code, a wheel, `code_paths`, or normal package dependencies.

## Model config and artifacts

- `model_config` can be a dict or config file path at save/log time. It becomes available as `context.model_config` for `PythonModel` inference.
- `mlflow.pyfunc.load_model(model_uri, model_config=...)` can supply inference-time overrides for models that support model config.
- `artifacts` maps logical names to local or remote artifact URIs; MLflow resolves them and exposes paths through `context.artifacts`.
- Put slow artifact loading in `load_context` rather than every `predict` call.

## Inspecting a model package

1. Download or locate the model URI with `mlflow.artifacts.download_artifacts` if needed.
2. Open `MLmodel` and verify flavors, `python_function.loader_module`, signature, saved input example info, and environment file names.
3. Read `requirements.txt` and `conda.yaml` for missing optional packages or bad pins.
4. Load through `mlflow.pyfunc.load_model` to confirm the generic inference path.
5. If native flavor loading fails but pyfunc works, isolate whether the issue is framework-specific optional dependencies or the model artifact itself.
