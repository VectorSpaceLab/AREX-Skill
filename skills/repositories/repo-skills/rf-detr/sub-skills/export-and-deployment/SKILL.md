---
name: export-and-deployment
description: "Export and deploy RF-DETR models to ONNX, TensorRT, TFLite,
  ExecuTorch, CoreML, and Roboflow with backend constraints and safe option
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# RF-DETR export and deployment

Use this sub-skill when the task is about exporting RF-DETR models or choosing a deployment artifact. Do not use it for ordinary prediction, training, dataset validation, or repository maintenance.

## Route quickly

- For the full `RFDETR.export(...)` contract, format aliases, backend compatibility, file naming, and optional dependencies, read [export-reference.md](references/export-reference.md).
- For practical export/deploy choices across ONNX, TensorRT, TFLite, ExecuTorch, CoreML, inference-models, and Roboflow, read [deployment-workflows.md](references/deployment-workflows.md).
- For invalid combinations, missing extras, platform constraints, output-name surprises, calibration/import-order issues, and optimized-model failures, read [troubleshooting.md](references/troubleshooting.md).
- Before exporting, run [inspect_export_options.py](scripts/inspect_export_options.py) to inspect installed optional packages, validate shape divisibility, check static format/backend constraints, and preview output filename stems without exporting a model.

## Default decision rules

1. Prefer `format="onnx"` as the stable baseline unless the downstream runtime explicitly requires another artifact.
2. Do not export `format="tensorrt"` for inference-models consumers; give inference-models a plain ONNX or checkpoint path and let it build/manage its own TensorRT engine.
3. Treat TensorRT engines as non-portable build-machine artifacts tied to the local GPU architecture, TensorRT version, and precision.
4. Treat TFLite, ExecuTorch, and native CoreML export as experimental and dependency-sensitive; use isolated environments per backend.
5. Reject `dynamic_batch=True` for `format="executorch"` and `format="coreml"`; export one fixed-batch artifact per target batch size.
6. For ExecuTorch QNN, require `backend="qnn"` plus a target `soc` such as `SM8650`; do not assume the pip wheel contains the QNN delegate.
7. For native CoreML, use `format="coreml"`; for the ExecuTorch CoreML delegate, use `format="executorch", backend="coreml"`. These are different artifact families.

## Minimal safe preflight

```bash
python scripts/inspect_export_options.py --variant rfdetr-small --format onnx --shape 512 512
python scripts/inspect_export_options.py --variant rfdetr-small --format executorch --backend qnn --soc SM8650 --shape 512 512
```

The script is read-only: it imports metadata where available, reports optional-package readiness, validates options, and previews expected filename stems. It does not instantiate RF-DETR, download weights, trace models, or write export artifacts.
