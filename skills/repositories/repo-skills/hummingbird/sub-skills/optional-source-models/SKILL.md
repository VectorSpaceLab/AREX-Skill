---
name: optional-source-models
description: "Use Hummingbird with optional source model ecosystems: LightGBM,
  XGBoost, SparkML, Prophet, and optional ONNX-ML tooling dependency checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Optional Source Models

Load this sub-skill when a Hummingbird task involves optional source-model ecosystems or optional tooling dependencies, especially:

- LightGBM to PyTorch/TorchScript/ONNX.
- XGBoost `XGBClassifier`, `XGBRegressor`, or `XGBRanker`, particularly when `test_input` or feature-count inference is failing.
- SparkML models, transformers, or pipelines that use Spark DataFrames as conversion input.
- Prophet conversion to PyTorch or ONNX.
- Dependency questions around `hummingbird-ml[extra]`, `hummingbird-ml[sparkml]`, `hummingbird-ml[onnx]`, or `hummingbird-ml[benchmark]`.
- Optional-library failures such as OpenMP/libgomp/libomp/cmake errors.

## Start here

1. Check dependency availability with the bundled probe:
   [`scripts/check_optional_sources.py`](scripts/check_optional_sources.py).
2. Use the source-family workflows and caveats in
   [`references/optional-source-models.md`](references/optional-source-models.md).
3. Use the extras and import-gate matrix in
   [`references/dependency-matrix.md`](references/dependency-matrix.md).
4. Use OS-specific and source-family troubleshooting in
   [`references/troubleshooting.md`](references/troubleshooting.md).

## Route elsewhere

- For core `hummingbird.ml.convert` / `convert_batch` syntax on ordinary scikit-learn-style models, load [`../core-conversion/SKILL.md`](../core-conversion/SKILL.md).
- For ONNX backend output, ONNX-ML source-model details, model save/load, and container I/O, load [`../onnx-and-model-io/SKILL.md`](../onnx-and-model-io/SKILL.md).
- For CUDA, TVM, TorchScript performance tuning, threading, and batch-shape performance issues, load [`../advanced-backends-and-performance/SKILL.md`](../advanced-backends-and-performance/SKILL.md).

## Important constraints

- Optional source packages are not part of the minimal Hummingbird runtime. Treat missing LightGBM, XGBoost, Prophet, SparkML, and TVM as expected until the user requests those workflows.
- Hummingbird builds optional supported-operator lists at Python import time. If optional packages were installed after importing Hummingbird, restart the Python process before diagnosing missing converters.
- Do not claim optional source-family native verification unless the user's environment actually has the relevant optional packages and the conversion has been exercised.
