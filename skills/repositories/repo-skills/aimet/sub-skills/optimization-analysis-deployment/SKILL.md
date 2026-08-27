---
name: optimization-analysis-deployment
description: "Use AIMET analysis, mixed precision, compression, debugging,
  export validation, and deployment artifact workflows after core quantization
  setup."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# AIMET optimization, analysis, and deployment

Use this sub-skill when the user asks why accuracy dropped after quantization, how to use QuantAnalyzer or visualization outputs, how to choose mixed precision, how to use compression, or how to validate/export artifacts for target inference.

## Read/run first

- Read [API overview](../../references/api-overview.md) for compression, ONNX analysis, SeqMSE, AdaRound, and related signatures.
- Read [workflows](../../references/workflows.md) for the accuracy-debugging, compression, GenAILab, and deployment loops.
- Read [backend compatibility](../../references/backend-compatibility.md) to separate CPU-valid analysis from CUDA/provider, GenAILab, cluster, or target-runtime requirements.
- Read [troubleshooting](../../references/troubleshooting.md) for accuracy, visualization, compression, GenAILab, credential, cluster, and export-artifact symptoms.
- Run [inspect_export.py](../../scripts/inspect_export.py) on an export directory before handing artifacts to target tooling.
- Route Qualcomm AI Hub, QAIRT, QNN, HTP, DLC, and SDK-command tasks to [qualcomm-sdk-deployment](../qualcomm-sdk-deployment/SKILL.md).

## Core workflow

1. **Establish baselines.** Compare FP32, high-bit-width, and target-bit-width QuantSim behavior before choosing remedies.
2. **Separate weight and activation sensitivity.** Raise one side's bit-width while holding the other side at target precision.
3. **Apply the right PTQ remedy.** Use BatchNorm folding/Cross-Layer Equalization/per-channel quantization/AdaRound/SeqMSE for weight issues; use range-setting, higher activation precision, or mixed precision for activation issues.
4. **Analyze sensitive layers.** Use QuantAnalyzer, per-layer sensitivity, histograms, and layer-output comparisons to identify the quantizer or op causing the drop.
5. **Use mixed precision deliberately.** Lite/manual/automatic mixed precision should be driven by measured sensitivity and target latency/accuracy constraints.
6. **Compress when the target requires lower MACs or memory.** Select compression ratios, apply Weight SVD/Spatial SVD/Channel Pruning, evaluate, then fine-tune if required.
7. **Validate export artifacts.** Confirm the ONNX model and AIMET encodings match before QNN/QAIRT/AI Hub or other target handoff.

## Deployment boundaries

AIMET produces simulation/export artifacts. It does not prove target-device correctness by itself. For Qualcomm AI Runtime, QNN, QAIRT, HTP, DLC, or AI Hub tasks, first validate the AIMET export pair and then use [qualcomm-sdk-deployment](../qualcomm-sdk-deployment/SKILL.md) for the local SDK or AI Hub workflow.

## Data and runtime boundaries

- Compression and accuracy examples often assume ImageNet-style evaluators; replace them with a tiny evaluator while developing.
- Visualization needs compatible Bokeh/HoloViews/HVPlot dependencies.
- LLM/VLM GenAILab recipe benchmarks are now covered by [genai-lab](../genai-lab/SKILL.md), but they still require explicit model/dataset/credential/budget approval before execution.
- On-target execution requires external SDKs/devices or AI Hub credentials; local export validation is not target proof.

## Expected answer shape

When answering optimization/deployment tasks, include:

- the baseline comparison being made;
- which quantizers/layers are being isolated;
- the selected AIMET remedy and why it matches weight/activation sensitivity;
- the evaluator/calibration data requirements;
- compression or mixed-precision constraints;
- exported artifacts and validation steps;
- explicit backend or target-runtime assumptions.
