---
name: onnx-quantization
description: "Use AIMET ONNX for QuantizationSimModel calibration, provider
  selection, encodings, QDQ export, graph passes, and ONNX PTQ utilities."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# AIMET ONNX quantization

Use this sub-skill for `aimet_onnx`, ONNX `QuantizationSimModel`, ONNX Runtime providers, input dictionaries, encodings import/export, QDQ conversion, tensor precision controls, graph passes, AdaRound, SeqMSE, and ONNX-side analysis utilities.

## Read/run first

- Read [API overview](../../references/api-overview.md) for verified `aimet_onnx` signatures and utility entry points.
- Read [workflows](../../references/workflows.md) for the distilled ONNX QuantSim/PTQ loop.
- Read [backend compatibility](../../references/backend-compatibility.md) for CPU provider versus CUDAExecutionProvider evidence.
- Read [troubleshooting](../../references/troubleshooting.md) for input-shape, provider, graph-pass, encoding-load, and QDQ/export issues.
- Run [quick_smoke.py](../../scripts/quick_smoke.py) with `--framework onnx` to prove the installed package can quantize a tiny ONNX model.

## Core workflow

1. **Validate the ONNX graph.** Start from a valid `onnx.ModelProto`; simplify or clean the graph before QuantSim if the export is noisy.
2. **Choose precision.** Use `param_type` and `activation_type` (`int8`, `int16`, `float16`, or `QSpec`/granularity objects) based on target accuracy/performance constraints.
3. **Choose providers deliberately.** Default CPU provider is sufficient for most graph work; CUDA provider requires `onnxruntime-gpu` and a visible CUDA runtime.
4. **Create QuantSim.** Pass the model, quant scheme, config file, dummy input if needed, custom op libraries if needed, and provider list.
5. **Calibrate with dictionaries.** Calibration batches should be `{input_name: np_array}` mappings with valid shapes and dtypes.
6. **Apply PTQ utilities when needed.** Run SeqMSE, AdaRound, blockwise/LPBQ, or tensor-precision overrides before final calibration/export when the task calls for them.
7. **Export.** Use `sim.export(...)` for AIMET model + encodings, or `sim.to_onnx_qdq(...)` / `from_onnx_qdq(...)` when the downstream workflow needs QDQ graphs.

## Decision points

- **Plain encodings vs QDQ:** Choose the artifact form required by the target toolchain; QDQ nodes are not the same as a separate encodings JSON.
- **Strict encoding loads:** Use strict behavior for deployment readiness; only use non-strict loading when explicitly inspecting graph differences.
- **Dynamic shapes:** Build calibration inputs that satisfy the symbolic shape constraints observed by ONNX Runtime.
- **Custom ops:** Provide `user_onnx_libs` only when the model actually contains custom ops and the library is available.

## Boundaries

- Route PyTorch model-preparation, QAT, and Torch export questions to [torch-quantization](../torch-quantization/SKILL.md).
- Route accuracy-debugging, visualization, compression, and target handoff to [optimization-analysis-deployment](../optimization-analysis-deployment/SKILL.md).
- LLM topology/configurator and GenAILab automation are deferred unless a future skill extension adds that scope.

## Expected answer shape

When answering an ONNX AIMET request, include:

- ONNX graph validation/simplification assumptions;
- `QuantizationSimModel` constructor arguments and provider list;
- calibration input dictionary shape;
- whether PTQ utilities are applied before final calibration;
- export form and expected artifacts;
- provider/backend verification required before claiming CUDA behavior.
