---
name: hummingbird
description: "Use Hummingbird to convert trained traditional ML models into
  tensor backends, validate parity, choose backends, and troubleshoot optional
  dependencies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Hummingbird repo skill

Use this skill when a task involves the `hummingbird-ml` Python package: converting trained classical ML models into PyTorch, TorchScript, ONNX, or TVM-style tensor computations; validating prediction parity; saving/loading converted containers; or diagnosing optional model-source/back-end dependencies.

## Quick identification

- Import package: `hummingbird`, `hummingbird.ml`.
- Distribution: `hummingbird-ml`.
- Core APIs: `hummingbird.ml.convert(...)`, `hummingbird.ml.convert_batch(...)`, and `hummingbird.ml.load(...)`.
- Typical source models: scikit-learn estimators/pipelines, optional LightGBM/XGBoost/Prophet sklearn-style models, optional SparkML models, and ONNX-ML `ModelProto` inputs.
- Typical targets: `"torch"`/`"pytorch"`, `"torch.jit"`/`"torchscript"`, `"onnx"`, and optional `"tvm"`.

## Install and smoke-check

Install the package and extras that match the user's workflow:

```bash
python -m pip install hummingbird-ml
python -m pip install 'hummingbird-ml[onnx]'      # ONNX output or ONNX-ML input workflows
python -m pip install 'hummingbird-ml[extra]'     # LightGBM, XGBoost, Prophet source workflows
python -m pip install 'hummingbird-ml[sparkml]'   # SparkML source workflows
```

Run the bundled environment probe before deeper troubleshooting:

```bash
python scripts/check_hummingbird_env.py --json
```

Read [repo provenance](references/repo-provenance.md) when deciding whether this skill matches the current package version or should be refreshed.

## Route by task

| User task shape | Read next |
| --- | --- |
| Build a basic `convert(...)` call, convert a fitted sklearn estimator to PyTorch, or validate predictions quickly | [core conversion](sub-skills/core-conversion/SKILL.md) |
| Use `convert_batch`, handle uneven fixed-batch inference, or recover from `NotFittedError`, `MissingBackend`, or `MissingConverter` in the core path | [core conversion](sub-skills/core-conversion/SKILL.md) |
| Decide whether a scikit-learn estimator, transformer, `Pipeline`, `ColumnTransformer`, or tree strategy is supported | [sklearn pipelines and operators](sub-skills/sklearn-pipelines-and-operators/SKILL.md) |
| Work with ONNX output, ONNX-ML source models, `onnxruntime`, `onnxmltools`, `skl2onnx`, saved containers, digests, or `override_flag` | [ONNX and model I/O](sub-skills/onnx-and-model-io/SKILL.md) |
| Convert LightGBM, XGBoost, SparkML, or Prophet models, or diagnose optional-library install/import failures | [optional source models](sub-skills/optional-source-models/SKILL.md) |
| Choose TorchScript, TVM, CUDA/GPU, threading, batching, or benchmark/performance options | [advanced backends and performance](sub-skills/advanced-backends-and-performance/SKILL.md) |

## Core operating rules

1. Hummingbird converts trained models. If the source estimator must be fitted first, route the user to fit/validate it before calling `convert`.
2. Prefer `backend="torch"` for the lowest-friction CPU parity check unless the user explicitly needs ONNX, TorchScript, TVM, or GPU execution.
3. Provide representative `test_input` when tracing/exporting (`torch.jit`, ONNX, TVM), when shapes are not obvious, or when source packages such as XGBoost need feature-count inference.
4. Validate parity on the method the downstream code will call: `predict`, `predict_proba`, `transform`, `decision_function`, or `score_samples`.
5. Treat CUDA, TVM, SparkML, LightGBM, XGBoost, and Prophet as optional surfaces. Check imports and backend availability before promising runtime behavior.
6. Do not use benchmark-scale scripts as smoke tests. Use bundled smoke/probe helpers and tiny data unless the user explicitly requests a benchmark run.

## Shared references and helpers

- [API overview](references/api-overview.md) summarizes package entry points, backend aliases, constants, containers, and dependency surfaces.
- [Cross-cutting troubleshooting](references/troubleshooting.md) covers install/import, backend, optional dependency, parity, and artifact-loading failures.
- [Environment checker](scripts/check_hummingbird_env.py) reports package version, available backend aliases, optional imports, and torch CUDA status without installing anything.

## Verification note

This skill was generated with CPU PyTorch and ONNX workflows verified. CUDA, TVM, SparkML, LightGBM, XGBoost, and Prophet are documented as optional surfaces unless the active environment separately proves those dependencies/backends.
