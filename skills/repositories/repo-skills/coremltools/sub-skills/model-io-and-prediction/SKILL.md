---
name: model-io-and-prediction
description: "Load, save, inspect, edit, package, and predict with Core ML model
  artifacts using MLModel and spec utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Model I/O and Prediction

Use this sub-skill when the task is about operating on existing Core ML artifacts: `.mlmodel`, `.mlpackage`, specs, metadata, feature descriptions, prediction dictionaries, compute-unit selection, compiled models, or stateful prediction boundaries.

Start here:

- Use [references/api-reference.md](references/api-reference.md) for the exact API contracts and platform gates.
- Use [references/workflows.md](references/workflows.md) for copyable load/edit/save/package/predict workflows.
- Use [references/troubleshooting.md](references/troubleshooting.md) when artifact loading, prediction, packaging, compute units, or states fail.
- Use [scripts/inspect_mlmodel.py](scripts/inspect_mlmodel.py) to inspect a `.mlmodel` or `.mlpackage` spec without invoking Core ML prediction.

Operating rules:

1. Prefer spec-only inspection with `coremltools.models.utils.load_spec` when prediction is not required, especially on Linux.
2. Treat `MLModel.predict`, `CompiledMLModel`, compute devices, compute plans, and stateful runtime calls as macOS Core ML runtime features unless the environment proves otherwise.
3. Preserve artifact form: neural-network-style specs may be saved as `.mlmodel`; `mlprogram` models with external weights normally need `.mlpackage` and a valid `weights_dir`.
4. Prediction inputs are dictionaries keyed by Core ML feature names. Use NumPy arrays for multi-array inputs and PIL images for image inputs.
5. Route source model conversion to `../convert-models/`, compression and weight optimization to `../optimize-models/`, and MIL/debug utilities/custom passes to `../mil-and-debugging/`.
