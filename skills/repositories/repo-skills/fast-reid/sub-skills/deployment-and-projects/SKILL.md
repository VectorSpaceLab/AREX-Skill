---
name: deployment-and-projects
description: "Operate FastReID deployment export surfaces, optional
  ONNX/Caffe/TensorRT dependencies, FastRT, and extension-project registration
  patterns."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FastReID deployment and projects

Use this sub-skill when a FastReID task involves model export, deployment runtime checks, ONNX Runtime/Caffe/TensorRT inference, FastRT C++ TensorRT use, or extension projects such as FastAttr, FastClas, FastDistill, FastFace, FastRetri, FastTune, PartialReID, and NAIC20.

## Route boundaries

- Core model builders, tensor shapes, `DefaultPredictor`-style feature extraction, and checkpoint loading details belong to `../modeling-and-inference/`.
- Shared dataset registry mechanics, built-in dataset layouts, and custom dataset classes belong to `../data-and-datasets/`.
- Standard training/evaluation launch, distributed flags, resume, checkpoints, and evaluator output belong to `../training-and-evaluation/`.
- Source-only package setup, config merge, `_BASE_`, and model-zoo recipe selection belong to `../setup-and-configuration/`.

## Bundled references

- [references/deployment-workflows.md](references/deployment-workflows.md) — use for ONNX, ONNX Runtime, Caffe, TensorRT, and FastRT prerequisites, export/inference interface templates, validation comparisons, and backend limitations.
- [references/project-extensions.md](references/project-extensions.md) — use for the extension-project map, import-before-config rules, registry/config injection patterns, and project-specific dependency notes.
- [references/troubleshooting.md](references/troubleshooting.md) — use when parser help fails before argument parsing, optional deployment packages are missing, exported models disagree, TensorRT engines mismatch devices, Caffe protobuf/helpers are absent, or project imports/configs fail.

## Bundled scripts

- [scripts/check_deployment_dependencies.py](scripts/check_deployment_dependencies.py) — safe optional-dependency probe for `onnx`, `onnxruntime`, `onnxoptimizer`, `onnxsim`, `caffe`, `tensorrt`, `cv2`, and `torch`; use it before export/runtime work or when a deployment entrypoint fails at import time.
- [scripts/project_import_probe.py](scripts/project_import_probe.py) — safe import probe for selected FastReID extension projects; pass an explicit FastReID application checkout with `--repo-root` and one or more `--project` values to classify registration/import failures without training.

## Operating facts

- ONNX, ONNX Runtime, Caffe, TensorRT, PyCUDA, Ray Tune, bcolz, and mxnet are optional stacks, not part of the minimum FastReID CPU inspection environment.
- ONNX export code imports `onnx`, `onnxoptimizer`, and `onnxsim` before argument parsing in this FastReID version; a missing `onnx` package can make `--help` fail before showing parser output.
- TensorRT export code imports `tensorrt` before argument parsing; a missing TensorRT Python package can make `--help` fail before showing parser output.
- TensorRT/Caffe/FastRT workflows are hardware/runtime-gated and should not be claimed verified unless their native runtimes, drivers, model weights, and target devices are available.
- Project packages must usually be imported before merging or building configs that name their datasets, meta-architectures, heads, backbones, or project-only config keys.
