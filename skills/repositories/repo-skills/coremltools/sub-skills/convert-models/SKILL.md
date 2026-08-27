---
name: convert-models
description: "Convert PyTorch, TensorFlow, MIL, scikit-learn, XGBoost, LightGBM,
  and LibSVM models to Core ML with coremltools."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Convert Models

Use this sub-skill when the task is to convert a trained source model or source-model artifact into a Core ML `MLModel` using `coremltools`.

## Route here for

- Unified converter work with `ct.convert(...)` for PyTorch, TensorFlow, and MIL source programs.
- Input/output typing with `ct.TensorType`, `ct.ImageType`, flexible shapes, output names, and `ct.ClassifierConfig`.
- Deployment target and model-format choices: `minimum_deployment_target`, `convert_to`, `compute_precision`, `compute_units`, `package_dir`, `skip_model_load`, `pass_pipeline`, and PyTorch `states`.
- Classic converter entry points for scikit-learn, XGBoost, LightGBM, and LibSVM when their optional dependencies are installed and compatible.
- Diagnosing conversion-time errors before saving or prediction.

## Do not handle here

- Core ML model save/load/predict details, `MLModel` metadata editing, compiled models, or platform-specific prediction setup: route to [model-io-and-prediction](../model-io-and-prediction/).
- Hand-authored MIL graph construction, custom MIL passes, graph debugging utilities, and low-level MIL inspection: route to [mil-and-debugging](../mil-and-debugging/).
- Compression after conversion, post-training quantization, palettization, pruning, or deployment optimization workflows: route to [optimize-models](../optimize-models/). This sub-skill only covers converter-time `pass_pipeline` choices.

## Operating workflow

1. Identify the source family and dependency gate. Use `ct.convert` for PyTorch, TensorFlow, and MIL; use the classic converter namespace for scikit-learn, XGBoost, LightGBM, and LibSVM.
2. Choose source artifact format and conversion path from [workflows](references/workflows.md).
3. Specify inputs, outputs, classifier metadata, deployment target, model format, precision, compute units, and optional pass pipeline using [API reference](references/api-reference.md).
4. Convert in memory and inspect the returned object/spec before saving or predicting. For save/load/predict instructions, route to [model-io-and-prediction](../model-io-and-prediction/).
5. If conversion fails, use [troubleshooting](references/troubleshooting.md) before changing source-model semantics.

## Bundled script

- [`scripts/convert_torch_toy.py`](scripts/convert_torch_toy.py): creates a tiny `torch.nn.Module`, traces it, converts with an explicit named `TensorType`, and saves a user-provided `.mlpackage`. It is a smoke/demo helper and is dependency-gated on both PyTorch and coremltools.

Start with [workflows](references/workflows.md) for task recipes and [API reference](references/api-reference.md) for argument-level constraints.
