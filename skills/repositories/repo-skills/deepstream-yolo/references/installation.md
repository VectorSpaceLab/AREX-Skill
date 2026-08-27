# Installation and environment prerequisites

This repository is a DeepStream deployment and conversion project, not a standalone Python package. The runtime skill should assume two different environments:

1. **DeepStream runtime host** for building and running `deepstream-app`.
2. **Python inspection environment** for model export helpers and CLI help checks.

## DeepStream runtime prerequisites

- NVIDIA GPU host with a compatible driver.
- CUDA toolkit that matches the chosen DeepStream release.
- TensorRT and GStreamer packages from the same vendor stack.
- `deepstream-app` on PATH or an equivalent DeepStream install tree.
- `CUDA_VER` exported before building `nvdsinfer_custom_impl_Yolo`.

### `CUDA_VER` mapping from the repo docs

| DeepStream release | x86 `CUDA_VER` | Jetson `CUDA_VER` |
| --- | --- | --- |
| 8.0 | 12.8 | 13.0 |
| 7.1 | 12.6 | 12.6 |
| 7.0 / 6.4 | 12.2 | 12.2 |
| 6.3 | 12.1 | 11.4 |
| 6.2 | 11.8 | 11.4 |
| 6.1.1 | 11.7 | 11.4 |
| 6.1 | 11.6 | 11.4 |
| 6.0.1 / 6.0 | 11.4 | 10.2 |
| 5.1 | 11.1 | 10.2 |

## Python inspection environment

The temporary inspection environment used to draft this skill contains:

- Python 3.11
- `torch`
- `ultralytics`
- `onnx`
- `onnxslim`
- `onnxruntime`

That environment is used only to inspect and smoke-test the Ultralytics-family exporter scripts.

## Recommended local checks

- `scripts/check-deepstream-toolchain.sh` — probes build/runtime readiness.
- `scripts/build-nvdsinfer-plugin.sh` — wraps the custom library build.
- `scripts/make-calibration-list.sh` — prepares INT8 calibration image lists.

## Notes

- The repo's DeepStream runtime instructions are hardware- and release-specific.
- Do not expect `deepstream-app` validation to pass on a host that lacks the DeepStream SDK.
- The model-conversion helpers are CPU-friendly, but the runtime deployment workflows remain NVIDIA-accelerator specific.
