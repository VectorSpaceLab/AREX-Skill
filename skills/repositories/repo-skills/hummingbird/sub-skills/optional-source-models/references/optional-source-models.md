# Optional Source Model Workflows

This reference covers Hummingbird workflows whose source model comes from an optional ecosystem rather than core scikit-learn. All examples assume the source model is already trained and the required optional packages are installed in the active Python environment.

For the general `convert` API, backend normalization, prediction containers, and parity checks, route to the core conversion sub-skill. For detailed ONNX output/container I/O, route to the ONNX and model I/O sub-skill.

## General pattern

```python
import numpy as np
import hummingbird.ml

# model is a fitted optional source model.
X_sample = np.asarray(X[:1], dtype=np.float32)
hb_model = hummingbird.ml.convert(model, "torch", X_sample)
# Validate on representative data.
source_pred = model.predict(X_eval)
hb_pred = hb_model.predict(X_eval)
```

Guidelines:

- Fit the source model before conversion.
- Prefer a representative 2-D NumPy `test_input` for tree-based optional models, especially for XGBoost regressors/rankers and all TorchScript/ONNX/TVM-style tracing paths.
- Validate predictions against the original model after conversion. Optional ecosystems can have version-specific behavior.
- If optional packages are installed during a live session, restart Python before importing `hummingbird.ml.supported` or calling conversion.

## LightGBM

### Supported source objects

Hummingbird recognizes these LightGBM objects when `lightgbm` is importable:

- `lightgbm.LGBMClassifier`
- `lightgbm.LGBMRegressor`
- `lightgbm.LGBMRanker`
- `lightgbm.Booster`

The public `convert` documentation states that LightGBM support is for the scikit-learn API. The implementation also registers `Booster` support by reading tree information directly from the trained booster.

### Common PyTorch conversion

```python
import numpy as np
import lightgbm as lgb
import hummingbird.ml

X = np.asarray(X, dtype=np.float32)
model = lgb.LGBMClassifier(n_estimators=50)
model.fit(X, y)

hb_model = hummingbird.ml.convert(model, "torch")
np.testing.assert_allclose(model.predict_proba(X), hb_model.predict_proba(X), rtol=1e-5, atol=1e-5)
```

Notes:

- `LGBMClassifier`, `LGBMRegressor`, and `LGBMRanker` read the fitted model's internal feature count.
- A `Booster` can be converted, but prediction-method availability depends on whether the booster behaves like a regressor/ranker or classifier in the Hummingbird container.
- Tree implementation tuning such as `extra_config={"tree_implementation": "gemm"}` belongs to the sklearn/operator and advanced backend guidance; use parity checks after changing it.

### LightGBM to ONNX

When the target backend is `"onnx"`, install the ONNX extra and pass representative input:

```python
X_sample = np.asarray(X[:4], dtype=np.float32)
onnx_hb_model = hummingbird.ml.convert(model, "onnx", X_sample)
```

If the workflow first converts LightGBM to an ONNX-ML `ModelProto` with `onnxmltools`, route ONNX-ML details to the ONNX/model-I/O sub-skill. This sub-skill owns the LightGBM dependency check and source-family caveats.

### LightGBM caveats

- Direct `LGBMClassifier(boosting_type="rf")` conversion raises a runtime error instructing the user to convert through ONNX first. Use an ONNX-ML interop path if this exact model family is required.
- LightGBM installation failures often come from missing OpenMP libraries (`libomp` on macOS, `libgomp` on some Linux systems). See the troubleshooting reference.

## XGBoost

### Supported source objects

Hummingbird recognizes these XGBoost scikit-learn API objects when `xgboost` is importable and exposes a sufficiently recent native library API:

- `xgboost.XGBClassifier`
- `xgboost.XGBRegressor`
- `xgboost.XGBRanker`

### Feature-count rule

XGBoost conversion needs a feature count. Hummingbird tries, in order:

1. `model.get_booster().num_features()` when available.
2. `model._features_count` when present.
3. A 2-D NumPy `test_input`, using `test_input.shape[1]`.

If none is available, conversion raises an error like:

```text
XGBoost converter is not able to infer the number of input features. Please pass some test_input to the converter.
```

