---
name: automatic-colorization
description: "Run ECCV16 and SIGGRAPH17 automatic image colorization to saved
  PNG outputs with CPU/CUDA and download troubleshooting guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 2-Clause
---

# Automatic Colorization

Use this sub-skill when the task is to colorize an input image end-to-end with the ECCV16 and/or SIGGRAPH17 automatic colorizers, save PNG outputs, select CPU or CUDA execution, or debug release-style model/download/output failures.

## Route

- For complete command recipes, setup assumptions, CPU/CUDA behavior, output names, validation checks, and the release-workflow mapping, use [references/workflows.md](references/workflows.md).
- For dependency, import-path, pretrained-weight download, CUDA, image-read, output-write, and headless execution failures, use [references/troubleshooting.md](references/troubleshooting.md).
- For the bundled headless helper, use [scripts/colorize_image.py](scripts/colorize_image.py).
- For low-level Python APIs, tensor shapes, preprocessing details, or SIGGRAPH hint inputs, route to the sibling [../python-api/](../python-api/) skill instead of expanding that detail here.

## Operating boundaries

- Supported: automatic colorization with `eccv16`, `siggraph17`, or both; local image input; saved PNG outputs; CPU, CUDA, or auto device selection; pretrained weights by default; no-GUI/headless operation.
- Not supported here: historical Caffe training, representation-learning experiments, training workflows, or detailed programmatic tensor/hint usage.
- Do not use `--skip-pretrained` for quality colorization. It is only for smoke/API checks when downloads are intentionally disabled.
