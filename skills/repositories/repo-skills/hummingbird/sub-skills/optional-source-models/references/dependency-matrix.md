# Optional Dependency Matrix

Hummingbird's base package covers core scikit-learn-to-tensor conversion. The source ecosystems in this sub-skill require optional dependency groups and are intentionally absent in many minimal environments.

## Extras and what they enable

| Install extra | Main packages pulled by the extra | Enables | Notes |
| --- | --- | --- | --- |
| Base `hummingbird-ml` | `numpy`, `onnx`, `onnxconverter-common`, `scipy`, `scikit-learn`, `torch`, `psutil`, `dill`, `protobuf` | Core conversion to PyTorch/TorchScript when backend requirements are met | Base `onnx` is not the same as the Hummingbird ONNX backend being available; the ONNX backend is gated by ONNX Runtime. |
| `hummingbird-ml[onnx]` | `onnxruntime>=1.0.0,<1.18.0`, `onnxmltools>=1.6.0,<=1.12.0`, `skl2onnx>=1.7.0,<=1.16.0` | ONNX backend output, ONNX Runtime prediction, and ONNX-ML tooling workflows | Use with LightGBM/XGBoost/Prophet only when ONNX output or ONNX-ML interop is required. |
| `hummingbird-ml[extra]` | `xgboost>=0.90,<2.0.0`, `lightgbm>=2.2`, `holidays`, `prophet` | LightGBM, XGBoost, and Prophet source model workflows | These packages can require compiled native dependencies such as OpenMP or cmake. |
| `hummingbird-ml[sparkml]` | `pyspark>=2.4.4`, `pyarrow>1.0` | SparkML source model and Spark DataFrame workflows | Requires a working JVM/Spark runtime in addition to Python packages. |
| `hummingbird-ml[benchmark]` | `[onnx]` + `[extra]` + `memory-profiler` + `psutil` | Benchmark-style source packages and ONNX tooling in one environment | Avoid as the default install for routine conversion; it is broader than most user tasks need. |

Use shell quotes around extras in shells that treat brackets specially:

```bash
python -m pip install "hummingbird-ml[extra]"
python -m pip install "hummingbird-ml[onnx]"
python -m pip install "hummingbird-ml[extra,onnx]"
python -m pip install "hummingbird-ml[sparkml]"
```

## Import-time support gates

Hummingbird populates support lists and backend aliases by importing optional packages. Missing packages usually mean the relevant support list is empty, not that the core package is broken.

| Gate | Populated when | What to check |
| --- | --- | --- |
| `lgbm_operator_list` | `lightgbm` imports successfully | `LGBMClassifier`, `LGBMRanker`, `LGBMRegressor`, and `Booster` can be recognized. |
| `xgb_operator_list` | `xgboost` imports and exposes a sufficiently recent native library API | `XGBClassifier`, `XGBRanker`, and `XGBRegressor` can be recognized. |
| `sparkml_operator_list` | `pyspark` imports successfully | SparkML `Bucketizer`, `VectorAssembler`, and `LogisticRegressionModel` can be recognized. |
| `prophet_operator_list` | `from prophet import Prophet` succeeds | Prophet models can be recognized by the sklearn-style parser. |
| `onnxml_operator_list` | `onnxruntime` imports successfully | ONNX-ML operator names are enabled for ONNX input model conversion. |
| ONNX backend alias | `onnxruntime` imports successfully and `onnx` is importable | `backend="onnx"` can be selected by `hummingbird.ml.convert`. |
| TVM backend alias | `tvm` imports successfully | TVM source/output questions belong in the advanced backends sub-skill. |

If a package is installed after Hummingbird has already been imported, restart the Python process before rechecking these lists.

## Recommended combinations

| User goal | Minimal dependency target | Why |
| --- | --- | --- |
| LightGBM/XGBoost to PyTorch | `[extra]` | Adds the source libraries; base already includes PyTorch. |
| LightGBM/XGBoost to ONNX | `[extra,onnx]` | Adds source libraries plus ONNX Runtime/tooling. |
| SparkML pipeline to PyTorch | `[sparkml]` plus a working JVM/Spark runtime | Adds PySpark and pyarrow; conversion needs Spark DataFrames/model objects. |
| Prophet trend to PyTorch | `[extra]` | Adds Prophet and holidays. |
| Prophet to ONNX | `[extra,onnx]` | Adds Prophet plus ONNX Runtime; ONNX conversion should use numeric timestamp inputs. |
| ONNX-ML model produced by external tooling | `[onnx]` and whichever package creates the ONNX-ML model | Hummingbird consumes an ONNX `ModelProto`; creating one may require tools such as `onnxmltools` or `skl2onnx`. |

## Probe before debugging

Run the bundled probe to produce a machine-readable dependency snapshot without installing anything:

```bash
python scripts/check_optional_sources.py --json
```

The probe reports import success, package versions when available, backend aliases, and support-list counts.
