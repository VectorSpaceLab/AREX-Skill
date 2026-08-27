# Optional ONNX and TensorRT Paths

This repo keeps ONNX/TensorRT support as an optional, reference-only path. The supported baseline for future agents is still the standard PyTorch `test.py` synthesis flow that produces HTML results.

## What the optional flags mean

| Flag | What it does | Required stack | Caveat |
| --- | --- | --- | --- |
| `--export_onnx <file.onnx>` | Exports the loaded model to ONNX and exits | PyTorch ONNX export support plus a valid checkpoint | Export-only; it does not produce HTML synthesis output |
| `--engine <engine.plan>` | Runs a serialized TensorRT engine | TensorRT and `pycuda` | Vendor-specific path; not parity-verified with the standard CUDA path |
| `--onnx <model.onnx>` | Parses an ONNX model through TensorRT | TensorRT, `pycuda`, and the ONNX parser stack | Vendor-specific path; not parity-verified with the standard CUDA path |

## Why the helper is reference-only

`run_engine.py` is a legacy example helper and shows several fragilities that future agents should not ignore:

- it imports `tensorrt` and `pycuda` at module import time, so the whole path fails if the vendor stack is absent;
- `time_inference` measures execution but does not return a generated tensor;
- `test.py` expects a generated tensor so it can save HTML output, which means the current helper is not a drop-in parity path;
- `run_onnx` references undefined names such as `max_batch_size`, `max_workspace_size`, and `engine`;
- the code is written against older TensorRT APIs and should be treated as legacy background, not as a verified public runtime.

## Safe recovery guidance

If the vendor stack is unavailable or the helper fails:

1. fall back to the normal PyTorch inference path in `test.py`;
2. keep the standard HTML result contract as the supported output;
3. record the accelerator failure as an optional-path limitation rather than as a failure of standard inference;
4. if accelerated execution is truly needed, repair or replace the helper in a separate vendor-specific task.

## Practical rule

Do not claim that `--engine` or `--onnx` is equivalent to the normal CUDA synthesis path unless the vendor environment has been explicitly verified and the helper has been repaired or re-validated.
