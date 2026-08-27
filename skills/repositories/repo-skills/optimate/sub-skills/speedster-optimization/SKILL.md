---
name: speedster-optimization
description: "Guides Speedster inference optimization workflows,
  compiler/backend selection, save/load, and troubleshooting for optimized
  models."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Speedster optimization

Use this sub-skill when the user wants to accelerate an existing model, choose `optimize_model` parameters, save or load an optimized learner, or understand why a compiler/backend path was selected or skipped.

## Triggers

- Optimize a PyTorch, TensorFlow, ONNX, Hugging Face, or Diffusers model.
- Choose `metric_drop_ths`, `optimization_time`, `dynamic_info`, `ignore_compilers`, `ignore_compressors`, or `device`.
- Save or reload an optimized model.
- Interpret telemetry, latency summaries, or backend-specific warnings.

## Read next

- `references/api-reference.md` for verified function signatures, accepted inputs, and return behavior.
- `references/workflows.md` for end-to-end recipes and parameter choices.
- `references/framework-recipes.md` for framework-specific notes and compiler/backend selection.
- `references/troubleshooting.md` for install/import/backend and data-format failures.
- `../nebullvm-backends/SKILL.md` when the question is really about `DataManager`, device parsing, compiler lists, or optional dependency probes.
- `scripts/speedster_quick_probe.py` when you want a safe import/signature/backend smoke probe.

## What to include

- `optimize_model`, `save_model`, and `load_model`.
- Data input shapes and dynamic-shape guidance.
- Device selection and backend selection.
- Compatible compiler names and optional dependencies.
- Telemetry opt-out and save/load behavior.

## What to exclude

- Full compiler installation procedures that belong to the NebullVM backend support sub-skill.
- Long notebook or source-repo example paths.
- Heavy benchmark runs and large optimization sweeps.

## Quick decision rule

If the user asks “how do I make this model faster?”, start here. If the user asks “which backend/compiler package should I install?”, read the NebullVM backend sub-skill next.
