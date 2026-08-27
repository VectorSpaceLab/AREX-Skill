# ONNX Workflows

This reference covers Hummingbird's `backend="onnx"` target and ONNX-ML
`ModelProto` source inputs. For the general `convert`/`convert_batch` API shape,
use the sibling core-conversion route first.

## Dependency map

| Workflow | Required packages | Notes |
| --- | --- | --- |
| Fitted sklearn-style model -> Hummingbird ONNX backend | `hummingbird-ml`, `torch`, `onnx`, `onnxruntime`, `scikit-learn` source package | Hummingbird exports through PyTorch and wraps the ONNX model in an `ONNXContainer`; `onnxruntime` is required for prediction. |
| ONNX-ML `ModelProto` source -> Hummingbird backend | Above plus importable ONNX-ML tooling such as `onnxmltools` or `skl2onnx` | Use these packages to create the source `ModelProto`; Hummingbird then converts that model to `onnx`, `torch`, or another supported backend. |
| Optional source model -> ONNX | Source package plus ONNX stack | LightGBM, XGBoost, Prophet, and SparkML installation details belong in the optional-source-models route. |

The package extra `hummingbird-ml[onnx]` is the usual way to install ONNX-related
runtime packages, but use the same Python environment that will import and run
Hummingbird. Having the `onnx` serialization package without `onnxruntime` is
not enough for `ONNXContainer` inference.

## Fitted sklearn-style model to ONNX backend

Use this when the source model is already fitted and Hummingbird can parse the
original sklearn-like estimator directly.

```python
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from hummingbird.ml import convert, constants

X = np.asarray(X, dtype=np.float32)  # representative inference/tracing input
model = DecisionTreeClassifier(random_state=0).fit(X, y)

hb_onnx = convert(
    model,
    "onnx",
    test_input=X,
    extra_config={
        # Optional: current conversion path defaults to opset 13 if omitted.
        constants.ONNX_TARGET_OPSET: 13,
        # Optional: sets hb_onnx.model.graph.name; it does not persist a file.
        constants.ONNX_OUTPUT_MODEL_NAME: "my_hummingbird_model",
    },
)

labels = hb_onnx.predict(X)
probs = hb_onnx.predict_proba(X)
```

Important points:

- For non-ONNX source models targeting `backend="onnx"`, pass representative
  `test_input`; otherwise conversion raises a runtime error that the ONNX
  backend requires test inputs.
- `test_input` should match the shape and dtype the converted model will see in
  inference. Hummingbird commonly uses `float32` arrays for tensor export.
- `constants.ONNX_OUTPUT_MODEL_NAME` names the graph and temporary export file;
  Hummingbird removes the temporary file after loading the exported model. Use
  `save()` when you need a reusable artifact.
- `constants.ONNX_TARGET_OPSET` controls the output model's opset. In the
  current conversion path, the default output opset is 13; set the constant when
  an application requires a different opset.

## ONNX-ML input model recipes

Use this when the user already has an ONNX-ML `ModelProto`, or when another
converter is the best path to express the source model in ONNX-ML before asking
Hummingbird to target a backend.

### Recipe: sklearn estimator through `onnxmltools`

```python
import numpy as np
from sklearn.linear_model import LogisticRegression
from onnxmltools import convert_sklearn
from onnxmltools.convert.common.data_types import FloatTensorType
from hummingbird.ml import convert

X = np.asarray(X, dtype=np.float32)
model = LogisticRegression(solver="liblinear").fit(X, y)

onnx_ml_model = convert_sklearn(
    model,
    initial_types=[("input", FloatTensorType([None, X.shape[1]]))],
    target_opset=11,
)

hb_onnx = convert(onnx_ml_model, "onnx")
# Or pass X explicitly when the ONNX schema is dynamic, incomplete, or confusing:
# hb_onnx = convert(onnx_ml_model, "onnx", X)
```

### Recipe: sklearn estimator through `skl2onnx`

```python
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from hummingbird.ml import convert

onnx_ml_model = convert_sklearn(
    fitted_sklearn_model,
    initial_types=[("float_input", FloatTensorType([None, n_features]))],
)
hb_onnx = convert(onnx_ml_model, "onnx", test_input=sample_X)
```

### Recipe: LightGBM through ONNX-ML

```python
from onnxmltools.convert import convert_lightgbm
from onnxconverter_common.data_types import FloatTensorType
from hummingbird.ml import convert

onnx_ml_model = convert_lightgbm(
    fitted_lightgbm_model,
    initial_types=[("input", FloatTensorType([None, n_features]))],
    target_opset=9,
)
hb_onnx = convert(onnx_ml_model, "onnx")
```

Install and source-model caveats for LightGBM, XGBoost, Prophet, and SparkML are
owned by the optional-source-models route. This reference only covers what
Hummingbird expects once the ONNX-ML model object exists.

## `test_input` behavior for ONNX-ML sources

When the input model is an ONNX `ModelProto`, Hummingbird can sometimes generate
tracing input from the ONNX schema if `test_input` is omitted. That inference is
limited:

- Each graph input must expose a name, tensor type, and shape.
- Supported auto-generated input element types are float32, float64, int32, and
  int64.
- A one-dimensional schema shape is treated as `[1, n]`.
- A dynamic batch dimension represented as `0` is replaced with `1` for tracing.
- Multiple inputs must have the same inferred shape; Hummingbird sets the total
  feature count from the number of inputs and width of each input.
- String tensors and other unsupported types need explicit `test_input` and may
  still hit exporter/runtime limits.

Prefer explicit `test_input` when the ONNX schema is dynamic, missing names,
missing shapes, has multiple inputs, uses strings, or represents data types that
are hard to infer from the graph alone.

## ONNX runtime session behavior

A Hummingbird ONNX conversion returns an `ONNXContainer` subclass that mirrors
sklearn-style inference. At construction/load time the container:

- Requires `onnxruntime` to be importable.
- Creates an `onnxruntime.InferenceSession` from the serialized ONNX model.
- Captures session input names and output names, then maps future prediction
  arguments to those names.
- If `constants.N_THREADS` is present in `extra_config`, sets ONNX Runtime
  intra-op threads to that value, inter-op threads to `1`, and uses sequential
  execution.
- Converts prediction inputs with `np.array(...)`; string arrays require
  `constants.MAX_STRING_LENGTH` in the model's extra config before they can be
  converted to Hummingbird's numeric string representation.

## Output method selection

| Original estimator kind | Typical methods on the converted ONNX container |
| --- | --- |
| Classifier | `predict(X)` for labels and `predict_proba(X)` for probabilities |
| Regressor | `predict(X)` |
| Transformer/preprocessor | `transform(X)` |
| Anomaly detector | `predict(X)`, `decision_function(X)`, and `score_samples(X)` when the underlying container supports them |

If a method is absent, verify the original estimator kind instead of assuming an
ONNX conversion failure.
