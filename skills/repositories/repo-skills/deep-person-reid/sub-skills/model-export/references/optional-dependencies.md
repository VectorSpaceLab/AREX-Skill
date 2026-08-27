# Optional dependencies

This sub-skill must stay honest about what is actually installed.
The minimum verified environment for the distillation work did **not** include the export frameworks below, so the bundled helper should treat them as optional and lazy-load them only when the user asks for the corresponding conversion step.

## Dependency matrix

| Package / tool | Used for | Needed for `--help` or `--dry-run`? | Notes |
| --- | --- | --- | --- |
| `onnx` | Loading and checking the exported ONNX graph | No | Required for actual ONNX export and validation. |
| `onnx-simplified` / `onnxsim` | Simplifying the ONNX graph after export | No | The source exporter imports `onnxsim`; the requirements comment names the simplifier as `onnx-simplified`. |
| `openvino-dev` | ONNX → OpenVINO conversion / Model Optimizer | No | Needed only when `--include openvino` or `--include tflite` is requested. |
| `openvino2tensorflow` | OpenVINO → TFLite-style artifact chain | No | Needed only when `--include tflite` is requested. |
| `tensorflow` | Runtime dependency for the TFLite chain | No | Keep this explicit because the converter may import TensorFlow during model export. |
| `tensorflow_datasets` | Convenience dependency used by parts of the TFLite toolchain | No | Optional but listed in the repo comments; mention it separately so it is not silently assumed. |
| `pandas` | Source `tools/export.py` format table | No | The original exporter imports pandas at top level; the bundled helper should not depend on it for `--help` or `--dry-run`. |

## What the bundled helper should do

- Print a dependency summary before starting any conversion work.
- Let `--help` and `--dry-run` finish without importing any export backend.
- Fail with a clear message when a requested optional package is missing.
- Keep ONNX export usable without forcing OpenVINO or TensorFlow packages into the environment.

## What not to imply

- Do not imply that OpenVINO or TensorFlow are already installed in the minimum environment.
- Do not imply that a TFLite artifact exists unless the OpenVINO and TensorFlow steps were actually run.
- Do not imply that the source exporter is dependency-light just because the help flag works in one environment.
