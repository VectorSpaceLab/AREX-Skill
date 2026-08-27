---
name: core-conversion
description: "Convert already-trained scikit-learn-style models with Hummingbird
  convert and convert_batch, then validate CPU PyTorch prediction parity."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core conversion

Use this sub-skill when the task is to convert an already-trained scikit-learn-style estimator with `hummingbird.ml.convert` or `hummingbird.ml.convert_batch`, especially to the CPU PyTorch backend, and quickly verify that Hummingbird predictions match the source estimator.

## Read when

- The user asks to "convert sklearn model with Hummingbird", "use `hummingbird.ml.convert`", or "compile a trained sklearn estimator to PyTorch".
- The user asks for fixed-batch or uneven-row inference with `convert_batch`.
- The user needs quick prediction parity checks between the original estimator and the converted container.
- The user sees conversion failures such as `NotFittedError`, `MissingBackend`, `MissingConverter`, or a backend requiring `test_input`.

## Do not use as the only source for

- Detailed scikit-learn operator and pipeline coverage; route to `../sklearn-pipelines-and-operators/SKILL.md`.
- ONNX output details, ONNX-ML source models, save/load, and container integrity workflows; route to `../onnx-and-model-io/SKILL.md`.
- LightGBM, XGBoost, SparkML, Prophet, and optional source-package dependency handling; route to `../optional-source-models/SKILL.md`.
- CUDA, TVM, TorchScript deployment tuning, threading, benchmarking, and deep performance work; route to `../advanced-backends-and-performance/SKILL.md`.

## Operating path

1. Confirm the estimator is trained/fitted and belongs to a supported source family.
2. Pick the smallest backend that satisfies the request: usually `"torch"`/`"pytorch"` for CPU parity work.
3. Provide representative `test_input` when the backend needs tracing (`"torch.jit"`, `"torchscript"`, `"onnx"`, TVM) or when using `convert_batch`.
4. Convert with `convert(...)` for ordinary inference or `convert_batch(...)` for fixed batch-size/remainder workflows.
5. Validate method-level parity (`predict`, `predict_proba`, `transform`, `decision_function`, or `score_samples`) on held-out or representative input before replacing the source estimator.

## Bundled references and helper

- [Conversion workflows](references/conversion-workflows.md) covers normal `convert`, fixed-batch `convert_batch`, parity checks, and representative examples.
- [API reference](references/api-reference.md) summarizes signatures, backend aliases, `test_input`, `device`, `extra_config`, and container behavior.
- [Troubleshooting](references/troubleshooting.md) maps common exceptions and parity failures to corrective actions and sibling sub-skills.
- [Synthetic conversion smoke](scripts/convert_sklearn_smoke.py) runs a deterministic tiny scikit-learn conversion check with optional JSON output.
