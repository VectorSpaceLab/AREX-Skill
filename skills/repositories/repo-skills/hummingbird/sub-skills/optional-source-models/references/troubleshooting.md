# Optional Source Troubleshooting

Use this table after running `scripts/check_optional_sources.py`. Missing optional source packages should be treated as expected unless the user specifically requested that source family.

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `To convert LightGBM models you need to install LightGBM (or python -m pip install hummingbird-ml[extra])` | `lightgbm` is not installed or failed to import. | Install the `[extra]` group or a compatible LightGBM wheel, then restart Python before rechecking Hummingbird support lists. |
| `To convert XGBoost models you need to install XGBoost (or python -m pip install hummingbird-ml[extra])` | `xgboost` is missing, too old, or its native library does not expose the required API. | Install `hummingbird-ml[extra]` or `xgboost>=0.90,<2.0.0`; restart Python. If native library errors persist, reinstall XGBoost after fixing system build/runtime dependencies. |
| `ONNX backend` missing even though `onnx` imports | Hummingbird's ONNX backend and ONNX-ML operator list are gated by `onnxruntime`, not only the `onnx` package. | Install `hummingbird-ml[onnx]`; verify `onnxruntime`, `onnxmltools`, and `skl2onnx` with the probe. Route ONNX output/model-I/O details to the ONNX sub-skill. |
| Optional package installed but Hummingbird still reports no supported operators | Hummingbird support lists are populated at import time. | Restart the Python process and import again. Avoid diagnosing stale `hummingbird.ml.supported` state inside a long-running interpreter. |
| `XGBoost converter is not able to infer the number of input features` | The XGBoost object did not expose feature count metadata and no usable 2-D NumPy `test_input` was provided. | Pass representative input such as `X[:1].astype(np.float32)` to `hummingbird.ml.convert(model, "torch", X[:1])`. If needed, pass `extra_config={"n_features": X.shape[1]}` and validate predictions. |
| XGBoost conversion works for classifier but fails for regressor/ranker | XGBoost classifiers and regressors expose feature metadata differently across versions. | Always pass a 2-D `test_input` for XGBoost regressors/rankers and tracing backends. Keep column order and feature names aligned with the fitted model. |
| LightGBM classifier with `boosting_type="rf"` fails with `Unable to directly convert this model. It should be converted into ONNX first.` | Direct LightGBM tree conversion does not support this random-forest mode. | Use an ONNX-ML interop path with ONNX tooling, then route ONNX-ML conversion/output details to the ONNX sub-skill. Validate probabilities carefully. |
| macOS LightGBM import fails with `Library not loaded: ... libomp.dylib` | LightGBM's native library cannot find OpenMP. | Install OpenMP for macOS, commonly `brew install libomp`, then reinstall or re-import LightGBM. |
| Linux LightGBM import fails with `libgomp.so.1: cannot open shared object file` | GNU OpenMP runtime is missing. | On Yum-based systems install `libgomp` with the system package manager. On other Linux distributions use the equivalent GNU OpenMP runtime package, then retry the LightGBM import. |
| XGBoost install/build fails with `cmake: command not found` | Building XGBoost from source needs cmake. | Install cmake with the OS package manager, then retry XGBoost installation. On macOS this is commonly `brew install cmake`. |
| `pyspark` imports fail or Spark session cannot start | `[sparkml]` Python packages are missing or the JVM/Spark runtime is not healthy. | Install `hummingbird-ml[sparkml]`, ensure Java is installed, then create a small local Spark session before attempting Hummingbird conversion. |
| SparkML conversion raises `Unrecognized data type` | Spark DataFrame fields include a type outside Hummingbird's supported conversion path. | Convert or select input columns as numeric scalars, arrays, or vector columns. Pass a representative Spark DataFrame as `test_input` so Hummingbird can infer names and shapes. |
| SparkML prediction parity fails after conversion | The Spark DataFrame used for conversion and the NumPy/pandas data used for Hummingbird prediction do not have matching columns or order. | Align column names/order with the fitted Spark pipeline. For pipelines with `VectorAssembler`, compare against the same assembled feature order. |
| Prophet import or fit is slow/failing | Prophet is an optional heavy dependency and may require compiled/statistical runtime components. | Confirm `prophet` and `pandas` imports first. Keep Hummingbird debugging separate from source-model fit/install issues. |
| Prophet conversion fails with `Growth function ... not supported yet` | The Hummingbird Prophet converter supports linear growth. | Use a linear-growth Prophet model for Hummingbird conversion or keep the model in Prophet for unsupported growth functions. |
| Prophet ONNX conversion input fails | ONNX conversion needs numeric timestamp input, not a pandas datetime DataFrame. | Convert datetimes to Unix-second numeric arrays before `convert(model, "onnx", future_np)`, and ensure `onnxruntime` is installed. |

## Minimal triage sequence

1. Run `python scripts/check_optional_sources.py --json`.
2. Confirm the relevant optional package and Hummingbird support list are populated.
3. Restart Python if installation changed during the session.
4. For XGBoost and tracing-style backends, retry with a 2-D representative `test_input`.
5. For LightGBM/XGBoost native library errors, fix OS-level OpenMP/cmake dependencies before re-running Hummingbird conversion.
6. For ONNX details, switch to the ONNX/model-I/O sub-skill after dependency availability is confirmed.
