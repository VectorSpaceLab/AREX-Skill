# Compiler Selection

## Purpose

Read this when the user wants to understand `auto_installer` decisions or the supported framework/backend combinations.

## Selector behavior

- `select_frameworks_to_install(include_frameworks, include_backends)` accepts either `"all"` or a list of framework names.
- Supported base frameworks are `torch`, `tensorflow`, `huggingface`, `diffusers`, and `onnx`.
- Extra backends are filtered against the selected base frameworks.
- `select_compilers_to_install(include_compilers, framework_list)` accepts either `"all"` or a list of compiler names.
- The selectors deduplicate and sort their outputs.

## Framework/backend map

| Framework | Extra backends |
| --- | --- |
| `torch` | `onnx` |
| `tensorflow` | `onnx` |
| `huggingface` | `torch`, `tensorflow`, `onnx` |
| `diffusers` | `torch`, `onnx` |
| `onnx` | none |

## Compiler families

The source maps compiler and backend module families such as ONNX Runtime, TorchScript, OpenVINO, DeepSparse, TVM, Torch Dynamo, Torch XLA, Torch Neuron, TensorRT, BladeDISC, Intel Neural Compressor, TFLite, and FasterTransformer.

## Safe use

Treat this as selection logic, not a generic installer recipe. If the machine cannot satisfy a selected backend, narrow the requested framework/backends rather than forcing a broad install.
