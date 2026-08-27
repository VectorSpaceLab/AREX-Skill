---
name: torch-quantization
description: "Use AIMET Torch for model preparation, QuantizationSimModel
  calibration, PTQ/QAT, encodings, and Torch export workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# AIMET Torch quantization

Use this sub-skill for `aimet_torch`, PyTorch `QuantizationSimModel`, model preparation, BatchNorm folding, calibration callbacks, QAT, Torch PTQ utilities, quantizer inspection, and exporting Torch QuantSim results.

## Read/run first

- Read [API overview](../../references/api-overview.md) for verified `aimet_torch` signatures and related model-preparer/compression APIs.
- Read [workflows](../../references/workflows.md) for the distilled PyTorch QuantSim/PTQ/QAT loop.
- Read [backend compatibility](../../references/backend-compatibility.md) before deciding whether CPU or CUDA is evidence-bearing.
- Read [troubleshooting](../../references/troubleshooting.md) for functional-op, reused-module, encoding, QAT, and Torch/CUDA failures.
- Run [quick_smoke.py](../../scripts/quick_smoke.py) with `--framework torch` to prove the installed package can quantize a tiny model.

## Core workflow

1. **Stabilize the PyTorch model.** Use `eval()` for PTQ and a representative `dummy_input` on the same device as the model.
2. **Prepare the graph when needed.** If `forward` uses `torch.nn.functional` ops, reused modules, or FX-trace-sensitive code, run `aimet_torch.model_preparer.prepare_model` and compare outputs.
3. **Fold BatchNorm when deployment expects it.** Use `aimet_torch.batch_norm_fold.fold_all_batch_norms` before QuantSim when appropriate.
4. **Create QuantSim.** Configure `default_output_bw`, `default_param_bw`, `quant_scheme`, optional `config_file`, `in_place`, and `default_data_type`.
5. **Compute encodings.** The callback should run representative data through the QuantSim model without labels or optimizer updates.
6. **Evaluate and iterate.** Compare FP32, high-bit-width, and target-bit-width accuracy before adding QAT or advanced PTQ.
7. **Export.** Use the AIMET export path that creates a model plus encodings; keep artifacts together for downstream deployment.

## Decision points

- **PTQ vs QAT:** Use PTQ first. Move to QAT only when the user can run training and tune hyperparameters.
- **CPU vs CUDA:** CPU is enough for API behavior and small models. CUDA is evidence-bearing only for user model scale, CUDA-marked tests, or device-specific bugs.
- **Config files:** Use per-channel or custom quantization config when the task requires different default quantizer behavior; do not silently mix config and encoding files from unrelated graphs.
- **Torch to ONNX:** If the downstream toolchain is ONNX/QDQ based, route export details through the ONNX and deployment references after Torch calibration.

## Boundaries

- Route pure ONNX graph/provider/encoding tasks to [onnx-quantization](../onnx-quantization/SKILL.md).
- Route compression, QuantAnalyzer, mixed precision, and target handoff to [optimization-analysis-deployment](../optimization-analysis-deployment/SKILL.md).
- GenAILab LLM recipes and Hugging Face model download workflows are intentionally outside this first-pass sub-skill.

## Expected answer shape

When answering a Torch AIMET request, include:

- the exact `aimet_torch` imports;
- model preparation/folding assumptions;
- a calibration callback shape;
- QuantSim constructor arguments;
- the validation signal to compare FP32 and quantized behavior;
- export artifact expectations;
- any backend or dataset requirement that must be verified before running.
