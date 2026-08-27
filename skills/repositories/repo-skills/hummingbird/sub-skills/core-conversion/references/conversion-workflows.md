# Conversion workflows

This reference covers the common path: an already-trained scikit-learn-style estimator is converted with Hummingbird, then the converted container is checked against the original estimator on representative input.

## Minimal CPU PyTorch conversion

Use PyTorch (`"torch"` or `"pytorch"`) as the default backend for quick local validation because it has the fewest tracing requirements among the common tensor backends.

```python
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from hummingbird.ml import convert

X = np.asarray(X, dtype=np.float32)  # representative 2-D input
skl_model = RandomForestClassifier(n_estimators=10, max_depth=5, random_state=0)
skl_model.fit(X, y)

hb_model = convert(skl_model, "torch")

skl_pred = skl_model.predict(X)
hb_pred = hb_model.predict(X)
np.testing.assert_allclose(hb_pred, skl_pred, rtol=1e-6, atol=1e-6)

if hasattr(skl_model, "predict_proba") and hasattr(hb_model, "predict_proba"):
    np.testing.assert_allclose(
        hb_model.predict_proba(X),
        skl_model.predict_proba(X),
        rtol=1e-6,
        atol=1e-6,
    )
```

For simple classification and regression tasks, the converted object behaves like a scikit-learn-style container with methods such as `predict` and, when supported by the source estimator, `predict_proba`.

## Backend choice at a glance

| Requested backend | Typical aliases | Core note |
|---|---|---|
| PyTorch | `"torch"`, `"pytorch"`; case-insensitive | Best first choice for CPU parity and simple conversion. |
| TorchScript | `"torch.jit"`, `"torchscript"`; case-insensitive | Requires `test_input`; route deployment/performance details to `advanced-backends-and-performance`. |
| ONNX output | `"onnx"` | Requires ONNX dependencies and representative `test_input` for sklearn sources; route ONNX model I/O to `onnx-and-model-io`. |
| TVM | `"tvm"` | Requires TVM and `test_input`; route to `advanced-backends-and-performance`. |

If the backend is misspelled or its dependency is not installed, Hummingbird raises `MissingBackend`.

## `test_input` workflow

`test_input` is representative inference data used by backends that trace or compile model execution. Use a small, correctly shaped sample with the same feature layout and dtype family as production inference.

```python
hb_model = convert(skl_model, "torch.jit", test_input=X[:8])
```

Rules of thumb:

- Pass a 2-D NumPy array for ordinary tabular sklearn estimators.
- Keep column order, feature count, and dtype consistent with training.
- For TorchScript, ONNX output from sklearn sources, and TVM, provide `test_input` rather than relying on defaults.
- For pandas or multiple-input workflows, route detailed data-layout handling to `sklearn-pipelines-and-operators`.

## Prediction parity checklist

Validate the methods that the user will actually call:

| Source behavior | Parity check |
|---|---|
| Classifier labels | `np.testing.assert_allclose(hb.predict(X), skl.predict(X))` for numeric labels, or exact equality for nonnumeric labels. |
| Class probabilities | `np.testing.assert_allclose(hb.predict_proba(X), skl.predict_proba(X), rtol=1e-6, atol=1e-6)`. |
| Regressor output | `np.testing.assert_allclose(hb.predict(X), skl.predict(X), rtol=1e-6, atol=1e-6)`. |
| Transformer output | `np.testing.assert_allclose(hb.transform(X), skl.transform(X), rtol=1e-6, atol=1e-6)`. |
| Anomaly scores | Check `decision_function` and/or `score_samples` when those are the intended calls. |

If parity fails, first confirm the source estimator is fitted, `X` has the same features as training, and the selected converter supports every operator in the model or pipeline.

## Fixed-batch conversion with `convert_batch`

Use `convert_batch` when the converted model must support batch-by-batch inference where the total number of rows is constrained to:

```text
input_rows = test_input.shape[0] * k + remainder_size
```

Here, `test_input.shape[0]` is the fixed batch size and `k` is any nonnegative integer. Set `remainder_size` to the expected leftover row count for uneven totals.

```python
from hummingbird.ml import convert_batch

batch_size = 10
X_trace = X[:batch_size]
remainder_size = X.shape[0] % batch_size

hb_model = convert_batch(
    skl_model,
    "torch",
    X_trace,
    remainder_size=remainder_size,
)

np.testing.assert_allclose(
    hb_model.predict(X),
    skl_model.predict(X),
    rtol=1e-6,
    atol=1e-6,
)
```

Use this pattern for uneven fixed-batch workloads. If the user is mainly tuning batch size for throughput, route detailed threading/performance trade-offs to `advanced-backends-and-performance`.

## Basic tree conversion option

For tree estimators, `extra_config` can select a tree implementation strategy. Keep this sub-skill to syntax-level use; route detailed strategy selection and operator coverage to `sklearn-pipelines-and-operators`.

```python
from hummingbird.ml import constants, convert

hb_model = convert(
    skl_tree_model,
    "torch",
    extra_config={constants.TREE_IMPLEMENTATION: "gemm"},
)
```

Known tree implementation values include `"gemm"`, `"tree_trav"`, and `"perf_tree_trav"`.

## Smoke helper

Run the bundled helper to validate a tiny deterministic conversion in the current Python environment:

```bash
python scripts/convert_sklearn_smoke.py --backend torch --model decision-tree
python scripts/convert_sklearn_smoke.py --backend torch --model random-forest --batch-size 5 --remainder-size 3 --json
```

Run it from an environment where `hummingbird-ml`, scikit-learn, NumPy, and the selected backend dependencies are installed. The helper imports Hummingbird normally and does not modify `sys.path`.
