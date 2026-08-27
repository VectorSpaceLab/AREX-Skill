# Cross-cutting Troubleshooting

Read this before diving into a sub-skill when the failure surface is unclear.

## Fast triage

| Symptom or task | Likely owner | First action |
| --- | --- | --- |
| `onnxsim` cannot import, compiled extension missing, `onnxsim --help` fails | `sub-skills/bindings-and-packaging` | Run `python scripts/check_onnxsim_env.py --json`; if import fails, follow build/install troubleshooting. |
| Simplification runs but output check fails | `sub-skills/python-simplification` | Use `--graph-diff`, deterministic `--input-fill`, explicit `--test-input-shape`, and optimizer isolation. |
| Provider error mentions unavailable `CUDAExecutionProvider` or other EP | `sub-skills/python-simplification` first, then packaging if installation is needed | Validate providers with `python scripts/check_onnxsim_env.py --providers ... --json`; install the correct `onnxruntime` provider build or use CPU. |
| Custom op validation says `No Op registered for ...` | `sub-skills/python-simplification` or `advanced-graph-control` | Register the op schema in Python ONNX and leave automatic schema import enabled. |
| Need `custom_rewriter`, `FunctionProto` rules, metrics, graph diff, or profiling | `sub-skills/advanced-graph-control` | Use bundled rewrite/metrics smoke scripts before applying to user models. |
| CMake, submodule, nanobind, protobuf, C API, Rust, WASM, npm, or release version issues | `sub-skills/bindings-and-packaging` | Preserve the Python-wheel built-in-ORT caveat and choose the smallest build path. |

## Environment checker

From the generated skill root:

```bash
python scripts/check_onnxsim_env.py --help
python scripts/check_onnxsim_env.py --smoke --json
python scripts/check_onnxsim_env.py --providers CPUExecutionProvider --json
```

The checker reports package imports, compiled extension loading, optional ONNX Runtime providers, CLI optimizer listing, and a tiny API smoke. It does not need a source checkout.

## Optional dependency boundaries

- `onnxruntime` is optional for the Python package. Without it, CPU execution can fall back to ONNX's reference evaluator; non-CPU providers require ONNX Runtime and the matching provider build.
- CUDA constant folding through the Python API requires `onnxruntime-gpu` and an available `CUDAExecutionProvider`. The package should raise a provider availability `ValueError` rather than silently falling back to CPU when a non-CPU provider was requested.
- `sympy` is optional and affects symbolic metric formulas, not simplification correctness.
- `onnxscript` is optional authoring support for richer rewrite-rule examples. Pure-data `FunctionProto` rules can be authored with ONNX text and `onnx.parser.parse_function`.
- TVM, Halide, Qualcomm QNN, NVIDIA ModelOpt, torch/torchvision/timm/ultralytics/RF-DETR/VOICEVOX/X2Paddle, Rust, Node, Emscripten, browser, WebNN/WebGPU, and deployment credentials are optional integration/regression stacks, not minimum package requirements.

## Build-path warning

For Python wheel/editable builds, `setup.py` passes `-DONNXSIM_BUILTIN_ORT=OFF`; the Python extension does **not** compile vendored ONNX Runtime C++. Long ONNX Runtime C++ compilation means the user is on a standalone CMake, C API, Rust native-library, or default WASM path. Route those issues to `sub-skills/bindings-and-packaging`.

## When to stop and ask

Ask for a narrower target or explicit permission before:

- installing heavyweight optional provider stacks (`onnxruntime-gpu`, QNN, TVM, Halide, torch model-export packages);
- running long source builds, WASM builds, Rust native builds, or model-regression downloads;
- changing provider hardware/driver/toolkit assumptions;
- accepting `check=False` as good enough for a model the user wants to deploy;
- running mutating release scripts that bump versions or publish packages.
