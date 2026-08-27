---
name: optimize-models
description: "Guide coremltools model compression and optimization with Core ML
  package APIs and optional PyTorch optimization APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---
# optimize-models

Use this sub-skill when the task is to compress or optimize an already-converted Core ML model, or to choose an optional PyTorch-side optimization flow before Core ML export. It covers weight quantization, activation quantization with calibration data, palettization, pruning, decompression, metadata discovery, and joint compression choices.

## Route first

- Need to convert an original TensorFlow, PyTorch, sklearn, XGBoost, LightGBM, LibSVM, MIL, or other source model into Core ML before compression? Route to [convert-models](../convert-models/SKILL.md).
- Need to load, save, inspect metadata/specs, rename features, or run `MLModel.predict()` on an artifact? Route to [model-io-and-prediction](../model-io-and-prediction/SKILL.md).
- Need to debug MIL graph passes, custom ops, typed execution, or pass pipelines? Route to [mil-and-debugging](../mil-and-debugging/SKILL.md).
- Already have a Core ML `mlprogram` and want data-free package compression? Stay here and prefer `coremltools.optimize.coreml`.
- Have a PyTorch model and need calibration-data or fine-tuning/QAT-aware compression before Core ML export? Stay here only if PyTorch and the relevant `coremltools.optimize.torch` APIs import in the user's environment.

## Quick decision rules

1. **No training data, Core ML artifact already exists:** use `coremltools.optimize.coreml` functions directly on an `MLModel` package.
2. **Calibration data needed:** use Core ML activation quantization only when you can supply Core ML input dictionaries and can run calibration; otherwise use the optional Torch layerwise/calibration APIs on a PyTorch source model.
3. **Fine-tuning or QAT required:** use optional `coremltools.optimize.torch` optimizers on the PyTorch model, then convert with [convert-models](../convert-models/SKILL.md).
4. **Need the smallest safe first pass:** inspect weights with `get_weights_metadata`, compress only large weight tensors, and set `op_name_configs` or `op_type_configs` to skip fragile layers.
5. **Need to validate artifact behavior:** inspect compressed/decompressed artifacts with [model-io-and-prediction](../model-io-and-prediction/SKILL.md); prediction remains platform-dependent.

## Reference map

- API names, config fields, and safe snippets: [references/api-reference.md](references/api-reference.md)
- End-to-end workflow decision tree: [references/workflows.md](references/workflows.md)
- Compression-specific failures and fixes: [references/troubleshooting.md](references/troubleshooting.md)
- Local smoke helper: [scripts/optimize_coreml_smoke.py](scripts/optimize_coreml_smoke.py)

## Runtime guardrails

- Do not claim `coremltools.optimize.torch` works until importing the relevant submodule succeeds with PyTorch installed and version-compatible.
- Core ML package compression APIs operate on `mlprogram` `MLModel` objects; if the user has a non-`mlprogram` or original model object, route to conversion first.
- Activation quantization and Torch calibration flows need representative data. If no data exists, recommend weight-only Core ML compression first.
- Use `decompress_weights` and metadata/spec inspection to isolate compression-induced failures before changing the original conversion settings.
