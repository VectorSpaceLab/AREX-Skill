---
name: export
description: "Routes Chainer model export workflows for ONNX-Chainer and Caffe."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Export

Use this sub-skill when the user wants to export a Chainer model to ONNX or Caffe, generate export testcases, or debug conversion failures.

## Typical requests

- "Export this model to ONNX."
- "How do I generate ONNX testcases?"
- "Why does `onnx_chainer.export` fail on my model?"
- "How do I export a Chainer model to Caffe?"
- "Why is `chainer_model.prototxt` or `chainer_model.caffemodel` missing?"

## Read these first

- `references/workflows.md` for the export flow.
- `references/api-reference.md` for the exact export signatures and limits.
- `references/troubleshooting.md` for exporter-specific failure modes.

## Use this script

- `../../scripts/export_smoke.py` for a tiny ONNX and Caffe export check.

## Include here

- `onnx_chainer.export(...)` and `onnx_chainer.export_testcase(...)`
- ONNX opset version limits and named inputs / outputs
- Caffe export via `chainer.exporters.caffe.export(...)`
- Export validation, file layout, and unsupported-layer debugging

## Route elsewhere

- Ordinary model training or serialization -> `../training/`
- MPI / distributed / multi-node export scenarios -> `../distributed/`
- ChainerX-specific model behavior -> `../chainerx/`

## Quick mental model

A normal export workflow is:

1. Build a tiny model or load a trained model.
2. Feed a representative input.
3. Export the model to ONNX or Caffe.
4. Validate that the target files exist and the exported graph is structurally valid.

When you only need a fast check, use the bundled smoke script.