The safest workflow is to pass a representative 2-D NumPy sample:

```python
import numpy as np
import xgboost as xgb
import hummingbird.ml

X = np.asarray(X, dtype=np.float32)
model = xgb.XGBRegressor(n_estimators=50, max_depth=4)
model.fit(X, y)

hb_model = hummingbird.ml.convert(model, "torch", X[:1])
np.testing.assert_allclose(model.predict(X), hb_model.predict(X), rtol=1e-5, atol=1e-5)
```

For classifiers, some XGBoost versions expose enough metadata for `convert(model, "torch", [])` to work, but passing `X[:1]` is still more robust and is required for TorchScript/ONNX/TVM tracing paths.

If a model uses named features, Hummingbird can map the booster feature names to numeric ids during tree parsing. Keep evaluation data columns aligned with the fitted model.

## SparkML

### Supported source objects

Hummingbird recognizes the following SparkML operators when `pyspark` is importable:

- `pyspark.ml.feature.Bucketizer`
- `pyspark.ml.feature.VectorAssembler`
- `pyspark.ml.classification.LogisticRegressionModel`
- Spark `PipelineModel` instances containing supported stages.

### Spark DataFrame conversion input

SparkML conversion should pass a Spark DataFrame as `test_input` so Hummingbird can infer input names, counts, shapes, and dtypes:

```python
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.feature import VectorAssembler
import hummingbird.ml

assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")
pipeline = Pipeline(stages=[assembler, LogisticRegression()])
model = pipeline.fit(train_df)

test_df = train_df.select(feature_columns).limit(10)
hb_model = hummingbird.ml.convert(model, "torch", test_df)
```

Hummingbird converts Spark DataFrame columns into NumPy-like tracing inputs. Supported field kinds include vector columns, arrays, and numeric scalar columns (`IntegerType`, `FloatType`, `DoubleType`, and `LongType`). If conversion reports an unrecognized type, materialize the relevant column as a supported numeric scalar, vector, or array column before converting.

### Prediction data after conversion

Converted SparkML models are Hummingbird containers. In the tested patterns, Spark input can be used for conversion, while parity validation often uses equivalent NumPy arrays or pandas DataFrames with the same input columns.

SparkML workflows require more than a Python import: PySpark, pyarrow, a JVM, and a working local or cluster Spark runtime must all be healthy.

## Prophet

### Supported source object and output scope

When `prophet` is importable, Hummingbird recognizes `prophet.Prophet`. The converter implements the linear trend calculation from a fitted Prophet model. Validate carefully if the user expects a full Prophet forecast with all components rather than trend-only output.

The converter asserts that Prophet growth is linear:

```text
Growth function <name> not supported yet.
```

### PyTorch trend conversion

```python
from prophet import Prophet
import hummingbird.ml

model = Prophet()
model.fit(history_df)  # history_df has Prophet columns ds and y.

hb_model = hummingbird.ml.convert(model, "torch")
future = model.make_future_dataframe(periods=365)
hb_trend = hb_model.predict(future)
```

### Prophet to ONNX

For ONNX, convert datetime inputs to numeric Unix-second values before passing `test_input`:

```python
import numpy as np

future = model.make_future_dataframe(periods=365)
future_np = (future.values - np.datetime64("1970-01-01T00:00:00.000000000")).astype(np.int64) / 1_000_000_000
hb_onnx_model = hummingbird.ml.convert(model, "onnx", future_np)
```

Prophet ONNX conversion also needs ONNX Runtime; use the dependency matrix and probe script before debugging conversion logic.

## ONNX-ML optional tooling in source workflows

Some optional-source workflows create an ONNX-ML model first, then call `hummingbird.ml.convert` on the ONNX `ModelProto`. Common tooling includes `onnxmltools` and `skl2onnx` from the `[onnx]` extra.

Keep the distinction clear:

- This sub-skill owns the source ecosystem dependency questions: LightGBM, XGBoost, Prophet, SparkML, and whether ONNX-ML tooling packages are installed.
- The ONNX/model-I/O sub-skill owns ONNX backend output details, ONNX-ML `ModelProto` conversion details, opset/output naming, saving/loading, and ONNX Runtime inference behavior.
