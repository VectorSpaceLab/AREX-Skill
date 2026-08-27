---
name: deployment-export
description: "Export, inspect, and benchmark Detectron2 models with TorchScript,
  optional Caffe2/ONNX paths, and safe command construction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Detectron2 Deployment Export

Use this sub-skill when a task involves exporting a Detectron2 model for deployment, choosing between tracing/scripting/Caffe2 tracing, inspecting TorchScript IR, preparing ONNX/Caffe2 attempts, building export commands, analyzing FLOPs/parameters/activations, or planning benchmark runs.

## Fast Routing

- Read [references/export-workflows.md](references/export-workflows.md) to choose `tracing`, `scripting`, or optional `caffe2_tracing`, and to understand format/runtime limits.
- Use [scripts/export_command_builder.py](scripts/export_command_builder.py) to print a validated export command without importing Detectron2, loading weights, building a model, or writing output files.
- Read [references/analysis-and-benchmarking.md](references/analysis-and-benchmarking.md) before FLOP, activation, parameter, structure, data-loader, train, or eval benchmark work.
- Use [scripts/analyze_command_builder.py](scripts/analyze_command_builder.py) to print a validated model-analysis command without building a model.
- Read [references/model-conversion.md](references/model-conversion.md) for TorchScript input schema, Caffe2/ONNX caveats, and torchvision checkpoint conversion guidance.
- Read [references/troubleshooting.md](references/troubleshooting.md) when export fails, optional dependencies are missing, model families are unsupported, sample inputs are absent, or benchmark results are hardware-sensitive.

## Safe Defaults

- Prefer `--export-method tracing --format torchscript` for a first deployable artifact when a valid sample image or dataset sample is available.
- Prefer `--export-method scripting --format torchscript` when dynamic batch size is required and the model family is scriptable.
- Treat `caffe2_tracing`, Caffe2 protobuf, and ONNX as optional paths that require extra dependency and runtime checks.
- Keep export and analysis dry-run planning separate from actual execution; the bundled scripts print commands only.
- Ask before running export, evaluation, benchmark, or analysis commands that load weights, touch datasets, write large output directories, or use GPU/accelerator resources.

## Boundary Notes

This sub-skill owns deployment export method/format selection, `TracingAdapter`, `scripting_with_instances`, `dump_torchscript_IR`, optional Caffe2/ONNX planning, command construction, model analysis, and benchmark safety. Route config discovery and model-zoo checkpoint selection to ../configuration-model-zoo/. Route dataset registration and loaders to ../data-datasets/. Route training and evaluator semantics to ../training-evaluation/. Route custom trace/script compatibility design for new architectures or project extensions to ../extension-projects/.
