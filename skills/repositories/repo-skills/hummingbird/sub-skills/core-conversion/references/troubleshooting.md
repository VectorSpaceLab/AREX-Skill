# Core conversion troubleshooting

## Quick triage table

| Symptom or exception | Likely cause | Corrective action |
|---|---|---|
| `sklearn.exceptions.NotFittedError` | The source estimator has not been fitted. | Fit the estimator first, or call `check_is_fitted(model)` before `convert`. Hummingbird converts trained models; it does not train them. |
| `hummingbird.ml.exceptions.MissingBackend` | Backend name is misspelled or the required backend dependency is not installed/visible. | Check `hummingbird.ml.backends`; use `"torch"`/`"pytorch"` for core CPU work. Route optional backend setup to the appropriate backend sub-skill. |
| `hummingbird.ml.exceptions.MissingConverter` | A model, pipeline step, transformer, or predictor has no registered converter. | Identify the unsupported operator. Route sklearn operator/pipeline coverage to `sklearn-pipelines-and-operators`; route optional source packages to `optional-source-models`. |
| `RuntimeError` saying the backend requires test inputs | Backend needs representative input to trace/compile the model. | Re-run with `test_input=X_sample` of the same shape, dtype, and feature order expected at inference. |
| `ValueError: Backend must be a string` | The second positional argument is not a backend string. | Use `convert(model, "torch", ...)`, not an initial-types list or backend object. |
| Converted output has wrong shape | `test_input` or inference input does not match the trained model's feature layout. | Check input rank, feature count, column order, pandas column names, and multiple-input layout. Route complex pipelines to `sklearn-pipelines-and-operators`. |
| `predict_proba` missing on converted container | Source estimator or converter path does not expose probability output. | Validate the method actually exists on both source and converted models; compare only intended methods. |
| Parity mismatch above tolerance | Unsupported operator path, dtype/layout mismatch, tree implementation/precision choice, or checking on different preprocessing data. | Reproduce on a tiny representative slice, compare source preprocessing output, try the default tree implementation, and route operator-specific cases to `sklearn-pipelines-and-operators`. |
| `convert_batch` works for one input size but fails for another | Total rows do not match `test_input.shape[0] * k + remainder_size`. | Recompute `remainder_size = len(X_eval) % batch_size`, recreate the batch container, and retest parity on the exact target row count. |

## Not-fitted estimator recovery

Before conversion, verify the source estimator has learned attributes:

```python
from sklearn.utils.validation import check_is_fitted
from hummingbird.ml import convert

check_is_fitted(skl_model)
hb_model = convert(skl_model, "torch")
```

If `check_is_fitted` raises, the correct fix is to run the estimator's `fit(...)` step with the intended training data, then convert the fitted object. Do not catch the error and continue to conversion; the resulting model would not have learned parameters to translate.

## Missing backend recovery

Backend registration depends on installed packages. Inspect available backends:

```python
import hummingbird.ml
print(hummingbird.ml.backends)
```

Recovery order:

1. Normalize spelling: try `"torch"` or `"pytorch"` for PyTorch, and `"torch.jit"` or `"torchscript"` for TorchScript.
2. If `"onnx"` is missing, route ONNX dependency and model I/O details to `onnx-and-model-io`.
3. If `"tvm"` or CUDA behavior is requested, route setup and verification to `advanced-backends-and-performance`.
4. If the backend appears in `hummingbird.ml.backends` but conversion still fails, check whether `test_input` is required.

## Missing converter recovery

`MissingConverter` means the backend exists but Hummingbird could not translate at least one operator in the source model. For pipelines, the unsupported operator may be a preprocessing step rather than the final estimator.

Recommended narrowing pattern:

```python
for name, step in getattr(pipeline, "steps", []):
    print(name, type(step))
```

Then route as follows:

- scikit-learn estimator or preprocessing coverage: `sklearn-pipelines-and-operators`.
- LightGBM, XGBoost, SparkML, Prophet, or optional dependency source model: `optional-source-models`.
- ONNX-ML source model or ONNX output backend: `onnx-and-model-io`.

## Backend requires `test_input`

Some backend paths need representative data to trace or compile model execution. Use a small sample with the same feature count and dtype family as inference input:

```python
hb_model = convert(model, "torch.jit", test_input=X[:8])
hb_onnx = convert(model, "onnx", test_input=X[:8])
```

For `convert_batch`, `test_input` is always required and its row count defines the batch size.

## Uneven fixed-batch parity

When a target workload has uneven rows, create the batch container for that remainder:

```python
batch_size = 8
remainder_size = X_eval.shape[0] % batch_size
hb_model = convert_batch(model, "torch", X_eval[:batch_size], remainder_size=remainder_size)
np.testing.assert_allclose(hb_model.predict(X_eval), model.predict(X_eval), rtol=1e-6, atol=1e-6)
```

If the next workload has a different remainder, rebuild the batch container or choose an ordinary `convert` path if fixed-batch behavior is not required.

## Import and dependency failures

If importing Hummingbird fails, first confirm the distribution package `hummingbird-ml` is installed in the active Python environment. For core CPU PyTorch workflows, scikit-learn, NumPy, and PyTorch must also be importable. Optional backends or source ecosystems may require additional packages; keep those routes out of this core sub-skill unless the user's task is specifically about them.
