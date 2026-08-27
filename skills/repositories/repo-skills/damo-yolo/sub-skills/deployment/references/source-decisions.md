# Deployment source-script decisions

| Source artifact | Decision | Bundled replacement or runtime owner | Rationale |
|---|---|---|---|
| `tools/converter.py` | Adapt/wrap | `scripts/export_onnx_safe.py` plus workflow/CLI references | The ONNX export path is useful and can be made self-contained by importing installed `damo` APIs directly. TensorRT engine build is documented but not bundled because it depends on optional system libraries. |
| `tools/trt_eval.py` | Reference-only | `references/workflows.md`, `references/cli-reference.md`, `references/troubleshooting.md` | The evaluator imports TensorRT at module import time and requires a `.trt` engine, COCO data, and CUDA/TensorRT runtime. |
| `tools/calibrator.py` | Reference-only | `references/workflows.md`, `references/troubleshooting.md` | INT8 calibration requires many calibration images, CUDA memory allocation, TensorRT, and PyCUDA. It is not a safe default bundled executable. |
| `tools/partial_quantization/partial_quant.py` | Reference-only with path warning | `references/workflows.md`, `references/troubleshooting.md` | The source script has sibling-module and TensorRT import assumptions and launches expensive calibration/export/eval work. It is documented rather than copied as a default helper. |
| `damo/base_models/core/end2end.py` | Distilled/API reuse | `scripts/export_onnx_safe.py` and references | The `End2End` wrapper is importable from the installed package and is reused by the bundled ONNX exporter. |
| `damo/utils/model_utils.py` | Distilled/API reuse | `scripts/export_onnx_safe.py` | `replace_module()` and `get_model_info()` are reused for converter-equivalent behavior. |

The generated deployment sub-skill deliberately separates ONNX export, which can be verified with ordinary Python dependencies, from TensorRT/INT8 workflows, which require backend-specific runtime evidence before being claimed as operational.
